from pathlib import Path

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from .models import Mudanca

MODEL_TESTS = "deepseek/deepseek-v4-flash"
MODEL_CODER = "deepseek/deepseek-v4-flash"
MODEL_CUA = "google/gemini-2.5-flash"
MAX_TOKENS = 100000

# Sem este extra_body o OpenRouter não devolve custo e metrics.cost fica None.
USAGE_ACCOUNTING = {"usage": {"include": True}}

PROMPTS = Path(__file__).resolve().parent / "prompts"


def load(nome: str) -> str:
    """Lê prompts/<nome>.md."""
    return (PROMPTS / f"{nome}.md").read_text(encoding="utf-8")


def _agente(model_id: str, instrucoes: str) -> Agent:
    return Agent(
        model=OpenRouter(
            id=model_id, max_tokens=MAX_TOKENS, extra_body=USAGE_ACCOUNTING
        ),
        instructions=instrucoes + "\n\n" + load("diretiva_codigo_minimo"),
        output_schema=Mudanca,
        use_json_mode=True,
    )


def make_test_writer() -> Agent:
    return _agente(MODEL_TESTS, load("test_writer"))


def make_coder() -> Agent:
    return _agente(MODEL_CODER, load("coder"))
