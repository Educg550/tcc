from dataclasses import dataclass
from pathlib import Path

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.skills import LocalSkills, Skills
from pydantic import ValidationError

from .dominio import Mudanca

MAX_TOKENS = 100000
AMOSTRAGEM = {"temperature": 0.1, "top_p": 0.9}

# Sem este extra_body o OpenRouter não devolve custo e metrics.cost fica None. O teto de
# raciocínio deixa espaço para a resposta: no piloto v2 o GLM 5.3 gastou os 100k só pensando.
USAGE_ACCOUNTING = {"usage": {"include": True}, "reasoning": {"max_tokens": 32000}}

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def load(nome: str) -> str:
    """Lê prompts/<nome>.md. Todo texto de prompt vive em Markdown, não em string."""
    return (PROMPTS / f"{nome}.md").read_text(encoding="utf-8")


def _sem_cerca(texto: str) -> str:
    """Mesmo em json_mode o modelo às vezes cerca a resposta em ```json."""
    t = texto.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1].rsplit("```", 1)[0]
    return t


@dataclass(frozen=True)
class Resposta:
    """O que o provedor devolveu: a mudança proposta e o que ela custou. Sem `mudanca`
    quando a resposta não virou JSON válido - o passo custou mesmo assim."""

    mudanca: Mudanca | None
    custo_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    erro: str | None = None


class SoLeitura(Skills):
    """O modelo sugere e não executa: scripts de skill só podem ser lidos."""

    def _get_skill_script(self, skill_name, script_path, execute=False, args=None, timeout=30):
        return super()._get_skill_script(skill_name, script_path, False)


class Agente:
    """Único ponto que traduz resposta de provedor em objeto de domínio. Papéis
    diferem por model_id e instruções, que são argumentos, não subclasses."""

    def __init__(self, model_id: str, instrucoes: str, skills: list[Path] = ()):
        self.model_id = model_id
        self._agno = Agent(
            model=OpenRouter(
                id=model_id, max_tokens=MAX_TOKENS, extra_body=USAGE_ACCOUNTING, **AMOSTRAGEM
            ),
            skills=SoLeitura([LocalSkills(str(s), validate=False) for s in skills]) if skills else None,
            # A diretiva de código mínimo é constante do experimento: idêntica nos dois grupos.
            instructions=instrucoes + "\n\n" + load("estilo_codigo"),
            output_schema=Mudanca.model_json_schema(),
            use_json_mode=True,
        )

    @classmethod
    def de(cls, papel: str, model_id: str, skills: list[Path] = ()) -> "Agente":
        """O papel nomeia o prompt; o modelo vem do caso de uso, não do harness."""
        return cls(model_id, load(papel), skills)

    async def propor(self, prompt: str) -> Resposta:
        async with self._agno.model.get_async_client():
            resposta = await self._agno.arun(prompt)
        m = getattr(resposta, "metrics", None)
        try:
            mudanca, erro = self._mudanca(resposta.content), None
        except (ValidationError, ValueError) as falha:
            mudanca, erro = None, str(falha)[:2000]
        return Resposta(
            mudanca=mudanca,
            erro=erro,
            custo_usd=getattr(m, "cost", None) or 0.0,
            input_tokens=getattr(m, "input_tokens", None) or 0,
            output_tokens=getattr(m, "output_tokens", None) or 0,
            total_tokens=getattr(m, "total_tokens", None) or 0,
        )

    @staticmethod
    def _mudanca(content) -> Mudanca:
        if content is None or content == "":
            raise ValueError("O provedor devolveu uma resposta vazia, sem arquivos.")
        if isinstance(content, Mudanca):
            return content
        if isinstance(content, str):
            return Mudanca.model_validate_json(_sem_cerca(content))
        return Mudanca.model_validate(content)
