import json
import os
import socket
import subprocess
import time
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from browser_use import Agent as AgenteNavegador
from browser_use import ChatOpenAI
from pydantic import BaseModel

from .dominio import Mudanca, Projeto, Requisito

MAX_TOKENS = 100000
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Sem este extra_body o OpenRouter não devolve custo e metrics.cost fica None.
USAGE_ACCOUNTING = {"usage": {"include": True}}

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def load(nome: str) -> str:
    """Lê prompts/<nome>.md. Todo texto de prompt vive em Markdown, não em string."""
    return (PROMPTS / f"{nome}.md").read_text(encoding="utf-8")


@dataclass(frozen=True)
class Proposta:
    mudanca: Mudanca
    custo_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


class Agente:
    """Único ponto que traduz resposta de provedor em objeto de domínio. Papéis
    diferem por model_id e instruções, que são argumentos, não subclasses."""

    def __init__(self, model_id: str, instrucoes: str):
        self.model_id = model_id
        self._agno = Agent(
            model=OpenRouter(
                id=model_id, max_tokens=MAX_TOKENS, extra_body=USAGE_ACCOUNTING
            ),
            # A diretiva de código mínimo é constante do experimento: idêntica nos dois grupos.
            instructions=instrucoes + "\n\n" + load("estilo_codigo"),
            output_schema=Mudanca,
            use_json_mode=True,
        )

    @classmethod
    def de(cls, papel: str, model_id: str) -> "Agente":
        """O papel nomeia o prompt; o modelo vem do caso de uso, não do harness."""
        return cls(model_id, load(papel))

    async def propor(self, prompt: str) -> Proposta:
        resposta = await self._agno.arun(prompt)
        m = getattr(resposta, "metrics", None)
        return Proposta(
            mudanca=self._mudanca(resposta.content),
            custo_usd=getattr(m, "cost", None) or 0.0,
            input_tokens=getattr(m, "input_tokens", None) or 0,
            output_tokens=getattr(m, "output_tokens", None) or 0,
            total_tokens=getattr(m, "total_tokens", None) or 0,
        )

    @staticmethod
    def _mudanca(content) -> Mudanca:
        if isinstance(content, Mudanca):
            return content
        if isinstance(content, str):
            return Mudanca.model_validate_json(content)
        return Mudanca.model_validate(content)


class VeredictoCriterio(BaseModel):
    id: str
    passou: bool
    evidencia: str


class VeredictoCUA(BaseModel):
    criterios: list[VeredictoCriterio]
    aprovado_geral: bool
    resumo: str


class Avaliador:
    """O CUA: avaliador final, caixa-preta sobre o app rodando. Mede divergência
    semântica que os testes gerados pelo próprio pipeline não pegam."""

    def __init__(self, model_id: str):
        self.model_id = model_id

    @staticmethod
    @contextmanager
    def app_rodando(projeto: Projeto):
        """Sobe o app com o comando que o caso de uso declara, numa porta livre."""
        with socket.socket() as s:
            s.bind(("", 0))
            porta = s.getsockname()[1]
        projeto.saida.mkdir(parents=True, exist_ok=True)
        # Em arquivo, não em pipe: o app loga cada requisição do CUA e um pipe cheio
        # travaria o processo no meio da avaliação.
        log = projeto.saida / "app.log"
        url = f"http://localhost:{porta}"
        with log.open("w", encoding="utf-8") as stderr:
            proc = subprocess.Popen(
                projeto.alvo.app(porta),
                cwd=str(projeto.raiz),
                stdout=subprocess.DEVNULL,
                stderr=stderr,
            )
            try:
                # A primeira subida pode pagar a resolução das dependências do caso de uso.
                for _ in range(300):
                    if proc.poll() is not None:
                        raise RuntimeError(f"app morreu ao subir: {log.read_text()}")
                    try:
                        urllib.request.urlopen(url, timeout=1)
                        break
                    except OSError:
                        time.sleep(0.2)
                else:
                    raise RuntimeError(f"app não respondeu em {url}: {log.read_text()}")
                yield url
            finally:
                proc.kill()
                proc.wait()

    async def avaliar(self, projeto: Projeto, requisito: Requisito) -> dict:
        with self.app_rodando(projeto) as url:
            agente = AgenteNavegador(
                task=load("cua_task").format(
                    base_url=url, criterios=requisito.criterios
                ),
                llm=ChatOpenAI(
                    model=self.model_id,
                    base_url=OPENROUTER_BASE,
                    api_key=os.environ["OPENROUTER_API_KEY"],
                ),
                output_model_schema=VeredictoCUA,
                generate_gif=False,
                calculate_cost=True,
            )
            history = await agente.run()

        v, usage = history.structured_output, history.usage
        resultado = {
            "configured_model": self.model_id,
            "duration_s": round(history.total_duration_seconds() or 0.0, 2),
            "num_steps": history.number_of_steps(),
            "cost_usd": usage.total_cost if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
            "aprovado_geral": v.aprovado_geral if v else False,
            "resumo": v.resumo if v else "",
            "criterios": [c.model_dump() for c in v.criterios] if v else [],
        }
        projeto.saida.mkdir(parents=True, exist_ok=True)
        (projeto.saida / "veredito.json").write_text(
            json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return resultado
