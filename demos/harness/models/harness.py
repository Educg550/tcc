from abc import ABC, abstractmethod

from .agentes import Agente
from .dominio import CODIGO, SO_TESTES, Escopo, Modo, Projeto, Requisito
from .etapas import Etapa, EtapaTDD
from .politicas import Orcamento, Permissao
from .tracing import Resultado, Trace


class Harness(ABC):
    """Ambiente onde o modelo SUGERE mudanças e não executa nada: propõe, e o harness
    valida, autoriza, executa, registra e devolve observações.

    As subclasses são os dois grupos do experimento. Emitem o mesmo Resultado, com o
    mesmo orçamento e a mesma diretiva de estilo — o que varia entre elas é só a
    presença de etapas, que é a variável independente."""

    def __init__(
        self,
        projeto: Projeto,
        requisito: Requisito,
        permissao: Permissao,
        orcamento: Orcamento | None = None,
    ):
        self.projeto = projeto
        self.requisito = requisito
        self.permissao = permissao
        self.orcamento = orcamento or Orcamento()
        self.trace = Trace(projeto.saida / "trace.jsonl")

    def etapa(
        self, id: str, agente: Agente, escopo: Escopo, classe: type[Etapa] = Etapa
    ) -> Etapa:
        return classe(id, agente, escopo, self.permissao, self.orcamento, self.trace)

    @abstractmethod
    async def etapas(self, modo: Modo, resultado: Resultado) -> None: ...

    async def executar(self) -> dict:
        modo = Modo.detectar(self.projeto)
        self.projeto.preparar()
        antes = modo.baseline(self.projeto)
        resultado = Resultado(
            modo=modo.nome,
            requisito_id=self.requisito.id,
            antes=antes.contagem if antes else None,
        )
        await self.etapas(modo, resultado)
        resultado.pytest_final = self.projeto.rodar_pytest().contagem
        self.projeto.commitar(self.requisito.id)
        return resultado.gravar(self.projeto.saida / "RUN.log")


class HarnessTDD(Harness):
    """Grupo experimental: requisito → testes → implementação sob CI."""

    async def etapas(self, modo: Modo, resultado: Resultado) -> None:
        testes = self.etapa("tests", Agente.test_writer(), SO_TESTES)
        base = self.requisito.texto + modo.contexto(self.projeto)
        resultado.stages.append(await testes.executar(base, self.projeto))
        # Teste que já passa antes da implementação não é contrato, é tautologia.
        vermelho = not self.projeto.rodar_pytest().passou

        codigo = self.etapa("code", Agente.coder(), CODIGO, EtapaTDD)
        base = (
            f"{self.requisito.texto}\n\n## TESTES A FAZER PASSAR\n\n"
            f"{self.projeto.contexto('tests')}\n"
        )
        parte = await codigo.executar(base, self.projeto)
        resultado.loop = {**parte, "tests_vermelhos": vermelho}


class HarnessDireto(Harness):
    """Grupo baseline: requisito → modelo → código, uma etapa. Sem testes gerados, sem
    CI, sem CUA no loop. A ausência é a variável independente, não um prompt pior."""

    async def etapas(self, modo: Modo, resultado: Resultado) -> None:
        direta = self.etapa("direto", Agente.direto(), CODIGO)
        base = self.requisito.texto + modo.contexto(self.projeto)
        parte = await direta.executar(base, self.projeto)
        resultado.loop = {**parte, "tests_vermelhos": None}
