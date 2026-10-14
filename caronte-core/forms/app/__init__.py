import os
import threading
from app.services.form_service import get_available_forms
from flask import g, Flask, redirect, render_template, request, session, Response
from flask_babel import gettext
from signal import SIGINT, SIGTERM, signal

from .commands import register_commands

from flask_babel import format_date
from werkzeug.routing import BuildError as BuildError

flask_app = None


def create_app():
    global flask_app
    if flask_app is not None:
        return flask_app

    from .extension import babel, csrf, get_locale, senhaunica, redis, LANGUAGES
    from app.config import load_config
    from app.logger import Logger

    app = Flask(__name__, static_folder="static", static_url_path="/static")
    config = load_config()
    app.secret_key = config["SECRET_KEY"]

    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = redis.Redis(host=config["REDIS_URL"], port=6379, db=0)

    app.config["SERVER_NAME"] = (
        config["BASE_URL"].removeprefix("http://").removeprefix("https://")
    )
    if "BABEL_TRANSLATION_DIRECTORIES" in config:
        app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.path.join(
            os.getcwd(), config["BABEL_TRANSLATION_DIRECTORIES"]
        )
    if "BABEL_DEFAULT_LOCALE" in config:
        app.config["BABEL_DEFAULT_LOCALE"] = config["BABEL_DEFAULT_LOCALE"]

    app.config["SENHAUNICA_OAUTH_HOST"] = config["SENHAUNICA_OAUTH_HOST"]
    app.config["SENHAUNICA_REQUEST_TOKEN_RESOURCE"] = config[
        "SENHAUNICA_REQUEST_TOKEN_RESOURCE"
    ]
    app.config["SENHAUNICA_CONSUMER_KEY"] = config["SENHAUNICA_CONSUMER_KEY"]
    app.config["SENHAUNICA_CONSUMER_SECRET"] = config["SENHAUNICA_CONSUMER_SECRET"]
    app.config["SENHAUNICA_AUTHORIZE_URL"] = config["SENHAUNICA_AUTHORIZE_URL"]
    app.config["SENHAUNICA_ACCESS_TOKEN_RESOURCE"] = config[
        "SENHAUNICA_ACCESS_TOKEN_RESOURCE"
    ]
    app.config["SENHAUNICA_CALLBACK_ID"] = config["SENHAUNICA_CALLBACK_ID"]

    senhaunica.init_app(app)
    babel.init_app(app, locale_selector=get_locale)
    csrf.init_app(app)

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop("lang_code", None) if values else None
        if g.lang_code is None:
            g.lang_code = get_locale()

    @app.url_defaults
    def add_language_code(endpoint, values):
        if "lang_code" not in values and g.get("lang_code") is not None:
            values["lang_code"] = g.lang_code

    @app.before_request
    def ensure_lang_in_url():
        path = request.path

        # Ignora arquivos estáticos e favicon
        if (
            path.startswith("/static/")
            or path.startswith("/favicon.ico")
            or path.startswith("/sitemap.xml")
        ):
            return

        # Se já começa com idioma válido, não redireciona
        if any(
            path.startswith(f"/{lang}/") or path.startswith(f"/{lang}")
            for lang in LANGUAGES
        ):
            return

        # Redireciona a raiz ou qualquer rota sem lang_code
        lang = get_locale()
        new_path = f"/{lang}{path}" if path != "/" else f"/{lang}/"
        return redirect(new_path)

    from app.routes import pages as route_pages

    app.register_blueprint(route_pages)

    from app.routes.admin import admin as route_admin

    app.register_blueprint(route_admin)

    from app.routes.api import api as route_api

    app.register_blueprint(route_api)

    from app.routes.form import form as route_form

    app.register_blueprint(route_form)
    Logger.config(app)

    from app.persistence.db import db

    db.initialize(config)

    register_commands(app, db)

    from senhaunicapy.identity import Identity
    from app.entities.User import User
    from app.services.user_service import exist_user

    @app.context_processor
    def inject_globals():

        inject = {"app_url": config["BASE_URL"], "lang": get_locale()}

        dev_email = config.get("DEV_USER_EMAIL")
        if dev_email:
            db_user = exist_user(db, User({"email": dev_email}))
            if db_user.succeeded:
                inject["user"] = {
                    "emailPrincipalUsuario": dev_email,
                    "id": db_user.data["id"],
                    "roleApplication": db_user.data["role"],
                }
            return inject

        if "access_token" not in session or "access_secret" not in session:
            return inject

        _config = app.extensions["senhaunicapy"].config
        try:
            user = Identity.get_protected_resources(
                session["access_token"],
                session["access_secret"],
                "wsusuario/oauth/usuariousp",
                "POST",
                config=_config,
            )
        except Exception as _:
            return inject

        db_user = exist_user(db, User({"email": user["emailPrincipalUsuario"]}))

        if not db_user.succeeded:
            return inject

        user["roleApplication"] = db_user.data["role"]
        inject["user"] = user
        return inject

    @app.template_filter()
    def format_datetime(value, lang=get_locale()):
        formatted = format_date(value, format="medium")
        return formatted

    def signal_handler_exit(sig, frame):
        print(f"Received signal {sig}. Exiting...")
        exit(0)

    def set_signal_handlers(SIGINT, SIGTERM):
        if threading.current_thread() == threading.main_thread():
            signal(SIGINT, lambda signum, frame: signal_handler_exit(signum, frame))
            signal(SIGTERM, lambda signum, frame: signal_handler_exit(signum, frame))

    @app.route("/sitemap.xml", methods=["GET"])
    def sitemap():
        public_forms = get_available_forms(db, lang=get_locale())

        pages = []
        BASE_URL = config["BASE_URL"]

        static_urls = [
            {"loc": BASE_URL + "/"},
        ]

        for page in static_urls:
            pages.append(f"""
                <url>
                    <loc>{page['loc']}</loc>
                    <changefreq>weekly</changefreq>
                    <priority>1.0</priority>
                </url>
                """)

        for form in public_forms.data[:10]:
            loc = f"{BASE_URL}/form/shared/{form['token']}"
            lastmod = form.get("created_at").date()

            hreflangs = []
            for lang in LANGUAGES:
                hreflangs.append(
                    f'<xhtml:link rel="alternate" hreflang="{lang}" '
                    f'href="{BASE_URL}/{lang}/form/shared/{form["token"]}" />'
                )

            hreflangs.append(
                f'<xhtml:link rel="alternate" hreflang="x-default" ' f'href="{loc}" />'
            )

            pages.append(f"""
            <url>
                <loc>{loc}</loc>
                <lastmod>{lastmod}</lastmod>
                {''.join(hreflangs)}
            </url>
            """)

        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:xhtml="http://www.w3.org/1999/xhtml">
            {''.join(pages)}
        </urlset>
        """

        return Response(sitemap_xml, mimetype="application/xml")

    @app.route("/static/<path:filename>")
    def static_files(filename):
        pass

    @app.errorhandler(500)
    def internal_server_error(e):
        Logger.print.exception(f"Erro 500 no caminho {request.path}")
        return e, 500

    @app.errorhandler(404)
    def page_not_found(error):
        lang = g.get("lang_code", get_locale())
        return (
            render_template("404.html", message=error.description, lang_code=lang),
            404,
        )

    @app.errorhandler(401)
    def unauthorized(error):
        lang = g.get("lang_code", get_locale())
        return (
            render_template(
                "unauthorized.html", message=error.description, lang_code=lang
            ),
            401,
        )

    @app.errorhandler(403)
    def forbidden(error):
        lang = g.get("lang_code", get_locale())
        if "CSRF token" in str(error.description):
            return (
                render_template(
                    "message.html",
                    title=gettext(
                        "Sessão expirada. Recarregue a página e tente novamente."
                    ),
                    lang_code=lang,
                ),
                403,
            )
        return (
            render_template(
                "unauthorized.html", message=error.description, lang_code=lang
            ),
            403,
        )

    set_signal_handlers(SIGINT, SIGTERM)

    flask_app = app

    return app
