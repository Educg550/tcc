"""Funções de validação de entrada da CLI."""

import argparse
from datetime import datetime


class Validators:
    """Funções de validação reutilizáveis pelos handlers e argparse."""

    @staticmethod
    def priority_type(value):
        """
        Função type do argparse. Verifica se está em {low, medium, high}.

        Args:
            value: Valor a validar

        Returns:
            str: O valor se válido

        Raises:
            argparse.ArgumentTypeError: Se inválido
        """
        allowed = {"low", "medium", "high"}
        if value not in allowed:
            raise argparse.ArgumentTypeError(
                f"Prioridade inválida: {value}. Deve ser uma de: {', '.join(allowed)}"
            )
        return value

    @staticmethod
    def date_type(value):
        """
        Função type do argparse. Verifica se está em formato YYYY-MM-DD e é data real.

        Args:
            value: Valor a validar (string)

        Returns:
            str: O valor se válido

        Raises:
            argparse.ArgumentTypeError: Se inválido
        """
        try:
            # Valida o formato e se é data real
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Data inválida: {value}. Use o formato YYYY-MM-DD."
            )
