"""Modelo de dominio de uma tarefa."""


class Task:
    """Encapsula uma tarefa com id, titulo, prioridade, data de vencimento e status."""

    def __init__(self, id, title, priority, due_date, done, created_at):
        """
        Construtor da tarefa.

        Args:
            id: Identificador único (int auto-incremental)
            title: Título da tarefa (str)
            priority: Prioridade ("low"|"medium"|"high")
            due_date: Data de vencimento ("YYYY-MM-DD" ou None)
            done: Status de conclusão (bool)
            created_at: Data de criação em ISO 8601 (str)
        """
        self.id = id
        self.title = title
        self.priority = priority
        self.due_date = due_date
        self.done = done
        self.created_at = created_at

    def to_dict(self):
        """Serializa a tarefa para dicionário compatível com JSON."""
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date,
            "done": self.done,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Desserializa um dicionário e retorna uma instância Task."""
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data["priority"],
            due_date=data["due_date"],
            done=data["done"],
            created_at=data["created_at"],
        )
