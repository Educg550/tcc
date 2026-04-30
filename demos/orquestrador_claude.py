"""
Orquestrador mínimo — Pipeline TDD com Agent SDK

Demonstra o conceito central do TCC: um orquestrador que coordena
subagentes especializados no fluxo Requisito → Testes → Código.

Requisito de exemplo: função Python que valida CPF.

Uso:
    uv run orquestrador_claude.py
"""

import asyncio
import time
from datetime import datetime
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
WORKDIR = "demos/output/demo-cpf-1"

# ── Requisito de entrada ─────────────────────────────────────────
REQUISITO = """
Criar uma função `validar_cpf(cpf: str) -> bool` em Python que:
- Aceita CPF no formato "XXX.XXX.XXX-YY" (com pontuação obrigatória)
- Retorna True se o CPF for válido (11 dígitos + dígitos verificadores corretos)
- Retorna False para CPFs inválidos, com todos os dígitos iguais, ou com formato incorreto
"""

# ── Regras matemáticas de validação de CPF ──────────────────────
REGRAS_CPF = """
## Regras de Validação de CPF

A entrada é uma string no formato "XXX.XXX.XXX-YY", onde YY são os dois dígitos verificadores.

### Regras Estruturais
- O CPF deve conter exatamente 11 dígitos numéricos (ignorando pontuação).
- CPFs com todos os dígitos iguais são automaticamente inválidos
  (ex: "111.111.111-11", "000.000.000-00").

### Cálculo dos Dígitos Verificadores (módulo 11)

**1º Dígito Verificador (10º dígito do CPF):**
1. Tome os 9 primeiros dígitos (d1..d9).
2. Multiplique: d1×10 + d2×9 + d3×8 + d4×7 + d5×6 + d6×5 + d7×4 + d8×3 + d9×2.
3. Calcule soma % 11.
4. Se o resto for 0 ou 1 → 1º verificador = 0.
   Caso contrário → 1º verificador = 11 − resto.

**2º Dígito Verificador (11º dígito do CPF):**
1. Tome os 9 primeiros dígitos + o 1º verificador calculado (d1..d9, v1).
2. Multiplique: d1×11 + d2×10 + d3×9 + d4×8 + d5×7 + d6×6 + d7×5 + d8×4 + d9×3 + v1×2.
3. Calcule soma % 11.
4. Se o resto for 0 ou 1 → 2º verificador = 0.
   Caso contrário → 2º verificador = 11 − resto.

O CPF é válido somente se ambos os verificadores calculados coincidirem com os da entrada.

### Exemplos de CPFs válidos conhecidos
- "529.982.247-25" → válido
- "111.444.777-35" → válido

### Exemplos de CPFs inválidos
- "111.111.111-11" → inválido (todos dígitos iguais)
- "123.456.789-00" → inválido (verificadores errados)
- "000.000.000-00" → inválido (todos dígitos iguais)
"""

# ── Subagentes ───────────────────────────────────────────────────
agents = {
    "test-writer": AgentDefinition(
        description=(
            "Especialista em TDD. Recebe um requisito funcional e gera "
            "testes unitários com pytest ANTES de qualquer implementação."
        ),
        prompt=f"""Você é um especialista em Test-Driven Development.

Dado o requisito abaixo, escreva APENAS os testes (pytest) no arquivo tests/test_cpf.py.
NÃO implemente a função — apenas os testes.

Inclua casos para:
- CPFs válidos conhecidos (no formato "XXX.XXX.XXX-YY")
- CPFs com todos os dígitos iguais (ex: "111.111.111-11") → inválido
- CPFs com número errado de dígitos → inválido
- CPFs com dígitos verificadores incorretos → inválido

Importe a função assim: `from cpf import validar_cpf`

{REGRAS_CPF}
""",
        tools=["Write", "Bash", "Read"],
        model="haiku",
    ),
    "coder": AgentDefinition(
        description=(
            "Desenvolvedor Python. Recebe testes já escritos e implementa "
            "o código de produção que os faz passar."
        ),
        prompt=f"""Você é um desenvolvedor Python.

Leia os testes em tests/test_cpf.py e implemente a função `validar_cpf`
no arquivo cpf.py que faça TODOS os testes passarem.

A função deve seguir rigorosamente as regras matemáticas abaixo:

{REGRAS_CPF}

Depois de escrever o código, execute `python -m pytest tests/ -v` para
verificar que todos os testes passam. Se algum falhar, corrija o código
e rode os testes novamente.
""",
        tools=["Read", "Write", "Bash"],
        model="haiku",
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


def fmt_elapsed(start: float) -> str:
    elapsed = time.time() - start
    return f"[{elapsed:7.2f}s]"


async def main():
    Path(WORKDIR).mkdir(parents=True, exist_ok=True)
    start = time.time()
    start_dt = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  Pipeline TDD — validar_cpf")
    print(f"  Hora de início        : {start_dt}")
    print(f"  Diretório de trabalho : {WORKDIR}")
    print(f"  Modelos               : haiku (orquestrador + subagentes)")
    print(f"{sep}\n")

    options = ClaudeAgentOptions(
        cwd=WORKDIR,
        allowed_tools=["Agent", "Bash", "Read", "Write"],
        permission_mode="acceptEdits",
        agents=agents,
        model="haiku",
    )

    async for message in query(prompt=PROMPT_ORQUESTRADOR, options=options):
        ts = fmt_elapsed(start)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    # Print each line with the timestamp prefix
                    for line in block.text.splitlines():
                        print(f"{ts} {line}")
                elif isinstance(block, ToolUseBlock):
                    input_summary = ""
                    if isinstance(block.input, dict):
                        if "agent_name" in block.input:
                            input_summary = f" → subagente: {block.input['agent_name']}"
                        elif "command" in block.input:
                            cmd = str(block.input["command"])[:60]
                            input_summary = f" $ {cmd}"
                        elif "file_path" in block.input:
                            input_summary = f" 📄 {block.input['file_path']}"
                    print(f"{ts} TOOL  {block.name}{input_summary}")
        elif isinstance(message, ResultMessage):
            total = time.time() - start
            end_dt = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            print(f"\n{'=' * 60}")
            print(f"  Pipeline concluído — {message.subtype}")
            print(f"  Hora de conclusão  : {end_dt}")
            print(f"  Tempo total        : {total:.2f}s")
            print(f"{'=' * 60}\n")


asyncio.run(main())
