from abc import ABC, abstractmethod
from dataclasses import asdict

from .agentes import Agente, Avaliador, load
from .dominio import Projeto, Requisito
from .etapas import Etapa, EtapaCodigo, EtapaTDD, EtapaTestes
from .politicas import Permissao
from .tracing import Resultado, Trace


class Harness(ABC):
    """Ambiente onde o modelo SUGERE mudanças e não executa nada: propõe, e o harness
    valida, autoriza, executa, registra e devolve observações.

    As subclasses são os dois grupos do experimento. Emitem o mesmo Resultado, com o
    mesmo orçamento e a mesma diretiva de estilo - o que varia entre elas é só a
    presença de etapas, que é a variável independente."""

    grupo: str

    def __init__(
        self,
        projeto: Projeto,
        requisito: Requisito,
        permissao: Permissao,
        com_cua: bool = True,
    ):
        self.projeto = projeto
        self.requisito = requisito
        self.permissao = permissao
        self.com_cua = com_cua
        self.orcamento = requisito.orcamento
        self.trace = Trace(projeto.saida / "trace.jsonl")

    @property
    def contrato(self) -> str:
        """A restrição de execução vem do caso de uso e é a mesma para os dois grupos."""
        alvo = self.projeto.alvo
        return load("contrato_alvo").format(
            comando_app=alvo.comando_app,
            comando_teste=alvo.comando_teste,
            python=alvo.python,
            pacotes="\n".join(f"- `{p}`" for p in alvo.pacotes),
        )

    def prompt(self, *partes: str) -> str:
        return "\n\n".join(
            p for p in (self.requisito.texto, self.contrato, *partes) if p.strip()
        )

    def etapa(self, id: str, agente: Agente, classe: type[Etapa]) -> Etapa:
        return classe(id, agente, self.permissao, self.orcamento, self.trace)

    @abstractmethod
    async def etapas(self) -> list[dict]: ...

    async def executar(self) -> dict:
        # Toda run gera do zero: projeto reaproveitado mediria manutenção de código que
        # já existe, e não a geração que o experimento compara.
        if self.projeto.raiz.exists() and any(self.projeto.raiz.iterdir()):
            raise SystemExit(
                f"{self.projeto.raiz} já tem arquivos: cada run parte de um projeto novo"
            )
        self.projeto.preparar()
        self.projeto.semear(self.requisito.anexos)
        resultado = Resultado(
            grupo=self.grupo,
            requisito_id=self.requisito.id,
            alvo={**self.projeto.alvo.como_dict(), "modelos": self.requisito.modelos},
            orcamento=asdict(self.orcamento),
        )
        resultado.stages = await self.etapas()
        resultado.impressao_fim = self.projeto.impressao()
        resultado.pytest_final = self.projeto.rodar_pytest().contagem
        # Instrumento de medida da variável dependente, igual nos dois grupos. Grava o
        # próprio CUA.log: o veredito é medida do app rodando, não do pipeline que o fez.
        if self.com_cua:
            await Avaliador(self.requisito.modelos["cua"]).avaliar(
                self.projeto, self.requisito
            )
        log = resultado.gravar(self.projeto.saida / "RUN.log")
        return log


class HarnessTDD(Harness):
    """Grupo experimental: requisito → testes → implementação sob CI."""

    grupo = "tdd"

    async def etapas(self) -> list[dict]:
        modelos = self.requisito.modelos
        testes = self.etapa(
            "tests", Agente.de("test_writer", modelos["test_writer"]), EtapaTestes
        )
        parte_testes = await testes.executar(self.prompt(), self.projeto)

        codigo = self.etapa("code", Agente.de("coder", modelos["coder"]), EtapaTDD)
        base = self.prompt(
            "## TESTES A FAZER PASSAR\n\n" + self.projeto.contexto("tests")
        )
        return [parte_testes, await codigo.executar(base, self.projeto)]


class HarnessDireto(Harness):
    """Grupo baseline: requisito → modelo → código, uma etapa. Sem testes gerados, sem
    CI, sem CUA no loop. A ausência é a variável independente, não um prompt pior."""

    grupo = "baseline"

    async def etapas(self) -> list[dict]:
        # Roda com o modelo do coder: modelo diferente entre os grupos confundiria
        # modelo com pipeline.
        modelo = self.requisito.modelos["coder"]
        direta = self.etapa("direto", Agente.de("direto", modelo), EtapaCodigo)
        return [await direta.executar(self.prompt(), self.projeto)]
