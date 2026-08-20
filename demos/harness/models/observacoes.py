from abc import ABC, abstractmethod
from dataclasses import dataclass

from .dominio import Escopo, ResultadoPytest


class Observacao(ABC):
    """O que o harness devolve ao modelo depois de uma proposta. Cada subclasse sabe
    se anunciar no prompt, em vez de o laço concatenar strings à mão."""

    @abstractmethod
    def como_prompt(self) -> str: ...


@dataclass(frozen=True)
class FeedbackHumano(Observacao):
    texto: str

    def como_prompt(self) -> str:
        return f"## FEEDBACK ANTERIOR\n{self.texto}\n"


@dataclass(frozen=True)
class PropostaRejeitada(Observacao):
    erro: str
    escopo: Escopo

    def como_prompt(self) -> str:
        return (
            f"## PROPOSTA REJEITADA\n{self.erro}\n"
            f"Reenvie a Mudanca com caminhos relativos à raiz do projeto: "
            f"{self.escopo.regra}.\n"
        )


@dataclass(frozen=True)
class PytestFalhou(Observacao):
    resultado: ResultadoPytest

    def como_prompt(self) -> str:
        return (
            f"## PYTEST FALHOU\n```\n{self.resultado.saida[-4000:]}\n```\n"
            "Corrija o código de produção. Não altere os testes.\n"
        )
