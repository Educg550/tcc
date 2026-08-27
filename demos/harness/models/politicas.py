import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .observacoes import FeedbackHumano


class Permissao(ABC):
    """Quem decide se a proposta já escrita encerra a etapa."""

    @abstractmethod
    def autorizar(self, etapa: str, resumo: str) -> FeedbackHumano | None: ...


class Batch(Permissao):
    """Autoriza tudo. É o modo do experimento: os dois grupos recebem exatamente a
    mesma ajuda humana, ou seja, nenhuma."""

    def autorizar(self, etapa: str, resumo: str) -> None:
        return None


class Interativa(Permissao):
    def autorizar(self, etapa: str, resumo: str) -> FeedbackHumano | None:
        barra = "═" * 60
        print(f"\n{barra}\n  Etapa: {etapa}\n{barra}\n{resumo}\n{barra}")
        pergunta = f"[{etapa}] aprovar? (y/n): "
        while (r := input(pergunta).strip().lower()) not in ("y", "n"):
            print("  Digite 'y' ou 'n'.")
        if r == "y":
            return None
        texto = ""
        while not texto.strip():
            texto = input("Feedback: ")
        return FeedbackHumano(texto.strip())


@dataclass(frozen=True)
class Orcamento:
    """Teto da etapa, declarado pelo caso de uso. Toda proposta custa um passo, inclusive
    a rejeitada: ela também custou uma chamada de modelo."""

    passos: int
    custo_usd: float
    tempo_s: int

    def estourou(self, passos: int, custo: float, inicio: float) -> str | None:
        if passos >= self.passos:
            return "passos"
        if custo >= self.custo_usd:
            return "custo"
        if time.time() - inicio >= self.tempo_s:
            return "tempo"
        return None
