from abc import ABC, abstractmethod
from dataclasses import dataclass

# Sem import de domínio: `propostas` e `politicas` importam daqui, e o domínio
# importa `propostas`. Por isso as observações guardam texto pronto, não objetos.


class Observacao(ABC):
    """O que o harness devolve ao modelo depois de uma proposta. Cada subclasse sabe
    se anunciar no prompt, em vez de o laço concatenar strings à mão."""

    @abstractmethod
    def como_prompt(self) -> str: ...


LIMITE_SAIDA = 8000
NAO_ALTERE = "Corrija o código de produção. Não altere os testes."


@dataclass(frozen=True)
class PytestFalhou(Observacao):
    saida: str
    logs: str = ""
    instrucao: str = NAO_ALTERE

    def como_prompt(self) -> str:
        # O começo traz os primeiros tracebacks; o fim, o resumo e a contagem.
        saida = self.saida
        if len(saida) > LIMITE_SAIDA:
            inicio, fim = saida[: LIMITE_SAIDA * 3 // 4], saida[-LIMITE_SAIDA // 4 :]
            saida = f"{inicio}\n[... {len(saida) - len(inicio) - len(fim)} caracteres omitidos ...]\n{fim}"
        logs = f"## LOGS DO APP\n```\n{self.logs}\n```\n" if self.logs else ""
        return f"## PYTEST FALHOU\n```\n{saida}\n```\n{logs}{self.instrucao}\n"


@dataclass(frozen=True)
class RespostaInvalida(Observacao):
    """A sessão terminou sem propor arquivos. O consumo continua contado."""

    erro: str

    def como_prompt(self) -> str:
        return (
            f"## RESPOSTA INVÁLIDA\n{self.erro}\n"
            "Use as ferramentas para ler o projeto e editar os arquivos necessários.\n"
        )
