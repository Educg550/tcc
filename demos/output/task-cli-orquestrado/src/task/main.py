"""Ponto de entrada da CLI; define e despacha os subcomandos via argparse."""

import argparse
import sys

from task.commands import TaskCommands
from task.storage import TaskStorage


def main(argv=None):
    """
    Constroi o parser principal com subparsers (add, list, done, edit, delete, show).

    Args:
        argv: Lista de argumentos (padrao: sys.argv[1:])

    Exit:
        0 se sucesso, != 0 se erro
    """
    if argv is None:
        argv = sys.argv[1:]

    # Criar parser principal
    parser = argparse.ArgumentParser(
        prog="task",
        description="CLI de gerenciador de tarefas",
    )

    # Criar subparsers para comandos
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando add
    add_parser = subparsers.add_parser("add", help="Adiciona uma nova tarefa")
    add_parser.add_argument("title", help="Titulo da tarefa")
    add_parser.add_argument("-p", "--priority", default="low", help="Prioridade (low, medium, high)")
    add_parser.add_argument("-d", "--due", dest="due_date", default=None, help="Data de vencimento (YYYY-MM-DD)")

    # Comando list
    list_parser = subparsers.add_parser("list", help="Lista tarefas")
    list_parser.add_argument("-a", "--all", action="store_true", help="Inclui tarefas concluidas")
    list_parser.add_argument("--done", action="store_true", help="Mostra apenas tarefas concluidas")
    list_parser.add_argument("-p", "--priority", default=None, help="Filtra por prioridade")

    # Comando done
    done_parser = subparsers.add_parser("done", help="Marca tarefa como concluida")
    done_parser.add_argument("task_id", type=int, help="ID da tarefa")

    # Comando edit
    edit_parser = subparsers.add_parser("edit", help="Edita uma tarefa")
    edit_parser.add_argument("task_id", type=int, help="ID da tarefa")
    edit_parser.add_argument("--title", default=None, help="Novo titulo")
    edit_parser.add_argument("-p", "--priority", default=None, help="Nova prioridade")
    edit_parser.add_argument("-d", "--due", dest="due_date", default=None, help="Nova data de vencimento")

    # Comando delete
    delete_parser = subparsers.add_parser("delete", help="Delete uma tarefa")
    delete_parser.add_argument("task_id", type=int, help="ID da tarefa")
    delete_parser.add_argument("--force", action="store_true", help="Nao pedir confirmacao")

    # Comando show
    show_parser = subparsers.add_parser("show", help="Exibe detalhes de uma tarefa")
    show_parser.add_argument("task_id", type=int, help="ID da tarefa")

    # Parse dos argumentos
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        # argparse ja saiu com codigo != 0
        if e.code != 0:
            sys.exit(1)
        sys.exit(0)

    # Criar storage e commands
    storage = TaskStorage()
    commands = TaskCommands(storage)

    # Despachar comando
    try:
        if args.command == "add":
            commands.add(args.title, args.priority, args.due_date)
        elif args.command == "list":
            commands.list_tasks(args.all, args.done, args.priority)
        elif args.command == "done":
            commands.done(args.task_id)
        elif args.command == "edit":
            commands.edit(args.task_id, args.title, args.priority, args.due_date)
        elif args.command == "delete":
            commands.delete(args.task_id, args.force)
        elif args.command == "show":
            commands.show(args.task_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
