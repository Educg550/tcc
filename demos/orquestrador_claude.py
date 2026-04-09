"""
Orquestrador mínimo — Pipeline TDD com Agent SDK

Demonstra o conceito central do TCC: um orquestrador que coordena
subagentes especializados no fluxo Requisito → Testes → Código.

Requisito de exemplo: função Python que valida CPF.

Uso:
    uv run orquestrador_claude.py
"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

# ── Diretório de trabalho do pipeline ────────────────────────────
WORKDIR = "/tmp/tcc-demo-cpf"

# ── Requisito de entrada ─────────────────────────────────────────
REQUISITO = """
Criar uma função `validar_cpf(cpf: str) -> bool` em Python que:
- Aceita CPF com ou sem pontuação (ex: "123.456.789-09" ou "12345678909")
- Retorna True se o CPF for válido (11 dígitos + dígitos verificadores corretos)
- Retorna False para CPFs inválidos, com todos os dígitos iguais, ou com formato incorreto
"""

# ── Subagentes ───────────────────────────────────────────────────
agents = {
    "test-writer": AgentDefinition(
        description=(
            "Especialista em TDD. Recebe um requisito funcional e gera "
            "testes unitários com pytest ANTES de qualquer implementação."
        ),
        prompt="""Você é um especialista em Test-Driven Development.

Dado o requisito abaixo, escreva APENAS os testes (pytest) no arquivo tests/test_cpf.py.
NÃO implemente a função — apenas os testes.

Inclua casos para:
- CPFs válidos conhecidos (com e sem pontuação)
- CPFs com todos os dígitos iguais (ex: "111.111.111-11") → inválido
- CPFs com número errado de dígitos → inválido
- CPFs com dígitos verificadores incorretos → inválido

Importe a função assim: `from cpf import validar_cpf`
""",
        tools=["Write", "Bash", "Read"],
        model="sonnet",
    ),
    "coder": AgentDefinition(
        description=(
            "Desenvolvedor Python. Recebe testes já escritos e implementa "
            "o código de produção que os faz passar."
        ),
        prompt="""Você é um desenvolvedor Python.

Leia os testes em tests/test_cpf.py e implemente a função `validar_cpf`
no arquivo cpf.py que faça TODOS os testes passarem.

Depois de escrever o código, execute `python -m pytest tests/ -v` para
verificar que todos os testes passam. Se algum falhar, corrija o código
e rode os testes novamente.
""",
        tools=["Read", "Write", "Bash"],
        model="sonnet",
    ),
}

# ── Prompt do orquestrador ───────────────────────────────────────
PROMPT_ORQUESTRADOR = f"""Você é um orquestrador de pipeline TDD.

Seu trabalho é coordenar dois subagentes para implementar o requisito abaixo,
seguindo rigorosamente a ordem:

1. Primeiro, chame o subagente "test-writer" passando o requisito.
   Ele vai criar os testes em tests/test_cpf.py.

2. Depois que os testes estiverem escritos, chame o subagente "coder".
   Ele vai ler os testes e implementar o código em cpf.py.

Não escreva código você mesmo. Apenas coordene os subagentes.

## Requisito

{REQUISITO}
"""


async def main():
    Path(WORKDIR).mkdir(parents=True, exist_ok=True)

    print(f"\nRequisito: validar_cpf(cpf: str) -> bool")
    print(f"Diretório de trabalho: {WORKDIR}\n")

    options = ClaudeAgentOptions(
        cwd=WORKDIR,
        allowed_tools=["Agent", "Bash", "Read", "Write"],
        permission_mode="acceptEdits",
        agents=agents,
        model="haiku",
    )

    async for message in query(prompt=PROMPT_ORQUESTRADOR, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"\n→ Chamando: {block.name}")
        elif isinstance(message, ResultMessage):
            print(f"\n{'=' * 60}")
            print(f"  Pipeline concluído — {message.subtype}")
            print(f"{'=' * 60}")


asyncio.run(main())
