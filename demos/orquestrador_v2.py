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

# ── Definições de agente ────────────────────────────────────────────────
AGENTS = {
    "test-writer": AgentDefinition(
        description=(
            "Especialista em TDD que gera acceptance tests pytest a partir "
            "de uma descrição NL do sistema, antes de qualquer implementação."
        ),
        prompt="""Você é um especialista em Test-Driven Development.

Dado o requisito abaixo, escreva APENAS testes pytest no arquivo
`tests/test_acceptance.py`. **NÃO** implemente nada em `src/`. **NÃO**
escreva `structure.yml`.

## Características obrigatórias dos testes

- São testes de **aceitação**, ou seja, invocam a CLI por fora: use
  `subprocess.run([sys.executable, "-m", "task", ...], ...)` OU importe
  `from task.main import main` e invoque simulando `sys.argv`. Escolha
  uma abordagem e mantenha consistente.
- Cada teste deve validar EFEITO observável: saída no stdout/stderr,
  código de retorno, e/ou estado de `tasks.json` no cwd do teste.
- Cubra os 6 comandos (add, list, done, edit, delete, show), prioridades
  (low/medium/high), datas de vencimento, e edge cases:
  - `tasks.json` inexistente (deve ser criado no primeiro uso)
  - ID inválido (não existente)
  - prioridade fora do enum
  - data malformada (YYYY-MM-DD inválido)
- Importe SOMENTE de `task` (`from task import ...` /
  `from task.main import main`). Assuma que o pacote existirá.
- Use `tmp_path` fixture do pytest para isolar `tasks.json` por teste.

## Restrições

- NÃO use libs externas. Só stdlib + pytest.
- NÃO crie outros arquivos. Apenas `tests/test_acceptance.py`.
""",
        tools=["Write", "Read", "Bash"],
        model=MODEL_DESIGN,
    ),
    "structure-writer": AgentDefinition(
        description=(
            "Gera estrutura YAML de pacotes/classes/métodos (formato Onion) "
            "a partir de acceptance tests pytest e do requisito original."
        ),
        prompt="""Você é um arquiteto de software.

Leia `tests/test_acceptance.py` e o requisito NL abaixo. Produza
`structure.yml` listando pacotes, classes e métodos necessários para
fazer esses testes passarem.

## Formato esperado (estilo Onion)

```yaml
!package
children:
- !main_module
  name: main
  description: "ponto de entrada da CLI"
- !class_module
  name: storage
  class_name: TaskStorage
  description: "..."
  methods:
  - !method
    name: __init__
    description: "..."
    parameters: [path]
    returns: []
  - !method
    name: load
    description: "..."
    parameters: []
    returns: ["lista de tarefas"]
```

## Regras

- Convenção Python (snake_case módulos, PascalCase classes).
- Deve haver um `!main_module` com `name: main` (ponto de entrada da CLI).
- NÃO escreva código de produção nem testes — somente o YAML.
- NÃO crie nada em `src/`.
""",
        tools=["Read", "Write"],
        model=MODEL_DESIGN,
    ),
    "coder": AgentDefinition(
        description=(
            "Implementa código Python a partir de structure.yml + testes "
            "pytest, executando os testes até passarem."
        ),
        prompt="""Você é um desenvolvedor Python.

Leia `structure.yml` e `tests/test_acceptance.py`. Implemente os módulos
em `src/task/` seguindo a estrutura.

## Bootstrap do pacote para pytest

Crie um `conftest.py` na raiz do workdir contendo:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
```

Isso permite `from task import ...` sem `pip install -e .`.

## Ciclo de validação

Depois de implementar o código, execute:

```bash
python -m pytest tests/ -v
```

Se algum teste falhar, corrija o CÓDIGO (jamais os testes) e rode os
testes novamente. Itere até todos passarem ou até estar inequivocamente
travado.

## Restrições

- Apenas stdlib (json, argparse, datetime, pathlib, sys).
- NÃO altere arquivos em `tests/`.
- NÃO altere `structure.yml`.
""",
        tools=["Read", "Write", "Bash"],
        model=MODEL_CODE,
    ),
}


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
            passed=0,
            failed=0,
            errors=0,
            total=0,
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


# ── Execução de uma etapa ───────────────────────────────────────────────
def _fmt_elapsed(start: float) -> str:
    return f"[{time.time() - start:7.2f}s]"


async def run_stage(
    stage_id: str,
    agent_name: str,
    configured_model: str,
    prompt_base: str,
    feedback: Optional[str] = None,
) -> StageMetrics:
    """
    Executa UMA tentativa de uma etapa via query() do agent SDK.

    Anexa o bloco FEEDBACK DA TENTATIVA ANTERIOR no prompt se feedback
    não-None. Apenas o último feedback é usado (não acumula histórico).

    Retorna um StageMetrics com retries=0; o caller (execute_with_approval)
    atualiza `retries` ao final do loop.
    """
    full_prompt = prompt_base
    if feedback is not None:
        full_prompt += (
            "\n\n## FEEDBACK DA TENTATIVA ANTERIOR\n"
            f"{feedback}\n"
        )

    options = ClaudeAgentOptions(
        cwd=str(WORKDIR),
        allowed_tools=["Agent", "Bash", "Read", "Write"],
        permission_mode="acceptEdits",
        agents=AGENTS,
        model=configured_model,
    )

    start = time.time()
    print(f"\n──── etapa [{stage_id}] via {agent_name} ({configured_model}) ────")
    last_result: Optional[ResultMessage] = None

    async for message in query(prompt=full_prompt, options=options):
        ts = _fmt_elapsed(start)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    for line in block.text.splitlines():
                        print(f"{ts} {line}")
                elif isinstance(block, ToolUseBlock):
                    summary = ""
                    if isinstance(block.input, dict):
                        if "agent_name" in block.input:
                            summary = f" → subagente: {block.input['agent_name']}"
                        elif "command" in block.input:
                            cmd = str(block.input["command"])[:80]
                            summary = f" $ {cmd}"
                        elif "file_path" in block.input:
                            summary = f" 📄 {block.input['file_path']}"
                    print(f"{ts} TOOL  {block.name}{summary}")
        elif isinstance(message, ResultMessage):
            last_result = message

    if last_result is None:
        raise RuntimeError(f"etapa {stage_id}: query() terminou sem ResultMessage")

    return StageMetrics(
        id=stage_id,
        agent=agent_name,
        configured_model=configured_model,
        duration_s=round(last_result.duration_ms / 1000, 2),
        duration_api_s=round(last_result.duration_api_ms / 1000, 2),
        num_turns=last_result.num_turns,
        retries=0,
        cost_usd=last_result.total_cost_usd,
        usage=last_result.usage,
        model_usage=last_result.model_usage,
    )


# ── Loop com aprovação humana ───────────────────────────────────────────
async def execute_with_approval(
    stage_id: str,
    agent_name: str,
    configured_model: str,
    prompt_base: str,
    artifact_path: Path,
) -> StageMetrics:
    """
    Executa uma etapa em loop até o usuário aprovar.

    - Em 'n', exige feedback textual e re-roda com bloco FEEDBACK.
    - Verifica que `artifact_path` foi escrito após cada tentativa.
    - Apenas a tentativa aprovada é retornada como StageMetrics (item 8.4
      do spec); retries reflete o número de tentativas rejeitadas antes.
    """
    feedback = None
    retries = 0
    while True:
        metrics = await run_stage(
            stage_id, agent_name, configured_model, prompt_base, feedback
        )

        if not artifact_path.exists():
            raise RuntimeError(
                f"Etapa {stage_id}: agente terminou mas {artifact_path} "
                f"não foi escrito. Abortando."
            )

        feedback = aprovar_artefato(stage_id, artifact_path)
        if feedback is None:
            metrics.retries = retries
            return metrics
        retries += 1
        print(f"  → rejeitado, retry #{retries} com feedback")


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
