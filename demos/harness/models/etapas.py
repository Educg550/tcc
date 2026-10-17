import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .dominio import MEDIDO, Mudanca, Projeto, ResultadoPytest
from .observacoes import PytestFalhou, SessaoFalhou
from .politicas import Orcamento, Permissao
from .propostas import Proposta, PropostaAceita, PropostaRejeitada
from .sessao import IMAGEM, VERSAO, Sessao
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

    @property
    def permissao(self) -> dict:
        """A mesma regra no formato de edição do opencode, onde vale a última que casa."""
        if self.dentro:
            return {"*": "deny", f"{self.dentro}/**": "allow"}
        return {"*": "allow", **{p: "deny" for f in self.fora for p in (f, f"{f}/**")}}

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
    """Um laço: a sessão edita → o harness confere o escopo → observa → autoriza, até o
    orçamento estourar ou nada mais haver a observar. O modelo nunca executa: quem roda
    o pytest é o harness, quem decide é a Permissao."""

    # Skills de autoria de testes só nas etapas que escrevem testes: a baseline e o coder
    # recebem o mesmo inventário de implementação.
    propositos: tuple[str, ...] = ("implementation",)

    @property
    @abstractmethod
    def escopo(self) -> Escopo:
        """Onde a etapa pode escrever. É da classe, não do chamador: etapa que escreve
        fora do seu escopo adultera a própria medição."""

    def __init__(
        self,
        id: str,
        sessao: Sessao,
        permissao: Permissao,
        orcamento: Orcamento,
        trace: Trace,
        skills: list[Path] = (),
    ):
        self.id = id
        self.sessao = sessao
        self.permissao = permissao
        self.orcamento = orcamento
        self.trace = trace
        self.skills = list(skills)

    def inicio(self, projeto: Projeto) -> dict:
        """Estado do projeto no instante em que a etapa começa, medido uma vez e gravado
        junto da etapa no RUN.log."""
        return {}

    def verificar(self, projeto: Projeto) -> ResultadoPytest | None:
        return None

    async def executar(self, base: str, projeto: Projeto) -> dict:
        inicio, passos, custo = time.time(), 0, 0.0
        tokens_in, tokens_out, tokens = 0, 0, 0
        arquivos: set[str] = set()
        skills: list[str] = []
        historico: list[dict] = []
        inicial = self.inicio(projeto)
        # A sessão guarda o histórico: depois do primeiro passo só vai a observação nova.
        prompt = base

        def parte(ok: bool, motivo: str) -> dict:
            return {
                "id": self.id,
                "configured_model": self.sessao.model_id,
                "executor": f"opencode {VERSAO}",
                "imagem": IMAGEM,
                "sessao": self.sessao.id,
                "duration_s": round(time.time() - inicio, 2),
                "ok": ok,
                "motivo": motivo,
                "passos": passos,
                # Derivado de passos, e mantido porque total_retries é chave congelada
                # do RUN.log: chamadas além da primeira. Zero no baseline por definição.
                "retries": max(passos - 1, 0),
                "arquivos": sorted(arquivos),
                "skills": skills,
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

            antes = projeto.estado()
            restante = self.orcamento.tempo_s - (time.time() - inicio)
            turno = await self.sessao.enviar(
                prompt, projeto, self.escopo.permissao, self.skills, restante
            )
            passos += 1
            custo += turno.custo_usd
            tokens_in += turno.input_tokens
            tokens_out += turno.output_tokens
            tokens += turno.total_tokens
            skills += turno.skills
            novos = projeto.alterados(antes)
            arquivos.update(novos)
            evento = {
                "etapa": self.id,
                "passo": passos,
                "arquivos": novos,
                "cost_usd": round(custo, 6),
            }

            # O opencode já nega a edição fora do escopo; isto confere que negou. Escrita
            # que passou mesmo assim adulterou a medição, e a etapa termina aqui.
            try:
                for a in novos:
                    self.escopo.destino(projeto.raiz, a)
            except EscopoViolado as erro:
                self.trace.registrar({**evento, "erro": str(erro)})
                return parte(False, "escopo")

            if turno.erro:
                self.trace.registrar({**evento, "erro": turno.erro})
                prompt = SessaoFalhou(turno.erro).como_prompt()
                continue

            resultado = self.verificar(projeto)
            if resultado is not None:
                historico.append(resultado.contagem)
            self.trace.registrar(
                {**evento, "pytest": historico[-1] if resultado is not None else None}
            )
            if resultado is not None and not resultado.passou:
                prompt = PytestFalhou(resultado.saida).como_prompt()
                continue

            decisao = self.permissao.autorizar(self.id, "\n".join(sorted(arquivos)))
            if decisao.aprovado:
                return parte(True, "verde")
            prompt = decisao.como_prompt()


class EtapaTestes(Etapa):
    """Escreve os testes. Não roda o pytest: vermelho aqui é o esperado."""

    escopo = SO_TESTES
    propositos = ("implementation", "testing")


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
