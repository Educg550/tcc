import uuid
from datetime import datetime

from sqlalchemy import text

from database import FormsSession


def _t(json_value, lang="pt"):
    if not json_value:
        return ""
    if isinstance(json_value, str):
        return json_value
    value = json_value.get(lang)
    if value is None:
        for candidate in json_value.values():
            if candidate:
                value = candidate
                break
    return value or ""


def list_forms(year=None, notice=None):
    query = "select * from form where true"
    params = {}
    if year:
        query += " and tags ->> 'Ano' = :year"
        params["year"] = str(year)
    if notice:
        query += " and tags ->> 'Edital' = :notice"
        params["notice"] = str(notice)
    query += " order by id"
    with FormsSession() as s:
        rows = s.execute(text(query), params).mappings().all()
    return [form_json(r) for r in rows]


def form_json(row):
    return {
        "id": row["id"],
        "title": _t(row["title"]),
        "description": _t(row["description"]),
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "created_by": row["created_by"],
        "tags": row["tags"] or {},
        "phase": row["phase"],
        "version": row["version"],
    }


def get_form(form_id):
    with FormsSession() as s:
        row = s.execute(text("select * from form where id = :i"), {"i": form_id}).mappings().first()
        return form_json(row) if row else None


def select_sections(form_id, version=None):
    """Sections of a form for a version; falls back to every section of the form."""
    with FormsSession() as s:
        if version is None:
            rows = s.execute(
                text("select * from form_section where form_id = :f and is_active order by position, id"),
                {"f": form_id},
            ).mappings().all()
        else:
            rows = s.execute(
                text(
                    "select * from form_section where form_id = :f"
                    " and (version = :v or (:v = 1 and version is null))"
                    " order by position, id"
                ),
                {"f": form_id, "v": version},
            ).mappings().all()
            if not rows:
                rows = s.execute(
                    text(
                        "select * from form_section where form_id = :f and is_active"
                        " order by position, id"
                    ),
                    {"f": form_id},
                ).mappings().all()
    return [dict(r) for r in rows]


def section_json(sec):
    return {
        "id": sec["id"],
        "title": _t(sec["title"]),
        "description": _t(sec["description"]),
        "position": sec["position"],
        "is_active": sec["is_active"],
        "version": sec["version"],
    }


def get_fields(section_id):
    with FormsSession() as s:
        rows = s.execute(
            text("select * from form_field where section_id = :s order by position, id"),
            {"s": section_id},
        ).mappings().all()
    return [dict(r) for r in rows]


def field_json(f):
    return {
        "id": f["id"],
        "name": f["name"],
        "label": _t(f["label"]),
        "description": _t(f["description"]),
        "type": f["type"],
        "placeholder": f["placeholder"],
        "required": f["required"],
        "disabled": f["disabled"],
        "prefix": f["prefix"],
        "position": f["position"],
        "is_active": f["is_active"],
        "version": f["version"],
    }


def get_response(response_id):
    with FormsSession() as s:
        row = s.execute(
            text("select * from form_response where id = :i"), {"i": response_id}
        ).mappings().first()
        return dict(row) if row else None


def get_response_values(response_id):
    with FormsSession() as s:
        rows = s.execute(
            text(
                "select r.field_id, r.value, ff.name, ff.type, ff.section_id"
                " from responses r join form_field ff on ff.id = r.field_id"
                " where r.response_id = :i"
            ),
            {"i": response_id},
        ).mappings().all()
    return [dict(r) for r in rows]


def get_submitted_responses(form_id):
    with FormsSession() as s:
        rows = s.execute(
            text("select * from form_response where form_id = :f and submitted_at is not null order by id"),
            {"f": form_id},
        ).mappings().all()
    return [dict(r) for r in rows]


def set_form_phase(form_id, phase):
    with FormsSession() as s:
        s.execute(
            text("select * from change_form_phase(cast(:f as integer), cast(:p as form_phase))"),
            {"f": form_id, "p": phase},
        )
        s.commit()


def reopen_response(response_id):
    with FormsSession() as s:
        s.execute(
            text("select * from update_form_response_section(cast(:i as integer), 0)"),
            {"i": response_id},
        )
        s.commit()


def create_accept_form(form_id, email, expiration_at):
    """Creates a private single-answer share and its linked response in Forms."""
    token = str(uuid.uuid4())
    with FormsSession() as s:
        shared_id = s.execute(
            text(
                "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at)"
                " values (:f, true, false, cast(:t as uuid), :c, :e) returning id"
            ),
            {"f": form_id, "t": token, "c": datetime.now(), "e": expiration_at},
        ).scalar_one()
        response_id = s.execute(
            text(
                "insert into form_response (form_id, shared_id, email, token, current_section, form_version)"
                " values (:f, :s, :e, cast(:t as uuid), 0, 1) returning id"
            ),
            {"f": form_id, "s": shared_id, "e": email, "t": str(uuid.uuid4())},
        ).scalar_one()
        s.commit()
    return shared_id, response_id, token
