from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load(nome: str) -> str:
    """Lê prompts/<nome>.md. Levanta FileNotFoundError se não existir."""
    return (PROMPTS_DIR / f"{nome}.md").read_text(encoding="utf-8")
