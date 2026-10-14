from app.extension import get_locale
from app.repositories.collaborator_service import get_all_collaborator_by_form
from app.services.collaborator_service import can_access_form, invite_collaborator_form
from app.services.field_service import get_field_by_name, update_field_by_id
from app.services.file_service import (
    handle_download_file,
    handle_request_files,
    remove_request_files,
)
from app.services.response_service import (
    create_partial_response,
    create_partial_upload,
    create_response,
    finalize_response,
    get_response_info,
)
from app.services.section_service import (
    get_fields_by_section,
    get_section_by_id,
    load_section_info,
    set_section,
)
from app.services.token_service import (
    create_shared_token,
    edit_shared_token,
    get_all_tokens_by_form_id,
    get_or_create_response_token,
    get_shared_token_info,
    get_token_by_id,
)
from flask_babel import gettext
import csv
from datetime import datetime
import json
from distutils.util import strtobool

from app.common import file_to_stringio, render_template_or_404
from app.entities.Field import Field
from app.entities.Form import Form
from app.entities.FormResponse import FormResponse
from app.exceptions.error_messages import (
    CREATED_TOKEN,
    ERROR,
    ERROR_UPDATE_TOKEN,
    FORM_NOT_FOUND,
    IDENTITY_PERMISSION_DENIED,
    NO_FILE_PART,
    POSITION_FILE_ERROR,
    REMOVED_FORM,
    SUBMIT_FORM,
)
from flask import (
    Blueprint,
    jsonify,
    abort,
    request,
    flash,
    send_from_directory,
    url_for,
    redirect,
)

from app.config import load_config

from app.services.form_service import (
    create_form,
    get_all_user_forms,
    get_all_submissions_dict,
    get_form_dict,
    get_viewer_form_dict,
    get_submissions_by_id,
    get_tags,
    handle_tokens,
    load_send_by_email_field,
    remove_form_by_id,
    send_response_to_email,
    send_url_to_email,
    update_form_by_id,
)
from app.middleware import optional_authorization, require_authorization
from app.logger import Logger
from app.persistence.db import db

config = load_config()

form = Blueprint(
    "form", __name__, url_prefix="/<lang_code>/form", template_folder="templates"
)


@form.route("/")
@require_authorization()
def forms(user):
    """
    Listar todos os formulários que o usuário tem acesso
    """
    FORM_HEADERS = {
        "id": {"label": "ID", "type": "str"},
        "title": {"label": gettext("Título"), "type": "str"},
        "created_at": {"label": gettext("Criado em"), "type": "datetime"},
        "created_by": {"label": gettext("Criado por"), "type": "str"},
    }

    order_by = request.args.get("order_by", 1, type=int)
    order_type = request.args.get("order_type", 0, type=int)
    search = request.args.get("search", "", type=str)
    if order_type not in [0, 1]:
        order_type = 0

    tag_filter = get_tags(db, request.args).data

    list_forms = get_all_user_forms(
        db, user, order_by, order_type, tag_filter, search=search
    )

    return render_template_or_404(
        "form/forms.html",
        list_forms=list_forms.data,
        header=FORM_HEADERS,
        options={
            "search": search,
            "order_by": order_by,
            "order_type": order_type,
            "tags": tag_filter,
        },
    )


@form.route("/viewer/<int:id>")
@require_authorization()
def viewer(user, id):
    """
    Visualizar estrutura de formulários que o usuário tenha acesso
    """
    can_access = can_access_form(db, user, id)
    if not can_access.succeeded or not can_access.data:
        abort(404, FORM_NOT_FOUND())

    res = get_viewer_form_dict(db, id)

    if not res.succeeded:
        abort(404, FORM_NOT_FOUND())

    return render_template_or_404("form/viewer.html", form_id=id, form=res.data)


@form.route("/submissions/<int:id>")
@require_authorization()
def submissions(user, id):
    """
    Verificar todas as submissões que usuário tenha acesso
    """
    can_access = can_access_form(db, user, id)
    if not can_access.succeeded or not can_access.data:
        abort(404, FORM_NOT_FOUND())

    order_by = request.args.get("order_by", 1, type=int)
    order_type = request.args.get("order_type", 0, type=int)
    search = request.args.get("search", "", type=str)

    header = {
        "id": {"label": "id", "type": "str"},
        "submitted_at": {"label": gettext("Submetido em"), "type": "datetime"},
        "email": {"label": gettext("Submetido por"), "type": "str"},
    }

    if order_type not in [0, 1]:
        order_type = 0

    res = get_all_submissions_dict(db, id, order_by, order_type, search=search)

    if not res.succeeded:
        abort(404, res.message)

    for data in res.data:
        for response in data["responses"]:
            for k, v in response.items():
                if k not in header:
                    header[f"r-{k}"] = {"label": v["label"], "type": "str"}
            response = {f"r-{k}": v["value"] for k, v in response.items()}
            data.update(response)
        del data["responses"]

    return render_template_or_404(
        "form/submissions.html",
        form_id=id,
        submissions=res.data,
        header=header,
        options={"search": search, "order_by": order_by, "order_type": order_type},
    )


@form.route("/create", methods=["GET", "POST"])
@require_authorization()
def create(user):
    if request.method == "POST":
        form = request.form.copy()
        del form["_csrf_token"]
        form_schema = None

        # convert string json to dict json
        try:
            form_schema = json.loads(form["form"])
        except json.JSONDecodeError as e:
            flash(POSITION_FILE_ERROR(e.pos, e.lineno, e.colno), "error")
            return redirect(url_for("form.forms"))
        except Exception:
            flash(ERROR(), "error")
            return redirect(url_for("form.forms"))

        # reserved keys
        form_schema["created_at"] = datetime.today()
        form_schema["created_by"] = user["id"]
        form_schema["version"] = 1
        form_schema["metadata"] = {
            "client_ip": request.remote_addr,
            "browser": request.user_agent if request.user_agent else "",
        }

        form_id = create_form(db, form_schema)

        if not form_id.succeeded:
            Logger.print.warning(form_id.message)
            flash(form_id.message, "error")
            return redirect(url_for("form.forms"))

        flash(form_id.message, "info")
        return redirect(url_for("form.forms"))

    return render_template_or_404("form/create.html")


@form.route("/edit/<int:id>", methods=["GET", "POST"])
@require_authorization()
def edit_form(user, id):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        abort(401, FORM_NOT_FOUND())

    if request.method == "POST":
        form = request.form.copy()
        del form["_csrf_token"]
        form_schema = None

        try:
            form_schema = json.loads(form["form"])
        except json.JSONDecodeError as e:
            flash(POSITION_FILE_ERROR(e.pos, e.lineno, e.colno), "error")
            return redirect(url_for("form.viewer", id=id))
        except Exception:
            flash(ERROR(), "error")
            return redirect(url_for("form.viewer", id=id))

        update_result = update_form_by_id(db, id, form_schema)

        if not update_result.succeeded:
            Logger.print.warning(update_result.message)
            flash(update_result.message, "error")
            return redirect(url_for("form.viewer", id=id))

        flash(update_result.message, "info")
        return redirect(url_for("form.viewer", id=id))

    res = get_viewer_form_dict(db, id)
    if not res.succeeded:
        abort(404, FORM_NOT_FOUND())

    popup_mode = False
    if request.referrer:
        popup_mode = True

    return render_template_or_404(
        "form/create.html",
        existing_form=res.data,
        form_id=id,
        popup_mode=popup_mode,
    )


@form.route("/upload/<int:id>", methods=["GET", "POST"])
@require_authorization()
def upload(user, id):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        abort(401, FORM_NOT_FOUND())

    if request.method == "POST":
        if "file" not in request.files:
            flash(NO_FILE_PART(), "warning")
            return redirect(url_for("form.submissions", id=id))
        file = request.files["file"]

        stringio = file_to_stringio(file, ["csv"])
        if not stringio.succeeded:
            flash(stringio.message, "warning")
            return redirect(url_for("form.submissions", id=id))

        reader = csv.DictReader(stringio.data, delimiter=",")
        for index, row_reader in enumerate(reader):
            form_response = FormResponse(
                {
                    "form_id": id,
                    "submitted_at": datetime.today(),
                    "metadata": {
                        "client_ip": str(request.remote_addr),
                        "browser": str(request.user_agent),
                        "__message__": "submitted by the system",
                    },
                }
            )
            form_response_id = create_response(db, form_response, responses=row_reader)

            if form_response_id.succeeded:
                flash(form_response_id.message, "info")
            else:
                flash(form_response_id.message, "warning")

        return redirect(url_for("form.submissions", id=id))

    popup_mode = False
    if request.referrer:
        popup_mode = True

    return render_template_or_404("form/upload.html", popup_mode=popup_mode)


@form.route("/<int:id>/field/<string:name>/edit", methods=["GET", "POST"])
@require_authorization()
def field_edit(user, id, name):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        abort(401, FORM_NOT_FOUND())

    field = get_field_by_name(db, id, name)
    if not field.succeeded:
        abort(404)

    if request.method == "POST":
        form = request.form.copy()
        del form["_csrf_token"]
        insert_values = {}
        for key, value in dict(form).items():
            label, lang = key.split(".")
            if label not in insert_values:
                insert_values[label] = {}
            insert_values[label][lang] = value

        update_field_by_id(db, field.data["id"], insert_values)

        return redirect(url_for("form.viewer", id=id))

    popup_mode = False
    if request.referrer:
        popup_mode = True

    return render_template_or_404(
        "form/field/edit.html", popup_mode=popup_mode, field_data=field.data
    )


@form.route("/settings/<int:id>")
@require_authorization()
def settings(user, id):
    can_access = can_access_form(db, user, id)
    if not can_access.succeeded or not can_access.data:
        abort(404, FORM_NOT_FOUND())

    # settings new token
    header_tokens = {
        "id": {"label": "id", "type": "str"},
        "token": {"label": gettext("Token"), "type": "str"},
        "unique_answers": {"label": gettext("Respostas únicas"), "type": "boolean"},
        "is_public": {"label": gettext("Público"), "type": "boolean"},
        "created_at": {"label": gettext("Criado em"), "type": "datetime"},
        "expiration_at": {"label": gettext("Expira em"), "type": "datetime"},
    }
    tokens = get_all_tokens_by_form_id(db, id)
    if not tokens.succeeded:
        abort(404, tokens.message)
    form_new_token = Form(
        {
            "fields": [
                Field(
                    {
                        "name": "expires-in",
                        "label": gettext("Expira em"),
                        "type": "Date",
                        "position": 0,
                    }
                ),
                Field(
                    {
                        "name": "single-answer",
                        "label": gettext(
                            "Só é permitida uma resposta por participante"
                        ),
                        "type": "CheckBox",
                        "options": [
                            gettext("Respostas únicas"),
                        ],
                        "position": 1,
                    }
                ),
                Field(
                    {
                        "name": "is-public",
                        "label": gettext("É um compartilhamento público?"),
                        "type": "CheckBox",
                        "options": [gettext("Sim")],
                        "position": 2,
                    }
                ),
            ]
        }
    )

    # settings invite collaborator
    header_collaborator = {
        "invited_by_email": {"label": gettext("Invitado por"), "type": "str"},
        "user_email": {"label": gettext("Usuário"), "type": "str"},
        "can_edit": {"label": gettext("Pode editar?"), "type": "boolean"},
    }
    collaborators = get_all_collaborator_by_form(db, id)
    if collaborators is None:
        abort(500)

    form_invite_collaborator = Form(
        {
            "fields": [
                Field(
                    {
                        "name": "email",
                        "label": gettext("E-mail"),
                        "type": "Text",
                        "position": 3,
                        "required": True,
                    }
                ),
                Field(
                    {
                        "name": "access-level",
                        "label": gettext("Nível de acesso"),
                        "type": "Radio",
                        "options": [gettext("Visualização"), gettext("Edição")],
                        "required": True,
                        "position": 4,
                    }
                ),
            ]
        }
    )

    return render_template_or_404(
        "form/settings.html",
        form_id=id,
        header_tokens=header_tokens,
        tokens=tokens.data,
        form_new_token=form_new_token,
        header_collaborator=header_collaborator,
        collaborators=collaborators,
        form_invite_collaborator=form_invite_collaborator,
    )


@form.route("/invite-collaborator/<int:id>", methods=["POST"])
@require_authorization()
def invite_collaborator(user, id):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        flash(IDENTITY_PERMISSION_DENIED(), "warning")
        return redirect(url_for("pages.index"))

    form = request.form.copy()

    can_edit = False
    if "access-level" in form and form["access-level"] == gettext("Edição"):
        can_edit = True
    invite_result = invite_collaborator_form(db, id, user, form.get("email"), can_edit)
    if not invite_result.succeeded:
        flash(invite_result.message, "warning")

    return redirect(url_for("pages.index"))


@form.route("/create/token/<int:id>", methods=["POST"])
@require_authorization()
def create_token(user, id):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        flash(IDENTITY_PERMISSION_DENIED(), "warning")
        return redirect(url_for("pages.index"))

    form = request.form.copy()

    # https://www.rfc-editor.org/rfc/rfc3339#section-5.6
    # full-date = date-fullyear "-" date-month "-" date-mday
    response = {"form_id": id}

    if "expires-in" in form and form["expires-in"]:
        response["expiration_at"] = datetime.strptime(form["expires-in"], "%Y-%m-%d")

    if "single-answer[1]" in form and form["single-answer[1]"]:
        response["unique_answers"] = True

    if "is-public[1]" in form and form["is-public[1]"]:
        response["is_public"] = True

    create_shared_token(db, response)

    flash(CREATED_TOKEN(), "info")
    return redirect(url_for("pages.index"))


@form.route("/remove/<int:id>", methods=["POST"])
@require_authorization()
def remove_form(user, id):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        flash(IDENTITY_PERMISSION_DENIED(), "warning")
        return redirect(url_for("pages.index"))

    remove_form_by_id(db, id)

    flash(REMOVED_FORM(), "info")
    return redirect(url_for("pages.index"))


@form.route("/edit/token/<int:id>", methods=["GET", "POST"])
@require_authorization()
def edit_token(user, id):
    can_access = can_access_form(db, user, id, action="edit")
    if not can_access.succeeded or not can_access.data:
        abort(401, FORM_NOT_FOUND())

    if request.method == "POST":
        form = request.form.copy()
        del form["_csrf_token"]

        response = {}

        if "expires-in" in form and form["expires-in"]:
            response["expiration_at"] = datetime.strptime(
                form["expires-in"], "%Y-%m-%d"
            )

        if "single-answer[1]" in form and form["single-answer[1]"]:
            response["unique_answers"] = True

        if "is-public[1]" in form and form["is-public[1]"]:
            response["is_public"] = True

        token = edit_shared_token(db, id, response)
        if not token.succeeded:
            flash(ERROR_UPDATE_TOKEN(), "warning")

        return redirect(url_for("form.settings", id=id))

    form_edit_token = Form(
        {
            "fields": [
                Field(
                    {
                        "name": "expires-in",
                        "label": gettext("Expira em"),
                        "type": "Date",
                        "position": 0,
                    }
                ),
                Field(
                    {
                        "name": "single-answer",
                        "label": gettext(
                            "Só é permitida uma resposta por participante"
                        ),
                        "type": "CheckBox",
                        "options": [gettext("Respostas únicas")],
                        "position": 1,
                    }
                ),
                Field(
                    {
                        "name": "is-public",
                        "label": gettext("É um compartilhamento público?"),
                        "type": "CheckBox",
                        "options": [gettext("Sim")],
                        "position": 2,
                    }
                ),
            ]
        }
    )

    token = get_token_by_id(db, id)
    if not token.succeeded:
        flash(FORM_NOT_FOUND(), "warning")
        return render_template_or_404("form/edit_token.html")

    entry = {
        "0": token.data["expiration_at"],
        "1_1": token.data["unique_answers"],
        "2_1": token.data["is_public"],
    }

    popup_mode = False
    if request.referrer:
        popup_mode = True

    return render_template_or_404(
        "form/edit_token.html",
        entry=entry,
        form_edit_token=form_edit_token,
        popup_mode=popup_mode,
    )


@form.route("shared/<uuid:token>", methods=["GET", "POST"])
@optional_authorization()
def access_shared(user, token):
    token_data = get_shared_token_info(db, token=str(token))
    if not token_data.succeeded:
        return (
            render_template_or_404(
                "message.html",
                title=token_data.message,
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )

    section_pos = 0
    sections = get_section_by_id(db, token_data.data["form_id"])
    current_section = sections.data[section_pos]
    section = get_fields_by_section(
        db, token_data.data["form_id"], current_section["id"], lang=get_locale()
    )

    if request.method == "POST":
        form_response = FormResponse(
            {
                "email": request.form["__email__"],
                "metadata": {
                    "client_ip": request.remote_addr,
                    "browser": request.user_agent,
                },
            }
        )

        if user is not None:
            form_response["user_id"] = user["id"]

        response_token = get_or_create_response_token(
            db, token_data.data, form_response
        )
        if not response_token.succeeded:
            return (
                render_template_or_404(
                    "message.html", title=ERROR(), messages=[response_token.message]
                ),
                400,
            )

        external_url = url_for(
            "form.form_section",
            response_token=str(response_token.data["token"]),
            _external=True,
        )
        send_url_to_email(
            db,
            request.form["__email__"],
            section.data["title"],
            str(external_url),
            token_data.data["expiration_at"],
        )

        return (
            render_template_or_404(
                "message.html",
                title=gettext("Verifique seu e-mail para obter o link de acesso."),
                messages=[gettext("Acesso liberado com sucesso")],
            ),
            400,
        )

    return render_template_or_404(
        "form/shared.html",
        title=section.data["title"],
        unique_answers=token_data.data["unique_answers"],
    )


@form.route("/<uuid:response_token>/download/<string:filename>")
@optional_authorization()
def download_file(user, response_token, filename):
    fileargs = handle_download_file(db, response_token, filename)

    if not fileargs.succeeded:
        abort(400, fileargs.message)

    try:
        return send_from_directory(**fileargs.data)
    except FileNotFoundError:
        abort(404)


@form.route("/<uuid:response_token>/upload", methods=["POST"])
@optional_authorization()
def upload_file(user, response_token):
    tokens_info = handle_tokens(db, response_token)
    if not tokens_info.succeeded:
        flash(tokens_info.message, "warning")
        return (
            render_template_or_404(
                "message.html",
                title=tokens_info.message,
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )
    tokens_info = tokens_info.data

    section_info = load_section_info(
        db,
        request.args.get("entry"),
        tokens_info["form_id"],
        tokens_info["response_id"],
        tokens_info["current_pos"],
    )
    if not section_info.succeeded:
        abort(400, section_info.message)
    section_info = section_info.data

    form_data = request.form.copy()

    fields = [
        field
        for field in section_info["section"]["fields"]
        if field["name"] in request.files.keys()
    ]
    result_request_files = handle_request_files(
        fields, section_info, form_data, request.files
    )
    if not result_request_files.succeeded:
        abort(500, result_request_files.message)

    partial_response = create_partial_upload(
        db,
        tokens_info["response_id"],
        fields,
        form_data,
        ignore_validations=False,
        entry=section_info["entry_name"],
    )
    if not partial_response.succeeded:
        abort(500, partial_response.message)

    return partial_response.message, 200


@form.route("/<uuid:response_token>/upload", methods=["DELETE"])
@optional_authorization()
def remove_file(user, response_token):
    tokens_info = handle_tokens(db, response_token)
    if not tokens_info.succeeded:
        flash(tokens_info.message, "warning")
        return (
            render_template_or_404(
                "message.html",
                title=tokens_info.message,
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )
    tokens_info = tokens_info.data

    section_info = load_section_info(
        db,
        request.args.get("entry"),
        tokens_info["form_id"],
        tokens_info["response_id"],
        tokens_info["current_pos"],
    )
    if not section_info.succeeded:
        abort(400, section_info.message)
    section_info = section_info.data

    body = request.get_json()

    fields = [
        field
        for field in section_info["section"]["fields"]
        if field["name"] == body.get("inputName")
    ]
    if len(fields) <= 0:
        abort(500)
    result = remove_request_files(db, fields[0], response_token, body.get("filename"))
    if not result.succeeded:
        abort(500, result.message)

    form_data = {fields[0].get("name"): ""}
    partial_response = create_partial_upload(
        db,
        tokens_info["response_id"],
        fields,
        form_data,
        ignore_validations=True,
        entry=section_info["entry_name"],
    )
    if not partial_response.succeeded:
        abort(500, partial_response.message)

    return partial_response.message, 200


@form.route("/<uuid:response_token>", methods=["GET", "POST"])
@optional_authorization()
def form_section(user, response_token):
    tokens_info = handle_tokens(db, response_token)
    if not tokens_info.succeeded:
        flash(tokens_info.message, "warning")
        return (
            render_template_or_404(
                "message.html",
                title=tokens_info.message,
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )
    tokens_info = tokens_info.data

    if (
        tokens_info["token_data"].get("phase") == "Approval"
        and tokens_info["token_data"].get("submitted_at") is None
    ):
        return (
            render_template_or_404(
                "message.html",
                title=ERROR(),
                messages=[gettext("Formulário não está mais disponível para envios.")],
            ),
            400,
        )

    section_info = load_section_info(
        db,
        request.args.get("entry"),
        tokens_info["form_id"],
        tokens_info["response_id"],
        tokens_info["current_pos"],
    )
    if not section_info.succeeded:
        return (
            render_template_or_404(
                "message.html",
                title=section_info.message,
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )
    section_info = section_info.data

    if request.method == "POST":
        form_data = request.form.copy()
        del form_data["_csrf_token"]

        result_request_files = handle_request_files(
            section_info["section"]["fields"], section_info, form_data, request.files
        )
        if not result_request_files.succeeded:
            flash(result_request_files.message, "warning")
            return jsonify(
                {
                    "url_redirect": url_for(
                        "form.form_section", response_token=response_token
                    )
                }
            )

        is_back_submit = "back" in form_data

        partial_response = create_partial_response(
            db,
            tokens_info["response_id"],
            section_info["section"]["fields"],
            form_data,
            ignore_validations=is_back_submit
            and tokens_info["token_data"].get("submitted_at", None) is None,
            entry=section_info["entry_name"],
        )
        if not partial_response.succeeded:
            flash(partial_response.message, "warning")
            return jsonify(
                {
                    "url_redirect": url_for(
                        "form.form_section", response_token=response_token
                    )
                }
            )

        if "next" in form_data:
            section_info["current_pos"] += 1
            set_section(db, tokens_info["response_id"], section_info["current_pos"])
            return jsonify(
                {
                    "url_redirect": url_for(
                        "form.form_section", response_token=response_token
                    )
                }
            )
        elif is_back_submit:
            section_info["current_pos"] -= 1
            set_section(db, tokens_info["response_id"], section_info["current_pos"])
            return jsonify(
                {
                    "url_redirect": url_for(
                        "form.form_section", response_token=response_token
                    )
                }
            )

        section_info["current_pos"] += 1
        set_section(db, tokens_info["response_id"], section_info["current_pos"])

        send_to_email = False
        if (
            tokens_info["token_data"]["email"] is not None
            and "send-to-email[1]" in form_data
        ):
            send_to_email = True
        return jsonify(
            {
                "url_redirect": url_for(
                    "form.form_submit",
                    response_token=response_token,
                    send_to_email=send_to_email,
                )
            }
        )

    load_send_by_email_field(tokens_info["token_data"], section_info)

    return render_template_or_404(
        "form/index.html",
        form=section_info["section"],
        section_pos=section_info["current_pos"],
        total=len(section_info["sections"]) - 1,
        entry=section_info["entry_pos"],
        token=str(response_token),
    )


@form.route("/submit/<uuid:response_token>", methods=["GET", "POST"])
@optional_authorization()
def form_submit(user, response_token):
    token_data = get_response_info(db, str(response_token))

    if not token_data.succeeded:
        flash(ERROR(), "warning")
        return (
            render_template_or_404(
                "message.html",
                title=ERROR(),
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )

    if (
        token_data.data.get("phase") == "Approval"
        and token_data.data.get("submitted_at") is None
    ) or token_data.data.get("phase") == "Completed":
        return (
            render_template_or_404(
                "message.html",
                title=ERROR(),
                messages=[gettext("Formulário não está mais disponível para envios.")],
            ),
            400,
        )

    response_id = token_data.data["id"]
    form_id = token_data.data["form_id"]
    email = token_data.data["email"]
    send_to_email = strtobool(request.args.get("send_to_email", "false")) == 1

    sections = get_section_by_id(db, form_id)
    if not sections.succeeded:
        return abort(404)

    if len(sections.data) > token_data.data["current_section"]:
        return (
            render_template_or_404(
                "message.html",
                title=sections.message,
                messages=[
                    gettext(
                        "Verifique se a url está correta ou tente entrar em contato com o proprietário do formulário se achar que isso é um erro."
                    )
                ],
            ),
            400,
        )

    finalize_response(db, response_id)

    flash(gettext(SUBMIT_FORM()), "info")

    response = get_submissions_by_id(db, response_id)
    if email is not None and send_to_email:
        response_form = get_form_dict(db, form_id)
        send_response_to_email(db, email, response.data, response_form.data)

    return render_template_or_404(
        "message.html", title=SUBMIT_FORM(), token=str(response_token)
    )
