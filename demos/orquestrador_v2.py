"""
Orquestrador v2 — pipeline TDD com 3 etapas e aprovação humana

Gera uma CLI de tarefas (CRUD) em Python a partir de um único prompt em
linguagem natural, em três etapas separadas com pausa humana entre cada:

    1. test-writer  (Sonnet) -> tests/test_acceptance.py
    2. structure-writer (Sonnet) -> structure.yml
    3. coder        (Haiku)  -> src/task/*.py + pytest passando

Uso (a partir de `demos/`):
    uv run orquestrador_v2.py

Ou da raiz do TCC:
    uv run --project demos demos/orquestrador_v2.py
"""

import asyncio
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

# ── Paths absolutos ───────────────────────────────────
WORKDIR = (SCRIPT_DIR / "output" / "task-cli-orquestrado").resolve()
ACCEPTANCE_TESTS = WORKDIR / "tests" / "test_acceptance.py"
STRUCTURE_FILE = WORKDIR / "structure.yml"
SRC_MAIN = WORKDIR / "src" / "task" / "main.py"
RUN_LOG = WORKDIR / "RUN.log"

# ── Modelos por etapa ────────────────────────────────────────────────────
MODEL_DESIGN = "sonnet"
MODEL_CODE = "haiku"

# ── Prompt inicial (entrada do pipeline) ────────────────────────────────
PROMPT_INICIAL = """\
Implemente uma CLI de tarefas em Python chamada `task` com persistência em
arquivo JSON e CRUD completo. Requisitos:

## Comandos

1. `task add "<título>" [-p low|medium|high] [-d YYYY-MM-DD]`
   - cria nova tarefa
   - `-p, --priority`: prioridade (default: low)
   - `-d, --due`: data de vencimento opcional, formato YYYY-MM-DD

2. `task list [-a | --done] [-p high|medium|low]`
   - sem flags: lista apenas tarefas pendentes
   - `-a, --all`: inclui concluídas
   - `--done`: apenas concluídas
   - `-p`: filtra por prioridade

3. `task done <id>` — marca como concluída

4. `task edit <id> [--title T] [-p P] [-d D]` — edita campos da tarefa <id>

5. `task delete <id> [--force]`
   - remove a tarefa; pede confirmação (`y/N`) ao usuário a menos que --force

6. `task show <id>` — mostra os detalhes de uma única tarefa pelo ID

## Persistência

- Arquivo `tasks.json` no diretório atual (NÃO em `~/`).
- Estrutura: `{"version": 1, "tasks": [...]}`.
- Cada tarefa tem `id` (int auto-incremental), `title` (str), `priority`
  (`"low"|"medium"|"high"`), `due_date` (`"YYYY-MM-DD"` ou null), `done`
  (bool), `created_at` (ISO 8601).
- Se `tasks.json` não existir, deve ser criado vazio no primeiro uso.

## Restrições técnicas

- Python 3.11+. Apenas stdlib (json, argparse, datetime, pathlib, sys).
- Empacotamento: módulo `task` em `src/task/`. Entrypoint principal em
  `src/task/main.py` exportando função `main()` chamável via
  `python -m task ...`.
- Erros tratados explicitamente: ID inexistente, prioridade fora do enum,
  data malformada (YYYY-MM-DD inválida), arquivo `tasks.json` ausente
  (deve ser criado, não falhar).
"""


# ── Dataclasses ─────────────────────────────────────────────────────────
@dataclass
class StageMetrics:
    """Métricas de UMA tentativa aprovada de uma etapa."""

    id: str
    agent: str
    configured_model: str
    duration_s: float
    duration_api_s: float
    num_turns: int
    retries: int = 0
    cost_usd: Optional[float] = None
    usage: Optional[dict] = None
    model_usage: Optional[dict] = None


@dataclass
class PytestFinal:
    passed: int
    failed: int
    errors: int
    total: int
    summary: str
    collection_error: Optional[str] = None


# ── Parsing do resumo do pytest ─────────────────────────────────────────
_PYTEST_FIELD_RE = re.compile(r"(\d+)\s+(passed|failed|errors?|error)")


def parse_pytest_summary(stdout: str) -> PytestFinal:
    """
    Extrai contagens da última linha de resumo do pytest.

    Reconhece linhas no estilo:
        '== 27 passed in 1.2s ==='
        '== 5 failed, 2 errors in 0.4s ==='
        '== 1 passed, 3 failed in 0.8s ==='

    Se nenhuma linha de resumo for encontrada, devolve um PytestFinal
    com totals zerados e `collection_error` populado com a última linha
    não-vazia do stdout, como pista do erro.
    """
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    summary_line = None
    for ln in reversed(lines):
        if "passed" in ln or "failed" in ln or "error" in ln:
            if "=" in ln or "in " in ln:
                summary_line = ln
                break

    if summary_line is None:
        last = lines[-1] if lines else ""
        return PytestFinal(
            passed=0, failed=0, errors=0, total=0,
            summary="collection error",
            collection_error=last,
        )

    counts = {"passed": 0, "failed": 0, "errors": 0}
    for n_str, kw in _PYTEST_FIELD_RE.findall(summary_line):
        if kw.startswith("error"):
            counts["errors"] += int(n_str)
        else:
            counts[kw] = int(n_str)

    total = counts["passed"] + counts["failed"] + counts["errors"]
    return PytestFinal(
        passed=counts["passed"],
        failed=counts["failed"],
        errors=counts["errors"],
        total=total,
        summary=f"{counts['passed']}/{total} passed",
    )


# ── Aprovação humana ────────────────────────────────────────────────────
def aprovar_artefato(label: str, artifact_path: Path) -> Optional[str]:
    """
    Pausa interativa entre etapas.

    Imprime o conteúdo do artefato (ou um `ls -R` se for diretório),
    pede aprovação y/n. Em caso de 'n' exige feedback textual não-vazio.
    Retorna None se aprovado; string de feedback se rejeitado.
    """
    banner = "═" * 60
    print(f"\n{banner}")
    print(f"  Etapa: {label}")
    print(f"  Artefato: {artifact_path}")
    print(banner)

    if artifact_path.is_dir():
        for item in sorted(artifact_path.rglob("*")):
            if item.is_file():
                rel = item.relative_to(artifact_path)
                print(f"  • {rel}")
    elif artifact_path.is_file():
        print(artifact_path.read_text())
    else:
        print("  (artefato não encontrado)")
    print(banner)

    while True:
        resp = input(f"[{label}] aprovar? (y/n): ").strip().lower()
        if resp == "y":
            return None
        if resp == "n":
            break
        print("  Resposta inválida. Digite 'y' ou 'n'.")

    feedback = ""
    while not feedback.strip():
        feedback = input("Feedback: ")
    return feedback.strip()


# ── Stub main ───────────────────────────────────────────────────────────
async def main() -> None:
    raise NotImplementedError("preenchido nas próximas tasks")


if __name__ == "__main__":
    asyncio.run(main())
