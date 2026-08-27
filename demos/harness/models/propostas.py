from abc import ABC
from dataclasses import dataclass

from .observacoes import Observacao


class Proposta(ABC):
    """O que sobrou da proposta do modelo depois que o harness tentou aplicá-la."""


@dataclass(frozen=True)
class PropostaAceita(Proposta):
    arquivos: list[str]


@dataclass(frozen=True)
class PropostaRejeitada(Proposta, Observacao):
    """Não chegou ao disco: violou o escopo da etapa. Leva a regra já em texto, porque
    o que volta ao modelo é a regra, não o Escopo."""

    erro: str
    regra: str

    def como_prompt(self) -> str:
        return (
            f"## PROPOSTA REJEITADA\n{self.erro}\n"
            f"Reenvie a Mudanca com caminhos relativos à raiz do projeto: "
            f"{self.regra}.\n"
        )
