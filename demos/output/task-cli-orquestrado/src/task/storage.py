"""Responsavel por ler e gravar tasks.json."""

import json
from pathlib import Path


class TaskStorage:
    """Responsavel por ler e gravar tasks.json no diretorio de trabalho atual."""

    def __init__(self, path: Path | None = None):
        """
        Recebe o caminho do arquivo JSON (padrao: Path.cwd() / 'tasks.json').

        Args:
            path: Caminho do arquivo JSON; se None, usa Path.cwd() / 'tasks.json'
        """
        if path is None:
            self.path = Path.cwd() / "tasks.json"
        else:
            self.path = path

    def load(self) -> dict:
        """
        Le tasks.json e retorna o dict {'version': 1, 'tasks': [...]}.

        Se o arquivo nao existir, cria-o vazio (version=1, tasks=[]) e retorna a estrutura vazia.

        Returns:
            dict: Dicionario com chaves 'version' e 'tasks'
        """
        if not self.path.exists():
            # Criar arquivo vazio
            data = {"version": 1, "tasks": []}
            self.save(data)
            return data

        # Ler arquivo existente
        return json.loads(self.path.read_text())

    def save(self, data: dict) -> None:
        """
        Serializa o dict de dados em tasks.json com indentacao.

        Args:
            data: Dicionario para serializar
        """
        self.path.write_text(json.dumps(data, indent=2))
