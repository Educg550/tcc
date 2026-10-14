import json
import locale
import re
from datetime import datetime, date
from app.common import get_values
from app.entities.Field import Field
from app.entities.User import UserType
from app.exceptions.error_messages import (
    ERROR,
    INVALID_FIELDS,
    CREATED_FORM,
    ERROR_CREATE_FORM,
    ERROR_REQUIRED_FIELDS,
)
from app.extension import get_locale
from app.common.Result import Result
from flask_babel import format_date, gettext

from typing import List
from app.repositories.form_repository import get_form_dict_raw, get_viewer_form_dict_raw
from app.services.email_service import Email
from app.entities.Form import FormPhaseEnum, FormType, Form
from app.services.response_service import get_response_info
from app.services.token_service import get_shared_token_info

from app.config import load_config
from app.entities.Options import Options
from app.entities.Section import Section


def get_form_dict(db, form_id, lang: str = None) -> Result:
    if lang is None:
        lang = get_locale()
    res = get_form_dict_raw(db, form_id, lang)
    return Result(res)


def get_viewer_form_dict(db, form_id, lang=None):
    if lang is None:
        lang = get_locale()

    res = get_viewer_form_dict_raw(db, form_id, lang)
    return Result(res)


def get_available_forms(db, lang: str = None) -> Result:
    if lang is None:
        lang = get_locale()
    sql_string = """
        select
            form.id,
            coalesce(form.title ->> %s, form.title ->> 'pt') as title,
            form_shared.expiration_at,
            form_shared.unique_answers,
            form_shared.token,
            form_shared.created_at
        from form_shared
            inner join form
            on form_shared.form_id = form.id
        where 
            form_shared.expiration_at >= %s and
            form.phase = 'Registration'::form_phase and
            form_shared.is_public = True
    """

    res = []
    with db.transaction() as f:
        today = date.today()
        res = f.sql_dict(
            sql_string,
            (
                lang,
                today,
            ),
            callback=lambda x: x.fetchall(),
        )

    return Result(res)


def change_form_phase(db, form_id: int, user: UserType, phase: FormPhaseEnum) -> Result:

    sql_string = """
        select * from change_form_phase(
            %s, %s
        )
    """
    params = (
        form_id,
        phase,
    )

    with db.transaction() as f:
        return f.sql_dict(sql_string, params, callback=lambda x: x.fetchone())


def get_all_user_forms(
    db,
    user: UserType,
    order_by: int,
    order_type: int,
    tag_filter,
    search: str = "",
    lang: str = None,
) -> Result:
    if lang is None:
        lang = get_locale()

    sql_string = """
        select * from get_all_user_forms(
            %s, %s, %s, %s, %s, %s, %s
        )
    """

    params = (
        user.get("id"),
        order_by,
        order_type,
        json.dumps(tag_filter),
        search,
        lang,
        False,
    )

    res = []
    with db.transaction() as f:
        res = f.sql_dict(sql_string, params, callback=lambda x: x.fetchall())

    return Result[List[FormType]](res)


def get_tags(db, request_args) -> Result:
    "**admin command**"

    sql_string = """
        select 
            array_agg(distinct(key)) as tags
        from
            form,
            jsonb_object_keys(tags) as key;
    """

    with db.transaction() as f:
        row = f.sql_dict(sql_string, (), callback=lambda x: x.fetchone())

    all_tags = row.get("tags") if row else None
    tag_filter = {}

    if not all_tags:
        return Result(tag_filter)

    for tag in all_tags:
        tag_filter[tag] = request_args.get(tag, "", type=str).strip()

    return Result(tag_filter)


def get_all_submissions_dict(
    db, form_id: int, order_by, order_type, search="", lang: str = None
) -> Result:

    if lang is None:
        lang = get_locale()

    sql_string = """
        select * from get_all_submissions(
            p_form_id := %s,
            p_order_by := %s,
            p_order_type := %s,
            p_search := %s,
            p_lang := %s
        )
    """
    params = (
        form_id,
        order_by,
        order_type,
        search,
        lang,
    )

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, params, callback=lambda x: x.fetchall())

    return Result(res)


def get_submissions_by_id(db, id) -> Result:
    """
    Não tem verificações de que a `response` pertence ao dono
    - Única verificação é o `response_id`

    Usar **somente** se o `token` já ter sido validado
    """

    sql_string = """
        select
            form_response.id,
            form_response.submitted_at,
            form_response.metadata,
            users.email,
            json_agg(
                json_build_object(
                    form_field.name, responses.value
                )
            ) as responses
        from form_response
            left join users
                on form_response.user_id = users.id
            inner join responses
                on form_response.id = responses.response_id
            inner join form_field
                on responses.field_id = form_field.id
        where 
            form_response.id = %s
        group by form_response.id, users.id;
    """

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (id,), callback=lambda x: x.fetchone())

    return Result(res)


def load_send_by_email_field(token_data, section_info):
    if (
        token_data["email"] is not None
        and len(section_info["sections"]) - 1 == section_info["current_pos"]
    ):
        position = section_info["section"]["fields"][-1]["position"] + 1
        section_info["section"]["fields"].append(
            Field(
                {
                    "name": "send-to-email",
                    "type": "CheckBox",
                    "required": False,
                    "options": [
                        gettext(
                            "Enviar uma cópia das minhas respostas para meu e-mail."
                        )
                    ],
                    "position": position,
                }
            )
        )
        section_info["entry_pos"][f"{position}_1"] = True


def handle_tokens(db, response_token):
    # pega response
    token_data = get_response_info(db, str(response_token))

    if not token_data.succeeded:
        return Result(message=ERROR())

    response_id = token_data.data["id"]
    form_id = token_data.data["form_id"]
    current = token_data.data["current_section"]

    # verifica se o formulario ainda e valido
    shared_token_data = get_shared_token_info(
        db, shared_id=token_data.data["shared_id"]
    )
    if not shared_token_data.succeeded:
        return Result(message=shared_token_data.message)

    return Result(
        {
            "response_id": response_id,
            "form_id": form_id,
            "current_pos": current,
            "token_data": token_data.data,
        }
    )


class FormValidationError(Exception):
    def __init__(self, message):
        self.message = message


def _insert_sections(f, form_id, sections, version=1, is_active=True):
    """Insere sections/fields/options. Lança FormValidationError em caso de dado inválido."""
    pattern = re.compile(r"[\[|\]]+")
    position_section = 0

    for section in sections:
        insert = get_values(Section, section)
        insert["form_id"] = form_id
        insert["position"] = position_section
        insert["version"] = version
        insert["is_active"] = is_active

        sql_string = f"""
            insert into form_section({",".join(insert.keys())})
                values({",".join(["%s" for _ in range(len(insert))])}) returning id;
        """
        section_id = f.sql(
            sql_string, tuple(insert.values()), callback=lambda x: x.fetchone()
        )[0]

        position_field = 0
        for field in section["fields"]:
            if "type" not in field:
                raise FormValidationError('Propriedade "type" é requerida.')

            if "name" not in field:
                if "label" not in field:
                    raise FormValidationError(
                        'Propriedade "label" ou "name" é requerida.'
                    )
                field["name"] = field["label"].lower().replace(" ", "-")

            if field["type"] == "CheckBox" and "options" not in field:
                continue

            if pattern.match(field["name"]):
                raise FormValidationError(INVALID_FIELDS())

            insert = get_values(Field, field)
            insert["form_id"] = form_id
            insert["section_id"] = section_id
            insert["position"] = position_field
            insert["version"] = version
            insert["is_active"] = is_active

            sql_string = f"""
                insert into form_field({",".join(insert.keys())})
                    values({",".join(["%s" for _ in range(len(insert))])}) returning id;
            """
            field_id = f.sql(
                sql_string, tuple(insert.values()), callback=lambda x: x.fetchone()
            )[0]

            if field["type"] in ("CheckBox", "Radio", "Text") and "options" in field:
                for option in field["options"]:
                    insert = get_values(Options, option)
                    insert["field_id"] = field_id
                    sql_string = f"""
                        insert into field_option({",".join(insert.keys())})
                            values({",".join(["%s" for _ in range(len(insert))])}) returning id;
                    """
                    f.sql(
                        sql_string,
                        tuple(insert.values()),
                        callback=lambda x: x.fetchone(),
                    )

            position_field += 1
        position_section += 1


def create_form(db, form: FormType) -> Result:
    if "sections" not in form or not len(form["sections"]) > 0:
        return Result(message=ERROR_REQUIRED_FIELDS("sections")).handler_error(
            message=ERROR_REQUIRED_FIELDS("sections")
        )

    form["version"] = form.get("version") or 1
    insert = get_values(Form, form)
    sql_string = f"""
        insert into form({",".join(insert.keys())})
            values({",".join(["%s" for _ in range(len(insert))])}) returning id;
    """

    try:
        with db.transaction() as f:
            form_id = f.sql(
                sql_string, tuple(insert.values()), callback=lambda x: x.fetchone()
            )[0]
            _insert_sections(f, form_id, form["sections"], version=form["version"], is_active=True)
    except FormValidationError as e:
        return Result(message=ERROR_CREATE_FORM()).handler_error(message=e.message)

    return Result(form_id, message=CREATED_FORM())


def update_form_by_id(db, form_id, form: FormType) -> Result:
    if "sections" not in form or not len(form["sections"]) > 0:
        return Result(message=ERROR_REQUIRED_FIELDS("sections")).handler_error(
            message=ERROR_REQUIRED_FIELDS("sections")
        )

    try:
        with db.transaction() as f:
            # Verifica se já existem submissões
            sub_count = f.sql(
                "select count(*) from form_response where form_id = %s;",
                (form_id,),
                callback=lambda x: x.fetchone()[0] if x else 0,
            )

            # Busca versão atual do form
            current_form = f.sql_dict(
                "select version from form where id = %s;",
                (form_id,),
                callback=lambda x: x.fetchone(),
            )
            if not current_form:
                raise FormValidationError(ERROR())

            current_version = current_form.get("version") or 1

            if sub_count and sub_count > 0:
                # Com submissões existentes: arquiva seções e campos anteriores e incrementa versão
                new_version = current_version + 1
                form["version"] = new_version
                update = get_values(Form, form)
                if update:
                    set_clause = ",".join([f"{k} = %s" for k in update.keys()])
                    sql_string = f"""
                        update form set {set_clause}
                            where id = %s
                        returning id;
                    """
                    res = f.sql(
                        sql_string,
                        tuple(update.values()) + (form_id,),
                        callback=lambda x: x.fetchone(),
                    )
                    if not res:
                        raise FormValidationError(ERROR())

                # Desativa seções e campos ativos anteriores (preserva dados para consultas históricas)
                f.sql(
                    "update form_section set is_active = false where form_id = %s and is_active = true;",
                    (form_id,),
                )
                f.sql(
                    "update form_field set is_active = false where form_id = %s and is_active = true;",
                    (form_id,),
                )

                _insert_sections(f, form_id, form["sections"], version=new_version, is_active=True)
            else:
                # Sem submissões: atualização direta sem versionamento
                form["version"] = current_version
                update = get_values(Form, form)
                if update:
                    set_clause = ",".join([f"{k} = %s" for k in update.keys()])
                    sql_string = f"""
                        update form set {set_clause}
                            where id = %s
                        returning id;
                    """
                    res = f.sql(
                        sql_string,
                        tuple(update.values()) + (form_id,),
                        callback=lambda x: x.fetchone(),
                    )
                    if not res:
                        raise FormValidationError(ERROR())

                f.sql("delete from form_field where form_id = %s;", (form_id,))
                f.sql("delete from form_section where form_id = %s;", (form_id,))

                _insert_sections(f, form_id, form["sections"], version=current_version, is_active=True)
    except FormValidationError as e:
        return Result(message=ERROR_CREATE_FORM()).handler_error(message=e.message)

    return Result(form_id, message=CREATED_FORM())  # TODO: trocar por UPDATED_FORM


def update_metadata_submission(db, response_id, metadata):
    "**admin command**"

    sql_string = """
        update 
            form_response set metadata = %s 
            where id = %s
        returning id;
    """

    res = None
    with db.transaction() as f:
        res = f.sql_dict(
            sql_string, (metadata, response_id), callback=lambda x: x.fetchone()
        )

    return Result(res)


def remove_form_by_id(db, form_id):
    sql_string = """
        delete 
            from form 
            where id = %s
        returning id;
    """

    res = None
    with db.transaction() as f:
        res = f.sql_dict(sql_string, (form_id,), callback=lambda x: x.fetchone())

    return Result(res)


# TODO: implementar melhor
# TODO: traduzir mensagem do email
def template_email_link(form_title, url, deadline):
    return {"html": f"""
<p>O acesso ao formulário <strong>"{ form_title }"</strong> foi autorizado.</p>

<p>
    Para iniciar o preenchimento, utilize o link abaixo:<br>
    <a href="{ url }" target="_blank">Acessar formulário</a>
</p>

<p>Este formulário estará disponível até <strong>{ deadline.strftime('%d %B %Y') }</strong>.</p>

<hr>

<p><strong>Informações importantes:</strong></p>
<ul>
    <li>O formulário pode conter múltiplas seções ou páginas;</li>
    <li>O progresso é salvo automaticamente durante a troca de sessões;</li>
    <li>O link pode aceitar apenas uma resposta (dependendo da configuração).</li>
</ul>

<p>Caso não reconheça a origem desta mensagem, por gentileza, desconsidere o conteúdo.</p>
"""}


def send_url_to_email(db, to_addrs, form_title, url, deadline):
    config = load_config()
    email = Email(config)

    locale.setlocale(locale.LC_ALL, "")
    email.send_queue(
        {
            "to_addrs": [to_addrs],
            "subject": f"Acesso ao formulário: {form_title}",
            "body": template_email_link(form_title, url, deadline),
        },
        priority=0,
    )


# TODO: traduzir mensagem do email
def template_email_response(response, form):
    html_return = ""

    for field in form["fields"]:
        r = [
            {"value": response_field, "field": field}
            for response_field in response["responses"]
            if field["name"] == next(iter(response_field.items()))[0]
        ]

        value = "—"
        if len(r):
            r = r[0]
            field_type = r["field"].get("type", "Text")
            field_prefix = r["field"].get("prefix", None)
            value = next(iter(r["value"].items()))[1]
            if value == "":
                value = "—"
            try:
                if field_type == "CheckBox":
                    value = ", ".join(json.loads(value))
                elif field_type == "Date":
                    value = format_date(
                        datetime.strptime(value, "%Y-%m-%d"), format="medium"
                    )
                elif field_type == "File":
                    splited_value = value.split("_")
                    splited_value.pop(0)
                    value = "_".join(splited_value)
            except Exception as _:
                value = ""

            if field_prefix:
                value = field_prefix + value
        html_return += f"""
<div style="font-family: sans-serif; padding: 24px; border-radius: 32px; border: 1px solid rgba(0, 0, 0, 0.05); background: #fff; box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.06); max-width: 450px; margin: 0 auto">
  <p><strong>{ field["label"] }</strong></p>
  <p style="border-bottom: 1px solid #37352f; padding: 6px">{ value }</p>
</div>
<br>
"""
    return {"html": f"""
<div style="font-family: sans-serif; padding: 24px; border-radius: 32px; border: 1px solid rgba(0, 0, 0, 0.05); background: #fff; box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.06); max-width: 450px; margin: 0 auto">
  <p><strong>Este formulário é uma cópia da sua inscrição para o: { form["title"] }</strong></p>
</div>
<br>
<div style="font-family: sans-serif; padding: 24px; border-radius: 32px; border: 1px solid rgba(0, 0, 0, 0.05); background: #fff; box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.06); max-width: 450px; margin: 0 auto">
  <p><strong>{ form["title"] }</strong></p>
</div>
<br>
{html_return}
<div style="font-family: sans-serif; margin: 0 auto; text-align: center">
  <p>{response["submitted_at"]}</p>
  <br>
  <p>Caso não reconheça a origem desta mensagem, por gentileza, desconsidere o conteúdo.</p>
</div>
<br>
"""}


def send_response_to_email(db, to_addrs, response, form):
    config = load_config()
    email = Email(config)

    locale.setlocale(locale.LC_ALL, "")
    email.send_queue(
        {
            "to_addrs": [to_addrs],
            "subject": f"Cópia da sua inscrição para o { form['title'] }",
            "body": template_email_response(response, form),
        },
        priority=1,
    )
