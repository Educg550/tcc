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


# ── Stub main ───────────────────────────────────────────────────────────
async def main() -> None:
    raise NotImplementedError("preenchido nas próximas tasks")


if __name__ == "__main__":
    asyncio.run(main())
