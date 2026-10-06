"""Utilitários de formatação."""


def formatar_moeda(valor):
    """Recebe o número de centavos e devolve a string formatada, sem espaços."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
