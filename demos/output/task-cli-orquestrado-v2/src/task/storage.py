"""Camada de persistência de tarefas."""

import json
from datetime import datetime
from pathlib import Path

from task.models import Task


class TaskStorage:
    """Gerencia a leitura e gravação de tarefas em tasks.json."""

    def __init__(self, directory):
        """
        Construtor.

        Args:
            directory: Path do diretório onde tasks.json deve ser mantido
        """
        self.directory = Path(directory)

    def _path(self):
        """Retorna o Path completo para tasks.json."""
        return self.directory / "tasks.json"

    def _empty_store(self):
        """Retorna a estrutura inicial {"version": 1, "tasks": []}."""
        return {"version": 1, "tasks": []}

    def load(self):
        """
        Lê tasks.json.

        Se não existir, retorna estrutura vazia sem criar.
        Retorna dict bruto com version e tasks.
        """
        caminho = self._path()
        if not caminho.exists():
            return self._empty_store()
        try:
            conteudo = caminho.read_text(encoding="utf-8")
            return json.loads(conteudo)
        except (json.JSONDecodeError, IOError):
            return self._empty_store()

    def save(self, data):
        """
        Persiste o dict bruto (version + lista de tasks) em tasks.json.

        Cria o arquivo se não existir.

        Args:
            data: Dicionário com "version" e "tasks"
        """
        caminho = self._path()
        caminho.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def all_tasks(self):
        """
        Retorna lista de instâncias Task carregadas do arquivo.

        Retorna lista vazia se arquivo ausente.
        """
        data = self.load()
        return [Task.from_dict(t) for t in data.get("tasks", [])]

    def get_by_id(self, task_id):
        """
        Retorna a Task com o id informado, ou None se não existir.

        Args:
            task_id: ID da tarefa

        Returns:
            Task ou None
        """
        tasks = self.all_tasks()
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    def next_id(self, tasks):
        """
        Calcula o próximo ID: 1 se lista vazia, ou max(ids) + 1.

        Args:
            tasks: Lista de Tasks

        Returns:
            int: Próximo ID a usar
        """
        if not tasks:
            return 1
        return max(t.id for t in tasks) + 1

    def add_task(self, title, priority, due_date):
        """
        Cria e persiste nova Task com id auto-incremental e created_at em ISO 8601.

        Args:
            title: Título da tarefa
            priority: Prioridade ("low"|"medium"|"high")
            due_date: Data de vencimento ("YYYY-MM-DD" ou None)

        Returns:
            Task: A tarefa criada
        """
        tasks = self.all_tasks()
        task_id = self.next_id(tasks)
        created_at = datetime.now().isoformat()
        task = Task(
            id=task_id,
            title=title,
            priority=priority,
            due_date=due_date,
            done=False,
            created_at=created_at,
        )
        # Carrega, adiciona e salva
        data = self.load()
        data["tasks"].append(task.to_dict())
        self.save(data)
        return task

    def update_task(self, task_id, title=None, priority=None, due_date=None):
        """
        Atualiza apenas os campos não-None e persiste.

        Args:
            task_id: ID da tarefa
            title: Novo título (opcional)
            priority: Nova prioridade (opcional)
            due_date: Nova data de vencimento (opcional)

        Returns:
            Task ou None se não encontrada
        """
        data = self.load()
        tasks = data.get("tasks", [])
        for t in tasks:
            if t["id"] == task_id:
                if title is not None:
                    t["title"] = title
                if priority is not None:
                    t["priority"] = priority
                if due_date is not None:
                    t["due_date"] = due_date
                self.save(data)
                return Task.from_dict(t)
        return None

    def mark_done(self, task_id):
        """
        Define done=True e persiste.

        Args:
            task_id: ID da tarefa

        Returns:
            Task ou None se não encontrada
        """
        data = self.load()
        tasks = data.get("tasks", [])
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = True
                self.save(data)
                return Task.from_dict(t)
        return None

    def delete_task(self, task_id):
        """
        Remove a Task com o task_id informado e persiste.

        Args:
            task_id: ID da tarefa

        Returns:
            bool: True se removida, False se não encontrada
        """
        data = self.load()
        tasks = data.get("tasks", [])
        original_len = len(tasks)
        data["tasks"] = [t for t in tasks if t["id"] != task_id]
        if len(data["tasks"]) < original_len:
            self.save(data)
            return True
        return False
