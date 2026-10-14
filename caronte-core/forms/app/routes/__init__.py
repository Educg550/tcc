from app.exceptions.error_messages import IDENTITY_ERROR
from app.extension import LANGUAGES as LANGUAGES, get_locale
from app.middleware import require_authorization
from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    session,
    redirect,
    url_for,
    current_app,
)
from jinja2 import TemplateNotFound
from app.services.form_service import get_available_forms
from app.services.section_service import get_fields_by_section, get_section_by_id
from senhaunicapy.identity import Identity

from app.config import load_config


from app.entities.User import User
from app.services.user_service import create_user
from app.logger import Logger as Logger
from app.persistence.db import db

config = load_config()
pages = Blueprint(
    "pages", __name__, url_prefix="/<lang_code>", template_folder="templates"
)


@pages.route("/", methods=["GET", "POST"])
def index():
    public_forms = get_available_forms(db, lang=get_locale())

    section_pos = 0
    for public_form in public_forms.data:
        sections = get_section_by_id(db, public_form["id"])
        current_section = sections.data[section_pos]
        section = get_fields_by_section(
            db, public_form["id"], current_section["id"], lang=get_locale()
        )
        if "title" in section.data:
            section.data["title"] = ""
        public_form["first_page"] = section.data

    if request.method == "POST":
        form = request.form.copy()
        return redirect(url_for("form.index", token=form["search"]))
    try:
        return render_template(
            "index.html",
            public_forms=public_forms.data,
            section_pos=section_pos,
            total=1,
        )
    except TemplateNotFound:
        abort(404)


@pages.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("pages.index"))


@pages.route("/login", methods=["GET"])
def login():
    callback_url = request.args.get("callback_url")
    if callback_url is None:
        callback_url = "pages.index"

    if "access_token" not in session:
        try:
            return render_template("login.html")
        except TemplateNotFound:
            abort(404)
    else:
        callback_params = request.args.to_dict()
        if "callback_url" in callback_params:
            del callback_params["callback_url"]
        try:
            return redirect(url_for(callback_url, **callback_params))
        except Exception as _:
            abort(404)


@pages.route("/profile")
@require_authorization()
def profile(user):
    try:
        return render_template("profile.html")
    except TemplateNotFound:
        abort(404)


@pages.route("/about")
def about():
    try:
        return render_template("about.html")
    except TemplateNotFound:
        abort(404)


@pages.route("/login/senhaunica", methods=["GET"])
def login_senhaunica():
    config = current_app.extensions["senhaunicapy"].config
    oauth_token = request.args.get("oauth_token")

    if oauth_token is None:
        try:
            response_request_token = Identity.get_request_token(config=config)
        except Exception:
            abort(500, IDENTITY_ERROR())
        session["request_secret"] = response_request_token.secret_token
        return redirect(response_request_token.url)
    else:
        if "request_secret" not in session:
            abort(500, IDENTITY_ERROR())

        oauth_verifier = request.args.get("oauth_verifier")

        try:
            response_access_token = Identity.get_access_token(
                oauth_token, session["request_secret"], oauth_verifier, config=config
            )
        except Exception:
            abort(500, IDENTITY_ERROR())

        session.pop("request_secret", default=None)

        # caso tenha alguem fora do filtro que possa acessar as rotas
        FILE_PATH = "app/commands/application_submissions/nusp_whitelist.txt"
        nusp_whitelist = []
        with open(FILE_PATH, "r") as f:
            for row in f:
                row = row.strip()
                if row:
                    nusp_whitelist.extend(map(str, row.split(",")))

        def filter_fn(vinculos, nusp):
            return (
                any(
                    v["tipoFuncao"] == "Docente" and v["codigoUnidade"] == 45
                    for v in vinculos
                )
                or nusp in nusp_whitelist
            )

        try:
            user = Identity.get_protected_resources(
                response_access_token.access_token,
                response_access_token.access_secret,
                "wsusuario/oauth/usuariousp",
                "POST",
                affiliation_filter=filter_fn,
                config=config,
            )
        except Exception:
            abort(500, IDENTITY_ERROR())

        session["access_token"] = response_access_token.access_token
        session["access_secret"] = response_access_token.access_secret

        create_user(db, User({"email": user["emailPrincipalUsuario"]}))

        return """<script type="text/javascript">window.opener.location.reload();self.close();</script>"""
