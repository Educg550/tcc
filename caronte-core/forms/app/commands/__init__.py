from app.common.Result import Result
from flask.cli import AppGroup
import click

from app.logger import Logger

def register_commands(app, db):
    path = "app/commands/application_submissions"
    path_tmp = "tmp"

    commands = AppGroup('commands')

    from app.commands.insert_admin_users import run as insert_admin_users
    @commands.command('admin_users')
    @click.argument("file", default=f"{path}/admin_emails.txt", type=click.File('r'))
    def admin_users_command(file):
        """
        Inserir usuários administradores.

        Os emails com cargo de administração, separados por vírgula.
        """
        try:
            return insert_admin_users(db, file)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))

    from app.commands.insert_application_form import run as insert_application_form
    @commands.command('create_application_form')
    @click.argument("notice", default="mestrado", type=str)
    @click.argument("year", default="2026", type=str)
    def application_form_command(notice, year):
        "Criar formulário para ser preenchido por candidatos."
        try:
            return insert_application_form(db, notice, year)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))

    from app.commands.insert_doctorate_application_form import run as insert_doctorate_application_form
    @commands.command('create_doctorate_application_form')
    @click.argument("notice", default="doutorado", type=str)
    @click.argument("year", default="2026", type=str)
    def application_doctorate_form_command(notice, year):
        "Criar formulário de doutorado para ser preenchido por candidatos."
        try:
            return insert_doctorate_application_form(db, notice, year)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))

    from app.commands.insert_recommenders_form import run as insert_recommenders_form
    @commands.command('create_recommenders_form')
    @click.argument("notice", default="mestrado", type=str)
    @click.argument("year", default="2026", type=str)
    def create_recommenders_form_command(notice, year):
        "Criar formulário para ser preenchido por recomendadores."
        try:
            return insert_recommenders_form(db, notice, year)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))
        
    from app.commands.insert_accept_form import run as insert_accept_form
    @commands.command('create_accept_form')
    @click.argument("notice", default="mestrado", type=str)
    @click.argument("year", default="2026", type=str)
    def create_accept_form_command(notice, year):
        "Criar formulário para ser preenchido por aprovados."
        try:
            return insert_accept_form(db, notice, year)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))
            
    from app.commands.generate_recommender_list import run as generate_recommender_list
    @commands.command('generate_recommender_list')
    @click.argument('application_form_id', type=int)
    @click.argument('recommender_form_id', type=int)
    @click.argument('expiration_at', type=click.DateTime())
    def generate_recommender_list_command(application_form_id, recommender_form_id, expiration_at):
        """
        Salvar tabela com recomendadores.

        **Submeter as respostas externas usando a função de *upload* do formulário.**
        """
        try:
            return generate_recommender_list(db, application_form_id, recommender_form_id, expiration_at)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))

    from app.commands.send_recommenders_email import run as send_recommenders_email
    @commands.command('send_recommenders_email')
    @click.argument("file", default=f"{path_tmp}/tmp_recommenders.csv", type=click.File('r'))
    def send_recommenders_email_command(file):
        """
        Enviar e-mails para recomendados.

        **Filename** salvo no servidor pelo comando `generate_recommender_list_command`.
        """
        try:
            return send_recommenders_email(db, file)
        except Exception as e:
            Logger.print.warning(e)
            return Result(message=str(e))

    app.cli.add_command(commands)
    return commands
