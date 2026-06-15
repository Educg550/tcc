"""Interface de linha de comando."""

import argparse

from task.validators import Validators


class CLI:
    """Monta o ArgumentParser com todos os subcomandos."""

    def __init__(self, handlers):
        """
        Construtor.

        Args:
            handlers: Instância de Handlers
        """
        self.handlers = handlers
        self.parser = self._build_parser()

    def _build_parser(self):
        """Cria o ArgumentParser principal com todos os subparsers."""
        parser = argparse.ArgumentParser(
            prog="task",
            description="CLI de gerenciamento de tarefas",
        )
        subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

        self._register_add(subparsers)
        self._register_list(subparsers)
        self._register_done(subparsers)
        self._register_edit(subparsers)
        self._register_delete(subparsers)
        self._register_show(subparsers)

        return parser

    def _register_add(self, subparsers):
        """Registra o subparser do comando add."""
        add_parser = subparsers.add_parser("add", help="Adicionar nova tarefa")
        add_parser.add_argument("title", help="Título da tarefa")
        add_parser.add_argument(
            "-p",
            "--priority",
            type=Validators.priority_type,
            default="low",
            help="Prioridade (low/medium/high)",
        )
        add_parser.add_argument(
            "-d",
            "--due",
            type=Validators.date_type,
            default=None,
            dest="due_date",
            help="Data de vencimento (YYYY-MM-DD)",
        )
        add_parser.set_defaults(func=self.handlers.cmd_add)

    def _register_list(self, subparsers):
        """Registra o subparser do comando list."""
        list_parser = subparsers.add_parser("list", help="Listar tarefas")
        list_parser.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Incluir tarefas concluídas",
        )
        list_parser.add_argument(
            "--done",
            action="store_true",
            help="Mostrar apenas concluídas",
        )
        list_parser.add_argument(
            "-p",
            "--priority",
            type=Validators.priority_type,
            default=None,
            help="Filtrar por prioridade",
        )
        list_parser.set_defaults(func=self.handlers.cmd_list)

    def _register_done(self, subparsers):
        """Registra o subparser do comando done."""
        done_parser = subparsers.add_parser("done", help="Marcar tarefa como concluída")
        done_parser.add_argument("id", type=int, help="ID da tarefa")
        done_parser.set_defaults(func=self.handlers.cmd_done)

    def _register_edit(self, subparsers):
        """Registra o subparser do comando edit."""
        edit_parser = subparsers.add_parser("edit", help="Editar tarefa")
        edit_parser.add_argument("id", type=int, help="ID da tarefa")
        edit_parser.add_argument(
            "--title",
            type=str,
            default=None,
            help="Novo título",
        )
        edit_parser.add_argument(
            "-p",
            "--priority",
            type=Validators.priority_type,
            default=None,
            help="Nova prioridade",
        )
        edit_parser.add_argument(
            "-d",
            "--due",
            type=Validators.date_type,
            default=None,
            dest="due_date",
            help="Nova data de vencimento",
        )
        edit_parser.set_defaults(func=self.handlers.cmd_edit)

    def _register_delete(self, subparsers):
        """Registra o subparser do comando delete."""
        delete_parser = subparsers.add_parser("delete", help="Deletar tarefa")
        delete_parser.add_argument("id", type=int, help="ID da tarefa")
        delete_parser.add_argument(
            "--force",
            action="store_true",
            help="Deletar sem pedir confirmação",
        )
        delete_parser.set_defaults(func=self.handlers.cmd_delete)

    def _register_show(self, subparsers):
        """Registra o subparser do comando show."""
        show_parser = subparsers.add_parser("show", help="Exibir detalhes da tarefa")
        show_parser.add_argument("id", type=int, help="ID da tarefa")
        show_parser.set_defaults(func=self.handlers.cmd_show)

    def parse_and_run(self, argv=None):
        """
        Faz parse de argv e invoca o handler associado.

        Args:
            argv: Lista de argumentos (se None, usa sys.argv[1:])

        Returns:
            int: Código de saída
        """
        try:
            args = self.parser.parse_args(argv)
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

        # Se nenhum comando foi especificado, mostra ajuda
        if not hasattr(args, "func"):
            self.parser.print_help()
            return 1

        # Executa o handler
        return args.func(args)
