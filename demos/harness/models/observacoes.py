from abc import ABC, abstractmethod
from dataclasses import dataclass

# Sem import de domínio: `propostas` e `politicas` importam daqui, e o domínio
# importa `propostas`. Por isso as observações guardam texto pronto, não objetos.


class Observacao(ABC):
    """O que o harness devolve ao modelo depois de uma proposta. Cada subclasse sabe
    se anunciar no prompt, em vez de o laço concatenar strings à mão."""

    @abstractmethod
    def como_prompt(self) -> str: ...


@dataclass(frozen=True)
class PytestFalhou(Observacao):
    saida: str

    def como_prompt(self) -> str:
        return (
            f"## PYTEST FALHOU\n```\n{self.saida[-4000:]}\n```\n"
            "Corrija o código de produção. Não altere os testes.\n"
        )
