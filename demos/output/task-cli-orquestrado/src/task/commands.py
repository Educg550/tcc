"""Implementa a logica de negocio de cada subcomando."""

import sys
from datetime import datetime

from task.models import Task
from task.storage import TaskStorage
from task.validators import validate_due_date, validate_priority


class TaskCommands:
    """Implementa a logica de negocio de cada subcomando."""

    def __init__(self, storage: TaskStorage):
        """
        Recebe uma instancia de TaskStorage.

        Args:
            storage: Instancia de TaskStorage para operacoes de I/O
        """
        self.storage = storage

    def add(self, title: str, priority: str = "low", due_date: str | None = None) -> None:
        """
        Cria nova tarefa com id auto-incremental.

        Args:
            title: Titulo da tarefa
            priority: Prioridade (low, medium, high); default 'low'
            due_date: Data de vencimento em YYYY-MM-DD ou None

        Prints:
            ID da tarefa criada

        Exit:
            1 se validacao falhar
        """
        # Validar prioridade
        try:
            validate_priority(priority)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Validar due_date se fornecido
        if due_date is not None:
            try:
                validate_due_date(due_date)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        # Carregar dados
        data = self.storage.load()

        # Calcular proximo ID
        if data["tasks"]:
            next_id = max(t["id"] for t in data["tasks"]) + 1
        else:
            next_id = 1

        # Criar tarefa
        task = Task(
            id=next_id,
            title=title,
            priority=priority,
            due_date=due_date,
            done=False,
            created_at=datetime.now().isoformat(),
        )

        # Adicionar a lista e salvar
        data["tasks"].append(task.to_dict())
        self.storage.save(data)

        # Imprimir ID criado
        print(next_id)

    def list_tasks(self, show_all: bool = False, only_done: bool = False, priority: str | None = None) -> None:
        """
        Lista tarefas filtradas.

        Args:
            show_all: Se True, inclui tarefas concluidas
            only_done: Se True, mostra apenas concluidas
            priority: Filtro por prioridade (low, medium, high)

        Prints:
            Tarefas formatadas com id, titulo, prioridade e due_date
        """
        data = self.storage.load()

        # Filtrar tarefas
        tasks = data["tasks"]

        # Filtrar por status
        if only_done:
            tasks = [t for t in tasks if t["done"]]
        elif not show_all:
            tasks = [t for t in tasks if not t["done"]]

        # Filtrar por prioridade
        if priority is not None:
            tasks = [t for t in tasks if t["priority"] == priority]

        # Imprimir tarefas
        for task in tasks:
            due_str = task["due_date"] if task["due_date"] else ""
            print(f"{task['id']} {task['title']} {task['priority']} {due_str}".strip())

    def done(self, task_id: int) -> None:
        """
        Marca a tarefa com o id fornecido como done=True.

        Args:
            task_id: ID da tarefa

        Exit:
            1 se ID nao existir
        """
        data = self.storage.load()

        # Procurar tarefa
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"Error: Task with id {task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Marcar como concluida
        task["done"] = True

        # Salvar
        self.storage.save(data)

    def edit(
        self,
        task_id: int,
        title: str | None = None,
        priority: str | None = None,
        due_date: str | None = None,
    ) -> None:
        """
        Atualiza somente os campos fornecidos.

        Args:
            task_id: ID da tarefa
            title: Novo titulo (opcional)
            priority: Nova prioridade (opcional)
            due_date: Nova data de vencimento (opcional)

        Exit:
            1 se ID nao existir ou validacao falhar
        """
        # Validar campos antes de alterar
        if priority is not None:
            try:
                validate_priority(priority)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        if due_date is not None:
            try:
                validate_due_date(due_date)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        # Carregar e procurar tarefa
        data = self.storage.load()
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"Error: Task with id {task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Atualizar campos
        if title is not None:
            task["title"] = title
        if priority is not None:
            task["priority"] = priority
        if due_date is not None:
            task["due_date"] = due_date

        # Salvar
        self.storage.save(data)

    def delete(self, task_id: int, force: bool = False) -> None:
        """
        Remove a tarefa com o id dado.

        Se --force nao for passado, exibe prompt 'y/N' e cancela se resposta nao for 'y'.

        Args:
            task_id: ID da tarefa
            force: Se True, nao pede confirmacao

        Exit:
            1 se ID nao existir ou usuario cancelar
        """
        data = self.storage.load()

        # Procurar tarefa
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"Error: Task with id {task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Se nao force, pedir confirmacao
        if not force:
            response = input(f"Delete task {task_id}? [y/N] ")
            if response.lower() != "y":
                return

        # Remover tarefa
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        self.storage.save(data)

    def show(self, task_id: int) -> None:
        """
        Exibe todos os detalhes de uma unica tarefa.

        Args:
            task_id: ID da tarefa

        Prints:
            Todos os detalhes da tarefa

        Exit:
            1 se ID nao existir
        """
        data = self.storage.load()

        # Procurar tarefa
        task = next((t for t in data["tasks"] if t["id"] == task_id), None)
        if task is None:
            print(f"Error: Task with id {task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Exibir detalhes
        print(f"ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Priority: {task['priority']}")
        print(f"Due Date: {task['due_date'] if task['due_date'] else 'None'}")
        print(f"Done: {task['done']}")
        print(f"Created At: {task['created_at']}")
