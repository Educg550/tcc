import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openrouter import OpenRouter
from agno.metrics import MessageMetrics
from agno.run.base import RunStatus
from agno.skills import LocalSkills, Skills

from .arquivos import Arquivos
from .dominio import Mudanca, Projeto
from .politicas import Orcamento
from .tracing import Trace

MAX_TOKENS = 100000
AMOSTRAGEM = {"temperature": 0.1, "top_p": 0.9}

# Sem este extra_body o OpenRouter não devolve custo e metrics.cost fica None. O teto de
# raciocínio deixa espaço para a resposta: no piloto v2 o GLM 5.3 gastou os 100k só pensando.
USAGE_ACCOUNTING = {"usage": {"include": True}, "reasoning": {"max_tokens": 32000}}

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def load(nome: str) -> str:
    """Lê prompts/<nome>.md. Todo texto de prompt vive em Markdown, não em string."""
    return (PROMPTS / f"{nome}.md").read_text(encoding="utf-8")


@dataclass
class ModeloComOrcamento(OpenRouter):
    """Confere o teto entre chamadas, inclusive dentro do ciclo de ferramentas."""

    orcamento: Orcamento | None = None
    inicio: float = 0
    chamadas: int = 0
    metricas: list[MessageMetrics] = field(default_factory=list)
    limite: str | None = None
    trace: Trace | None = None

    async def ainvoke(self, *args, **kwargs):
        mensagens = kwargs.get("messages", args[0] if args else [])
        pedido = {"messages": self._format_all_messages(mensagens), "tools": kwargs.get("tools")}
        tamanho = len(json.dumps(pedido, ensure_ascii=False).encode("utf-8"))
        precos = (self.extra_body or {}).get("provider", {}).get("max_price")
        # Limite conservador por bytes, com folga para a formatação interna do provedor.
        reserva = ((tamanho + 512 * len(mensagens) + 2048) * precos["prompt"]
                   + self.max_tokens * precos["completion"]) / 1_000_000 if precos else 0
        custo = sum(m.cost or 0 for m in self.metricas)
        if self.orcamento:
            # Passos são propostas ao gate; chamadas de ferramentas não são retries.
            self.limite = self.orcamento.estourou(0, custo + reserva, self.inicio)
            if self.limite:
                if self.trace:
                    self.trace.registrar({"evento": "limite", "motivo": self.limite,
                                          "cost_usd": custo, "reserva_usd": reserva})
                raise RuntimeError(f"Orçamento esgotado: {self.limite}")
        self.chamadas += 1
        inicio = time.time()
        evento = {"chamada": self.chamadas, "model": self.id,
                  "session_id": getattr(kwargs.get("run_response"), "session_id", None),
                  "request_bytes": tamanho, "mensagens": len(mensagens),
                  "max_output_tokens": self.max_tokens, "reserva_usd": reserva}
        if self.trace:
            self.trace.registrar({**evento, "evento": "inicio", "timestamp": inicio})
        try:
            resposta = await super().ainvoke(*args, **kwargs)
        except Exception as erro:
            if self.trace:
                self.trace.registrar({**evento, "evento": "erro", "erro": str(erro),
                                      "duration_s": round(time.time() - inicio, 3)})
            raise
        if resposta.response_usage:
            self.metricas.append(resposta.response_usage)
        if self.trace:
            self.trace.registrar({
                **evento, "evento": "fim", "duration_s": round(time.time() - inicio, 3),
                "metricas": resposta.response_usage.to_dict() if resposta.response_usage else None,
                "provider": (resposta.provider_data or {}).get("model_extra", {}).get("provider"),
                "response_id": (resposta.provider_data or {}).get("id"),
                "ferramentas": [t["function"]["name"] for t in resposta.tool_calls],
            })
        if precos and (resposta.response_usage is None or resposta.response_usage.cost is None):
            raise RuntimeError("Provedor não informou custo; sessão interrompida para preservar o teto.")
        return resposta


@dataclass(frozen=True)
class Resposta:
    """Arquivos editados pelas ferramentas e consumo das chamadas desta sessão."""

    mudanca: Mudanca | None
    custo_usd: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    erro: str | None = None
    chamadas: int = 1
    limite: str | None = None
    contexto_max_tokens: int = 0


class SoLeitura(Skills):
    """O modelo sugere e não executa: scripts de skill só podem ser lidos."""

    def _get_skill_script(self, skill_name, script_path, execute=False, args=None, timeout=30):
        return super()._get_skill_script(skill_name, script_path, False)


class Agente:
    """Sessão Agno com leitura e edição incremental, sem comandos de terminal."""

    def __init__(self, model_id: str, instrucoes: str, skills: list[Path] = ()):
        self.model_id = model_id
        self._agno = Agent(
            model=ModeloComOrcamento(
                id=model_id, max_tokens=MAX_TOKENS, extra_body=USAGE_ACCOUNTING,
                request_params={"parallel_tool_calls": False}, **AMOSTRAGEM
            ),
            skills=SoLeitura([LocalSkills(str(s), validate=False) for s in skills]) if skills else None,
            # A diretiva de código mínimo é constante do experimento: idêntica nos dois grupos.
            instructions="\n\n".join([instrucoes, load("estilo_codigo"), load("arquivos")]),
            db=InMemoryDb(),
            cache_session=True,
            add_history_to_context=True,
        )

    def preparar(self, projeto: Projeto, escopo, orcamento: Orcamento, inicio: float):
        self.arquivos = Arquivos(projeto, escopo)
        self._agno.set_tools([
            self.arquivos.listar_arquivos, self.arquivos.ler_arquivo,
            self.arquivos.criar_arquivo, self.arquivos.substituir_trecho,
        ])
        self._agno.model.orcamento = orcamento
        self._agno.model.inicio = inicio
        self._agno.model.trace = Trace(projeto.saida / "chamadas_modelo.jsonl")

    @classmethod
    def de(cls, papel: str, model_id: str, skills: list[Path] = ()) -> "Agente":
        """O papel nomeia o prompt; o modelo vem do caso de uso, não do harness."""
        return cls(model_id, load(papel), skills)

    async def propor(self, prompt: str) -> Resposta:
        self.arquivos.pendentes.clear()
        modelo = self._agno.model
        antes, chamadas = len(modelo.metricas), modelo.chamadas
        async with self._agno.model.get_async_client():
            resposta = await self._agno.arun(prompt)
        metricas = modelo.metricas[antes:]
        mudanca = self.arquivos.mudanca()
        erro = str(resposta.content)[:2000] if resposta.status == RunStatus.error else None
        if not mudanca.arquivos:
            mudanca = None
            erro = erro or "Nenhum arquivo foi editado. Use as ferramentas de arquivos."
        return Resposta(
            mudanca=mudanca,
            erro=erro,
            chamadas=modelo.chamadas - chamadas,
            limite=modelo.limite,
            contexto_max_tokens=max((m.input_tokens or 0 for m in metricas), default=0),
            custo_usd=sum(m.cost or 0 for m in metricas),
            input_tokens=sum(m.input_tokens or 0 for m in metricas),
            output_tokens=sum(m.output_tokens or 0 for m in metricas),
            total_tokens=sum(m.total_tokens or 0 for m in metricas),
        )
