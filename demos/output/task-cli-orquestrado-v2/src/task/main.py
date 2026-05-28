"""Ponto de entrada da CLI."""

import sys
from pathlib import Path

from task.cli import CLI
from task.handlers import Handlers
from task.storage import TaskStorage


def main():
    """
    Ponto de entrada da CLI invocada via `python -m task`.

    Constrói o parser argparse de nível superior, delega para os handlers
    e retorna o código de saída adequado.
    """
    # Determina o diretório de trabalho (cwd)
    work_dir = Path.cwd()

    # Cria as instâncias de storage e handlers
    storage = TaskStorage(work_dir)
    handlers = Handlers(storage)

    # Cria a CLI
    cli = CLI(handlers)

    # Faz parse e executa
    return cli.parse_and_run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
