import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .agentes import Agente
from .dominio import MEDIDO, Mudanca, Projeto, ResultadoPytest
from .observacoes import Observacao, PytestFalhou
from .politicas import Orcamento, Permissao
from .propostas import Proposta, PropostaAceita, PropostaRejeitada
from .tracing import Trace


class EscopoViolado(ValueError):
    pass


@dataclass(frozen=True)
class Escopo:
    """Onde uma etapa pode escrever: um prefixo permitido e prefixos negados."""

    dentro: str | None = None
    fora: tuple[str, ...] = ()

    def destino(self, raiz: Path, caminho: str) -> Path:
        alvo = (raiz / caminho).resolve()
        limite = (raiz / self.dentro).resolve() if self.dentro else raiz
        if not alvo.is_relative_to(limite):
            raise EscopoViolado(f"{caminho}: fora de {self.dentro or '.'}/")
        for negado in self.fora:
            if alvo.is_relative_to((raiz / negado).resolve()):
                raise EscopoViolado(f"{caminho}: {negado} é proibido")
        return alvo

    @property
    def regra(self) -> str:
        if self.dentro:
            return f"todo caminho começa com `{self.dentro}/`"
        return "nenhum caminho em " + ", ".join(f"`{f}`" for f in self.fora)

    def aplicar(self, mudanca: Mudanca, projeto: Projeto) -> Proposta:
        """Valida todos os caminhos antes de escrever qualquer um: proposta inválida
        não deixa mudança pela metade para o pytest medir."""
        try:
            destinos = [
                (self.destino(projeto.raiz, a.caminho), a.conteudo)
                for a in mudanca.arquivos
            ]
        except EscopoViolado as erro:
            return PropostaRejeitada(str(erro), self.regra)
        return PropostaAceita(projeto.escrever(destinos))


SO_TESTES = Escopo(dentro="tests")
CODIGO = Escopo(fora=MEDIDO + ("_harness", ".git"))


class Etapa(ABC):
    """Um laço: propor → validar → escrever → observar → autorizar, até o orçamento
    estourar ou nada mais haver a observar. O modelo nunca executa: quem escreve é
    o Projeto, quem decide é a Permissao."""

    @property
    @abstractmethod
    def escopo(self) -> Escopo:
        """Onde a etapa pode escrever. É da classe, não do chamador: etapa que escreve
        fora do seu escopo adultera a própria medição."""

    def __init__(
        self,
        id: str,
        agente: Agente,
        permissao: Permissao,
        orcamento: Orcamento,
        trace: Trace,
    ):
        self.id = id
        self.agente = agente
        self.permissao = permissao
        self.orcamento = orcamento
        self.trace = trace

    def inicio(self, projeto: Projeto) -> dict:
        """Estado do projeto no instante em que a etapa começa, medido uma vez e gravado
        junto da etapa no RUN.log."""
        return {}

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
        inicial = self.inicio(projeto)

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
                **inicial,
            }

        while True:
            estouro = self.orcamento.estourou(passos, custo, inicio)
            if estouro:
                return parte(False, estouro)

            resposta = await self.agente.propor(self._prompt(base, observacoes))
            passos += 1
            custo += resposta.custo_usd
            tokens_in += resposta.input_tokens
            tokens_out += resposta.output_tokens
            tokens += resposta.total_tokens

            proposta = self.escopo.aplicar(resposta.mudanca, projeto)
            if isinstance(proposta, PropostaRejeitada):
                observacoes.append(proposta)
                self.trace.registrar(
                    {
                        "etapa": self.id,
                        "passo": passos,
                        "erro": proposta.erro,
                        "cost_usd": round(custo, 6),
                    }
                )
                continue
            arquivos = proposta.arquivos

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
                observacoes.append(PytestFalhou(resultado.saida))
                continue

            decisao = self.permissao.autorizar(self.id, "\n".join(arquivos))
            if decisao.aprovado:
                return parte(True, "verde")
            observacoes.append(decisao)


class EtapaTestes(Etapa):
    """Escreve os testes. Não roda o pytest: vermelho aqui é o esperado."""

    escopo = SO_TESTES


class EtapaCodigo(Etapa):
    """Escreve o código de produção. Registra a impressão dos testes no instante em que
    começa: é contra ela que a integridade da run é medida no fim."""

    escopo = CODIGO

    def inicio(self, projeto: Projeto) -> dict:
        return {"impressao": projeto.impressao(), "tests_vermelhos": None}


class EtapaTDD(EtapaCodigo):
    """A única diferença real entre etapas: a saída do pytest volta ao modelo."""

    def inicio(self, projeto: Projeto) -> dict:
        # Teste que já passa antes da implementação não é contrato, é tautologia.
        return {
            **super().inicio(projeto),
            "tests_vermelhos": not projeto.rodar_pytest().passou,
        }

    def verificar(self, projeto: Projeto) -> ResultadoPytest:
        return projeto.rodar_pytest()
