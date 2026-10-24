import uuid
from typing import Any

from sqlalchemy import text

from prejanus.db import forms_engine


async def fetch_all(sql: str, params: dict | None = None) -> list[dict]:
    async with forms_engine.connect() as conn:
        result = await conn.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result.fetchall()]


async def fetch_one(sql: str, params: dict | None = None) -> dict | None:
    rows = await fetch_all(sql, params)
    return rows[0] if rows else None


async def execute(sql: str, params: dict | None = None) -> None:
    async with forms_engine.begin() as conn:
        await conn.execute(text(sql), params or {})


async def execute_returning(sql: str, params: dict | None = None) -> dict | None:
    async with forms_engine.begin() as conn:
        result = await conn.execute(text(sql), params or {})
        row = result.fetchone()
        return dict(row._mapping) if row else None


def _label(label: Any) -> str:
    if isinstance(label, dict):
        value = label.get("pt")
        if value is None and label:
            value = next(iter(label.values()))
        return value or ""
    return label or ""


async def list_forms() -> list[dict]:
    rows = await fetch_all(
        "select id, title, created_at, created_by, tags, phase "
        "from get_all_user_forms(NULL, 0, 0, NULL, '', 'pt', true)"
    )
    return [
        {
            "id": r["id"],
            "title": _label(r["title"]),
            "created_at": r["created_at"],
            "created_by": r["created_by"],
            "tags": r["tags"] or {},
            "phase": r["phase"],
        }
        for r in rows
    ]


async def get_form(form_id: int) -> dict | None:
    return await fetch_one("select * from form where id = :i", {"i": form_id})


async def get_sections(form_id: int, version: int | None = None) -> list[dict]:
    if version is None:
        rows = await fetch_all(
            "select id, title, description, position from form_section "
            "where form_id = :f and is_active = true order by position",
            {"f": form_id},
        )
    else:
        rows = await fetch_all(
            "select id, title, description, position from form_section "
            "where form_id = :f and (version = :v or (:v = 1 and version is null)) "
            "order by position",
            {"f": form_id, "v": version},
        )
        if not rows:
            rows = await fetch_all(
                "select id, title, description, position from form_section "
                "where form_id = :f order by position",
                {"f": form_id},
            )
    return [
        {
            "id": r["id"],
            "title": _label(r["title"]),
            "description": _label(r["description"]),
            "position": r["position"],
        }
        for r in rows
    ]


def _field_dict(r: dict) -> dict:
    return {
        "id": r["id"],
        "name": r["name"],
        "label": _label(r["label"]),
        "description": _label(r["description"]),
        "type": r["type"],
        "placeholder": r.get("placeholder"),
        "required": r.get("required"),
        "disabled": r.get("disabled"),
        "prefix": r.get("prefix"),
        "position": r.get("position"),
        "section_id": r.get("section_id"),
    }


async def get_fields(section_id: int) -> list[dict]:
    rows = await fetch_all(
        "select * from form_field where section_id = :s and is_active = true order by position",
        {"s": section_id},
    )
    return [_field_dict(r) for r in rows]


async def get_fields_for_version(section_id: int, version: int) -> list[dict]:
    rows = await fetch_all(
        "select * from form_field where section_id = :s "
        "and (version = :v or (:v = 1 and version is null)) order by position",
        {"s": section_id, "v": version},
    )
    if not rows:
        rows = await fetch_all(
            "select * from form_field where section_id = :s order by position",
            {"s": section_id},
        )
    return [_field_dict(r) for r in rows]


async def get_response(response_id: int) -> dict | None:
    return await fetch_one(
        "select id, form_id, shared_id, email, token, current_section, submitted_at, "
        "form_version from form_response where id = :i",
        {"i": response_id},
    )


async def get_submitted_responses(form_id: int) -> list[dict]:
    return await fetch_all(
        "select id, token, submitted_at, email, form_version from form_response "
        "where form_id = :f and submitted_at is not null order by id",
        {"f": form_id},
    )


async def get_response_data(response_id: int) -> tuple[dict, list[dict]]:
    rows = await fetch_all(
        "select r.value as response_value, f.* from responses r "
        "join form_field f on f.id = r.field_id "
        "where r.response_id = :i order by f.position",
        {"i": response_id},
    )
    values = {r["id"]: r["response_value"] for r in rows}
    fields = [_field_dict(r) for r in rows]
    return values, fields


async def change_form_phase(form_id: int, phase: str) -> None:
    await execute(
        "select * from change_form_phase(:f, cast(:p as form_phase))",
        {"f": form_id, "p": phase},
    )


async def reopen_response(response_id: int) -> None:
    await execute(
        "select * from update_form_response_section(:i, 0)", {"i": response_id}
    )
    await execute(
        "update form_response set submitted_at = null where id = :i", {"i": response_id}
    )


async def create_shared(form_id: int, expiration) -> dict:
    token = str(uuid.uuid4())
    return await execute_returning(
        "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
        "values (:f, true, false, cast(:t as uuid), now(), :e) returning id, token",
        {"f": form_id, "t": token, "e": expiration},
    )


async def create_response(form_id: int, shared_id: int, email: str, version: int) -> dict:
    token = str(uuid.uuid4())
    return await execute_returning(
        "insert into form_response (form_id, shared_id, email, token, current_section, form_version) "
        "values (:f, :s, :e, :t, 0, :v) returning id, token",
        {"f": form_id, "s": shared_id, "e": email, "t": token, "v": version},
    )
