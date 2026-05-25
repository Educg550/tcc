"""Funcoes puras de validacao para priority e due_date."""

from datetime import datetime


def validate_priority(value: str) -> str:
    """
    Verifica se o valor e um dos literais 'low', 'medium' ou 'high' (case-sensitive).

    Args:
        value: Valor a validar

    Returns:
        str: O valor validado

    Raises:
        ValueError: Se o valor nao estiver entre os valores validos
    """
    valid_priorities = {"low", "medium", "high"}
    if value not in valid_priorities:
        raise ValueError(f"Priority must be one of {valid_priorities}, got {value!r}")
    return value


def validate_due_date(value: str) -> str:
    """
    Verifica se a string esta no formato YYYY-MM-DD e representa uma data calendario valida.

    Args:
        value: Valor a validar em formato YYYY-MM-DD

    Returns:
        str: O valor validado

    Raises:
        ValueError: Se malformada ou inexistente (ex.: 2025-02-30)
    """
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Due date must be in YYYY-MM-DD format and valid, got {value!r}") from e
    return value
