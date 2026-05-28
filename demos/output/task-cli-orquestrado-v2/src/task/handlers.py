"""Lógica de negócio de cada subcomando."""

import sys


class Handlers:
    """Executa as operações de cada subcomando."""

    def __init__(self, storage):
        """
        Construtor.

        Args:
            storage: Instância de TaskStorage
        """
        self.storage = storage

    def cmd_add(self, args):
        """
        Executa `task add`.

        Persiste nova tarefa; retorna 0.

        Args:
            args: Namespace do argparse

        Returns:
            int: Código de saída (0=sucesso)
        """
        try:
            self.storage.add_task(
                title=args.title,
                priority=args.priority,
                due_date=args.due_date,
            )
            return 0
        except Exception as e:
            print(f"Erro ao adicionar tarefa: {e}", file=sys.stderr)
            return 1

    def cmd_list(self, args):
        """
        Executa `task list`.

        Filtra por status e prioridade; imprime no stdout.

        Args:
            args: Namespace do argparse

        Returns:
            int: Código de saída (sempre 0)
        """
        tasks = self.storage.all_tasks()

        # Filtro de status
        if args.done:
            # Apenas concluídas
            tasks = [t for t in tasks if t.done]
        elif not args.all:
            # Apenas pendentes (padrão)
            tasks = [t for t in tasks if not t.done]
        # else: all=True, inclui todas

        # Filtro de prioridade
        if args.priority:
            tasks = [t for t in tasks if t.priority == args.priority]

        # Imprime tarefas
        if tasks:
            for task in tasks:
                status = "[X]" if task.done else "[ ]"
                print(f"{status} [{task.id}] {task.title} ({task.priority})")
        else:
            print("Nenhuma tarefa encontrada.")

        return 0

    def cmd_done(self, args):
        """
        Executa `task done <id>`.

        Marca como concluída; retorna 1 se inexistente.

        Args:
            args: Namespace do argparse

        Returns:
            int: Código de saída (0=sucesso, 1=erro)
        """
        task = self.storage.mark_done(args.id)
        if task is None:
            print(f"Tarefa com ID {args.id} não encontrada.", file=sys.stderr)
            return 1
        print(f"Tarefa {args.id} marcada como concluída.")
        return 0

    def cmd_edit(self, args):
        """
        Executa `task edit <id>`.

        Atualiza campos informados; retorna 1 se ID inexistente ou validação falhar.
        Requer pelo menos um campo (title, priority ou due_date) para ser atualizado.

        Args:
            args: Namespace do argparse

        Returns:
            int: Código de saída (0=sucesso, 1=erro)
        """
        # Valida que pelo menos um campo foi informado
        if args.title is None and args.priority is None and args.due_date is None:
            print("Erro: É necessário informar pelo menos um campo para editar (--title, -p ou -d).", file=sys.stderr)
            return 1

        try:
            task = self.storage.update_task(
                task_id=args.id,
                title=args.title,
                priority=args.priority,
                due_date=args.due_date,
            )
            if task is None:
                print(f"Tarefa com ID {args.id} não encontrada.", file=sys.stderr)
                return 1
            print(f"Tarefa {args.id} atualizada.")
            return 0
        except Exception as e:
            print(f"Erro ao editar tarefa: {e}", file=sys.stderr)
            return 1

    def cmd_delete(self, args):
        """
        Executa `task delete <id>`.

        Com --force remove diretamente; sem flag lê confirmação y/N do stdin.

        Args:
            args: Namespace do argparse

        Returns:
            int: Código de saída (0=sucesso/cancelamento, 1=erro)
        """
        if not args.force:
            # Pede confirmação
            resposta = input(f"Tem certeza que deseja deletar tarefa {args.id}? (y/N): ").strip()
            if resposta.lower() != "y":
                print("Operação cancelada.")
                return 0

        # Tenta deletar
        removida = self.storage.delete_task(args.id)
        if not removida:
            print(f"Tarefa com ID {args.id} não encontrada.", file=sys.stderr)
            return 1

        print(f"Tarefa {args.id} deletada.")
        return 0

    def cmd_show(self, args):
        """
        Executa `task show <id>`.

        Imprime todos os campos da tarefa no stdout.

        Args:
            args: Namespace do argparse

        Returns:
            int: Código de saída (0=sucesso, 1=erro)
        """
        task = self.storage.get_by_id(args.id)
        if task is None:
            print(f"Tarefa com ID {args.id} não encontrada.", file=sys.stderr)
            return 1

        print(f"ID: {task.id}")
        print(f"Título: {task.title}")
        print(f"Prioridade: {task.priority}")
        print(f"Data de vencimento: {task.due_date or 'Não definida'}")
        print(f"Status: {'Concluída' if task.done else 'Pendente'}")
        print(f"Criada em: {task.created_at}")

        return 0
