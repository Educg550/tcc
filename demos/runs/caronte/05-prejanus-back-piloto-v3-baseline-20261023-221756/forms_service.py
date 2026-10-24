import json
import uuid

from sqlalchemy import text

from db import FormsSession


def _label(label_json, lang="pt"):
    if not isinstance(label_json, dict):
        return label_json or ""
    return label_json.get(lang) or label_json.get("pt") or next(iter(label_json.values()), "")


async def list_forms(year: str | None, notice: str | None):
    tag_filter = {}
    if year:
        tag_filter["Ano"] = year
    if notice:
        tag_filter["Edital"] = notice
    async with FormsSession() as s:
        rows = (
            await s.execute(
                text("select * from get_all_user_forms(:user_id, :order_by, :order_type, "
                     ":tags, :search, :lang, :is_admin)"),
                {"user_id": None, "order_by": 0, "order_type": 0,
                 "tags": json.dumps(tag_filter) if tag_filter else None,
                 "search": "", "lang": "pt", "is_admin": True},
            )
        ).mappings().all()
    return [
        {"id": r["id"], "title": r["title"], "created_at": r["created_at"],
         "created_by": r["created_by"], "tags": r["tags"], "phase": r["phase"]}
        for r in rows
    ]


async def get_sections(form_id: int, version: int | None = None):
    """Sections of a form for a version (with the original fallback), or active ones."""
    async with FormsSession() as s:
        if version is None:
            rows = (await s.execute(
                text("select * from form_section where form_id = :f and is_active = true order by \"position\", id"),
                {"f": form_id})).mappings().all()
        else:
            rows = (await s.execute(
                text("select * from form_section where form_id = :f and is_active = true "
                     "and (version = :v or (:v = 1 and version is null)) order by \"position\", id"),
                {"f": form_id, "v": version})).mappings().all()
            if not rows:
                rows = (await s.execute(
                    text("select * from form_section where form_id = :f order by \"position\", id"),
                    {"f": form_id})).mappings().all()
    return [dict(r) for r in rows]


async def get_fields(section_id: int, version: int | None = None):
    async with FormsSession() as s:
        if version is None:
            rows = (await s.execute(
                text("select * from form_field where section_id = :s and is_active = true order by \"position\", id"),
                {"s": section_id})).mappings().all()
        else:
            rows = (await s.execute(
                text("select * from form_field where section_id = :s and is_active = true "
                     "and (version = :v or (:v = 1 and version is null)) order by \"position\", id"),
                {"s": section_id, "v": version})).mappings().all()
            if not rows:
                rows = (await s.execute(
                    text("select * from form_field where section_id = :s order by \"position\", id"),
                    {"s": section_id})).mappings().all()
    return [dict(r) for r in rows]


async def get_form_full(form_id: int, version: int | None = None):
    sections = await get_sections(form_id, version)
    for sec in sections:
        fields = await get_fields(sec["id"], version)
        sec["fields"] = [
            {"id": f["id"], "name": f["name"], "label": _label(f["label"]), "type": f["type"],
             "prefix": f["prefix"], "position": f["position"], "required": f["required"],
             "placeholder": f["placeholder"], "description": _label(f["description"]),
             "is_active": f["is_active"], "version": f["version"]}
            for f in fields
        ]
        sec["title"] = _label(sec["title"])
        sec["description"] = _label(sec["description"])
    return {"id": form_id, "sections": sections}


async def get_section_fields(form_id: int, section_id: int):
    fields = await get_fields(section_id)
    return [
        {"id": f["id"], "name": f["name"], "label": _label(f["label"]), "type": f["type"],
         "prefix": f["prefix"], "position": f["position"], "required": f["required"],
         "placeholder": f["placeholder"], "description": _label(f["description"]),
         "disabled": f["disabled"], "validation": f["validation"], "version": f["version"]}
        for f in fields
    ]


async def get_form_fields(form_id: int, version: int | None = None):
    async with FormsSession() as s:
        if version is None:
            rows = (await s.execute(
                text("select * from form_field where form_id = :f and is_active = true order by \"position\", id"),
                {"f": form_id})).mappings().all()
        else:
            rows = (await s.execute(
                text("select * from form_field where form_id = :f and is_active = true "
                     "and (version = :v or (:v = 1 and version is null)) order by \"position\", id"),
                {"f": form_id, "v": version})).mappings().all()
            if not rows:
                rows = (await s.execute(
                    text("select * from form_field where form_id = :f order by \"position\", id"),
                    {"f": form_id})).mappings().all()
    return [dict(r) for r in rows]


async def get_submitted_responses(form_id: int):
    async with FormsSession() as s:
        rows = (await s.execute(
            text("select id, token, email, form_version, submitted_at, metadata, current_section "
                 "from form_response where form_id = :f and submitted_at is not null order by id"),
            {"f": form_id})).mappings().all()
    return [dict(r) for r in rows]


async def get_response_values(response_id: int):
    """Map field_id -> raw value for a response."""
    async with FormsSession() as s:
        rows = (await s.execute(
            text("select field_id, value from responses where response_id = :r"),
            {"r": response_id})).all()
    return {r[0]: r[1] for r in rows}


async def get_response(response_id: int):
    async with FormsSession() as s:
        row = (await s.execute(
            text("select id, form_id, shared_id, email, token, current_section, submitted_at, "
                 "metadata, form_version from form_response where id = :r"),
            {"r": response_id})).mappings().first()
    return dict(row) if row else None


async def change_form_phase(form_id: int, phase: str):
    async with FormsSession() as s:
        await s.execute(text("select * from change_form_phase(:f, :p)"), {"f": form_id, "p": phase})
        await s.commit()


async def reopen_response(response_id: int):
    """Reopen a candidate response for correction (current section zero)."""
    async with FormsSession() as s:
        await s.execute(text("select * from update_form_response_section(:r, 0)"), {"r": response_id})
        await s.execute(text("update form_response set submitted_at = null where id = :r"), {"r": response_id})
        await s.commit()


async def create_accept_share(form_id: int, email: str, expiration):
    """Create a private single-answer share and its linked response; return (shared_id, response_id, token)."""
    token = str(uuid.uuid4())
    async with FormsSession() as s:
        shared_id = (await s.execute(
            text("insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
                 "values (:f, true, false, :t, now(), :e) returning id"),
            {"f": form_id, "t": token, "e": expiration})).scalar()
        resp_token = str(uuid.uuid4())
        version = (await s.execute(text("select version from form where id = :f"), {"f": form_id})).scalar()
        response_id = (await s.execute(
            text("insert into form_response (form_id, shared_id, email, token, current_section, form_version) "
                 "values (:f, :s, :e, :t, 0, :v) returning id"),
            {"f": form_id, "s": shared_id, "e": email, "t": resp_token, "v": version or 1})).scalar()
        await s.commit()
    return shared_id, response_id, token


async def count_in_progress(form_id: int) -> int:
    async with FormsSession() as s:
        return (await s.execute(
            text("select count(*) from form_response where form_id = :f and submitted_at is null"),
            {"f": form_id})).scalar()
