from abc import ABC, abstractmethod
from dataclasses import asdict

from .agentes import Agente, Avaliador, load
from .dominio import Modo, Projeto, Requisito
from .etapas import Etapa, EtapaCodigo, EtapaTDD, EtapaTestes
from .politicas import Permissao
from .tracing import Resultado, Trace


class Harness(ABC):
    """Ambiente onde o modelo SUGERE mudanças e não executa nada: propõe, e o harness
    valida, autoriza, executa, registra e devolve observações.

    As subclasses são os dois grupos do experimento. Emitem o mesmo Resultado, com o
    mesmo orçamento e a mesma diretiva de estilo - o que varia entre elas é só a
    presença de etapas, que é a variável independente."""

    def __init__(
        self,
        projeto: Projeto,
        requisito: Requisito,
        permissao: Permissao,
    ):
        self.projeto = projeto
        self.requisito = requisito
        self.permissao = permissao
        self.orcamento = requisito.orcamento
        self.trace = Trace(projeto.saida / "trace.jsonl")

    @property
    def contrato(self) -> str:
        """A restrição de execução vem do caso de uso e é a mesma para os dois grupos."""
        alvo = self.projeto.alvo
        return load("contrato_alvo").format(
            comando_app=alvo.comando_app, comando_teste=alvo.comando_teste
        )

    def prompt(self, *partes: str) -> str:
        return "\n\n".join(
            p for p in (self.requisito.texto, self.contrato, *partes) if p.strip()
        )

    def etapa(self, id: str, agente: Agente, classe: type[Etapa]) -> Etapa:
        return classe(id, agente, self.permissao, self.orcamento, self.trace)

    @abstractmethod
    async def etapas(self, modo: Modo) -> list[dict]: ...

    async def executar(self) -> dict:
        modo = Modo.detectar(self.projeto)
        self.projeto.preparar()
        antes = modo.baseline(self.projeto)
        resultado = Resultado(
            modo=modo.nome,
            requisito_id=self.requisito.id,
            alvo={**self.projeto.alvo.como_dict(), "modelos": self.requisito.modelos},
            orcamento=asdict(self.orcamento),
            antes=antes.contagem if antes else None,
        )
        resultado.stages = await self.etapas(modo)
        resultado.impressao_fim = self.projeto.impressao()
        resultado.pytest_final = self.projeto.rodar_pytest().contagem
        # Instrumento de medida da variável dependente, igual nos dois grupos: roda antes
        # de gravar, senão o veredito não entra na medição da própria run.
        avaliador = Avaliador(self.requisito.modelos["cua"])
        resultado.cua = await avaliador.avaliar(self.projeto, self.requisito)
        log = resultado.gravar(self.projeto.saida / "RUN.log")
        self.projeto.commitar(self.requisito.id)
        return log


class HarnessTDD(Harness):
    """Grupo experimental: requisito → testes → implementação sob CI."""

    async def etapas(self, modo: Modo) -> list[dict]:
        modelos = self.requisito.modelos
        testes = self.etapa(
            "tests", Agente.de("test_writer", modelos["test_writer"]), EtapaTestes
        )
        base = self.prompt(modo.contexto(self.projeto))
        parte_testes = await testes.executar(base, self.projeto)

        codigo = self.etapa("code", Agente.de("coder", modelos["coder"]), EtapaTDD)
        base = self.prompt(
            "## TESTES A FAZER PASSAR\n\n" + self.projeto.contexto("tests")
        )
        return [parte_testes, await codigo.executar(base, self.projeto)]


class HarnessDireto(Harness):
    """Grupo baseline: requisito → modelo → código, uma etapa. Sem testes gerados, sem
    CI, sem CUA no loop. A ausência é a variável independente, não um prompt pior."""

    async def etapas(self, modo: Modo) -> list[dict]:
        # Roda com o modelo do coder: modelo diferente entre os grupos confundiria
        # modelo com pipeline.
        modelo = self.requisito.modelos["coder"]
        direta = self.etapa("direto", Agente.de("direto", modelo), EtapaCodigo)
        base = self.prompt(modo.contexto(self.projeto))
        return [await direta.executar(base, self.projeto)]
