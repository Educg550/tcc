from pathlib import Path

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.file import FileTools

from .models import Criterios
from .prompts import load

MODEL_SPEC = "deepseek/deepseek-v4-flash"
MODEL_CODER = "deepseek/deepseek-v4-flash"
MAX_TOKENS = 100000


def make_spec_writer() -> Agent:
    return Agent(
        model=OpenRouter(id=MODEL_SPEC, max_tokens=MAX_TOKENS),
        instructions=load("spec_writer"),
        output_schema=Criterios,
        use_json_mode=True,
    )


def make_coder(output_dir: Path) -> Agent:
    return Agent(
        model=OpenRouter(id=MODEL_CODER, max_tokens=MAX_TOKENS),
        instructions=load("coder"),
        tools=[FileTools(output_dir)],
    )
