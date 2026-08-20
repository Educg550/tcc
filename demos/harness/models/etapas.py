import time

from .agentes import Agente
from .dominio import Escopo, EscopoViolado, Projeto, ResultadoPytest
from .observacoes import Observacao, PropostaRejeitada, PytestFalhou
from .politicas import Orcamento, Permissao
from .tracing import Trace


class Etapa:
    """Um laço: propor → validar → escrever → observar → autorizar, até o orçamento
    estourar ou nada mais haver a observar. O modelo nunca executa: quem escreve é
    o Projeto, quem decide é a Permissao."""

    def __init__(
        self,
        id: str,
        agente: Agente,
        escopo: Escopo,
        permissao: Permissao,
        orcamento: Orcamento,
        trace: Trace,
    ):
        self.id = id
        self.agente = agente
        self.escopo = escopo
        self.permissao = permissao
        self.orcamento = orcamento
        self.trace = trace

    def verificar(self, projeto: Projeto) -> ResultadoPytest | None:
        return None

    def _prompt(self, base: str, observacoes: list[Observacao]) -> str:
        return "\n\n".join([base, *(o.como_prompt() for o in observacoes)])

    async def executar(self, base: str, projeto: Projeto) -> dict:
        inicio, passos, custo = time.time(), 0, 0.0
        tokens_in, tokens_out, tokens = 0, 0, 0
        observacoes: list[Observacao] = []
        arquivos: list[str] = []
        historico: list[dict] = []

        def parte(ok: bool, motivo: str) -> dict:
            return {
                "id": self.id,
                "configured_model": self.agente.model_id,
                "duration_s": round(time.time() - inicio, 2),
                "ok": ok,
                "motivo": motivo,
                "passos": passos,
                # Derivado de passos, e mantido porque total_retries é chave congelada
                # do RUN.log: propostas além da primeira. Zero no baseline por definição.
                "retries": max(passos - 1, 0),
                "arquivos": arquivos,
                "historico": historico,
                "input_tokens": tokens_in,
                "output_tokens": tokens_out,
                "total_tokens": tokens,
                "cost_usd": round(custo, 6),
            }

        while True:
            estouro = self.orcamento.estourou(passos, custo, inicio)
            if estouro:
                return parte(False, estouro)

            proposta = await self.agente.propor(self._prompt(base, observacoes))
            passos += 1
            custo += proposta.custo_usd
            tokens_in += proposta.input_tokens
            tokens_out += proposta.output_tokens
            tokens += proposta.total_tokens

            try:
                arquivos = projeto.aplicar(proposta.mudanca, self.escopo)
            except EscopoViolado as erro:
                observacoes.append(PropostaRejeitada(str(erro), self.escopo))
                self.trace.registrar(
                    {
                        "etapa": self.id,
                        "passo": passos,
                        "erro": str(erro),
                        "cost_usd": round(custo, 6),
                    }
                )
                continue

            resultado = self.verificar(projeto)
            if resultado is not None:
                historico.append(resultado.contagem)
            self.trace.registrar(
                {
                    "etapa": self.id,
                    "passo": passos,
                    "arquivos": arquivos,
                    "pytest": historico[-1] if resultado is not None else None,
                    "cost_usd": round(custo, 6),
                }
            )
            if resultado is not None and not resultado.passou:
                observacoes.append(PytestFalhou(resultado))
                continue

            feedback = self.permissao.autorizar(self.id, "\n".join(arquivos))
            if feedback is None:
                return parte(True, "verde")
            observacoes.append(feedback)


class EtapaTDD(Etapa):
    """A única diferença real entre etapas: a saída do pytest volta ao modelo."""

    def verificar(self, projeto: Projeto) -> ResultadoPytest:
        return projeto.rodar_pytest()
