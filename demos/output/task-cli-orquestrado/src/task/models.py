"""Modelo Task para representar uma tarefa individual."""


class Task:
    """Representa uma tarefa individual; fornece metodos de construcao e serializacao."""

    def __init__(self, id: int, title: str, priority: str, due_date: str | None, done: bool, created_at: str):
        """
        Inicializa todos os campos.

        Args:
            id: ID unico da tarefa
            title: Titulo da tarefa
            priority: Prioridade (low, medium, high)
            due_date: Data de vencimento em YYYY-MM-DD ou None
            done: Se a tarefa foi concluida
            created_at: Timestamp ISO 8601 de criacao
        """
        self.id = id
        self.title = title
        self.priority = priority
        self.due_date = due_date
        self.done = done
        self.created_at = created_at

    def to_dict(self) -> dict:
        """
        Converte a tarefa para dict serializavel em JSON.

        Returns:
            dict: Representacao da tarefa
        """
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date,
            "done": self.done,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """
        Metodo de classe que constroi um Task a partir de um dict lido do JSON.

        Args:
            data: Dict com os dados da tarefa

        Returns:
            Task: Instancia de Task
        """
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data["priority"],
            due_date=data["due_date"],
            done=data["done"],
            created_at=data["created_at"],
        )
