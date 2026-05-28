"""Permite executar o pacote como `python -m task`."""

import sys

from task.main import main

if __name__ == "__main__":
    sys.exit(main())
