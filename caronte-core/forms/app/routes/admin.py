from flask_babel import gettext
import click
from app.common import file_to_stringio
from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    current_app,
    redirect,
    url_for,
    flash,
)
from jinja2 import TemplateNotFound
import re

from app.config import load_config

from app.logger import Logger
from app.middleware import require_authorization

config = load_config()


admin = Blueprint(
    "admin", __name__, url_prefix="/<lang_code>/admin", template_folder="templates"
)


@admin.route("/logs")
@require_authorization(role="administrator")
def logs(user):
    try:
        return render_template("admin/logs.html")
    except TemplateNotFound:
        abort(404)


@admin.route("/script/<string:id>", methods=["GET", "POST"])
@require_authorization(role="administrator")
def script(user, id):
    if not request.referrer:
        return redirect(url_for("admin.scripts"))

    commands = current_app.cli.commands["commands"].commands

    popup_mode = False
    if request.referrer:
        popup_mode = True

    if id in commands:
        command = commands[id]
        script = {"name": command.name, "help": command.help, "params": []}

        if command.params:
            for index, param in enumerate(command.params):
                _type = "Text"
                if param.type.__class__ is click.types.StringParamType:
                    _type = "Text"
                elif param.type.__class__ is click.types.IntParamType:
                    _type = "Text"
                elif param.type.__class__ is click.types.DateTime:
                    _type = "Date"
                elif param.type.__class__ is click.types.File:
                    _type = "File"

                script["params"].append(
                    {
                        "type": _type,
                        "name": param.name,
                        "label": param.name,
                        "position": index,
                        "required": param.required,
                    }
                )

        if request.method == "POST":
            form = request.form.copy()
            del form["_csrf_token"]
            if "file" in request.files:
                file = request.files["file"]
                stringio = file_to_stringio(file)
                if not stringio.succeeded:
                    flash(stringio.message, "warning")
                    return redirect(url_for("admin.scripts"))
                form["file"] = stringio.data
            try:
                result = command.callback.__wrapped__(**form)
                if result.message:
                    if result.succeeded:
                        flash(result.message, "info")
                    else:
                        flash(result.message, "warning")
            except Exception as e:
                flash(e, "error")
                Logger.print.error(e)

            return redirect(url_for("admin.scripts"))

        return render_template(
            "admin/script.html", script=script, popup_mode=popup_mode
        )

    return abort(404)


@admin.route("/scripts")
@require_authorization(role="administrator")
def scripts(user):
    search = request.args.get("search", "", type=str)
    commands = current_app.cli.commands["commands"].commands

    header = {
        "func": {"label": gettext("Função"), "type": "str"},
        "params": {"label": gettext("Parâmetros"), "type": "str"},
        "help": {"label": gettext("Descrição"), "type": "str"},
    }

    data = []
    for key, value in commands.items():
        if search in key:
            data.append(
                {
                    "id": key,
                    "func": key,
                    "params": ", ".join(
                        [
                            f"{param.name} <{re.findall('[A-Z][^A-Z]*', param.type.__class__.__name__)[0].title()}>"
                            for param in value.params
                        ]
                    ),
                    "help": value.help,
                }
            )

    try:
        return render_template(
            "admin/scripts.html",
            scripts=data,
            header=header,
            options={"search": search},
        )
    except TemplateNotFound:
        abort(404)
