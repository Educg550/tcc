from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _label(row: dict) -> str:
    label = row.get("label") or {}
    if isinstance(label, dict):
        return label.get("pt") or label.get("en") or ""
    return str(label or "")


def _title(row: dict) -> str:
    title = row.get("title") or {}
    if isinstance(title, dict):
        return title.get("pt") or title.get("en") or ""
    return str(title or "")


async def list_forms(fdb: AsyncSession, tag_filter: dict | None = None) -> list[dict]:
    sql = text(
        "select * from get_all_user_forms("
        "NULL, 0, 0, cast(:tag_filter as jsonb), '', 'pt', true)"
    )
    res = await fdb.execute(sql, {"tag_filter": _to_json(tag_filter)})
    rows = [dict(r._mapping) for r in res.fetchall()]
    out = []
    for r in rows:
        tags = r.get("tags") or {}
        if not isinstance(tags, dict):
            tags = {}
        out.append(
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"],
                "created_by": r["created_by"],
                "tags": tags,
                "phase": r["phase"],
            }
        )
    return out


def _to_json(value) -> str:
    import json

    if value is None:
        return "{}"
    if isinstance(value, str):
        return value
    return json.dumps(value)


async def get_form(fdb: AsyncSession, form_id: int) -> dict | None:
    res = await fdb.execute(text("select * from form where id = :id"), {"id": form_id})
    row = res.fetchone()
    if row is None:
        return None
    r = dict(row._mapping)
    return {
        "id": r["id"],
        "title": _title(r),
        "description": r.get("description") or {},
        "created_at": r.get("created_at"),
        "phase": r.get("phase"),
        "created_by": r.get("created_by"),
        "tags": r.get("tags") or {},
        "metadata": r.get("metadata") or {},
        "version": r.get("version", 1),
    }


async def get_sections(
    fdb: AsyncSession, form_id: int, version: int | None = None
) -> list[dict]:
    if version is None:
        sql = text(
            "select * from form_section where form_id = :fid and is_active = true "
            "order by \"position\", id"
        )
        res = await fdb.execute(sql, {"fid": form_id})
    else:
        sql = text(
            "select * from form_section where form_id = :fid "
            "and (version = :v or (:v = 1 and version is null)) "
            "order by \"position\", id"
        )
        res = await fdb.execute(sql, {"fid": form_id, "v": version})
    rows = [dict(r._mapping) for r in res.fetchall()]
    if not rows:
        res = await fdb.execute(
            text(
                "select * from form_section where form_id = :fid "
                "order by \"position\", id"
            ),
            {"fid": form_id},
        )
        rows = [dict(r._mapping) for r in res.fetchall()]
    return [_section_dict(r) for r in rows]


def _section_dict(r: dict) -> dict:
    return {
        "id": r["id"],
        "form_id": r.get("form_id"),
        "title": _title(r),
        "description": r.get("description") or {},
        "position": r.get("position", 0),
        "is_active": r.get("is_active", True),
        "version": r.get("version", 1),
    }


async def get_fields(
    fdb: AsyncSession, section_id: int, version: int | None = None
) -> list[dict]:
    if version is None:
        sql = text(
            "select * from form_field where section_id = :sid and is_active = true "
            "order by \"position\", id"
        )
        res = await fdb.execute(sql, {"sid": section_id})
    else:
        sql = text(
            "select * from form_field where section_id = :sid "
            "and (version = :v or (:v = 1 and version is null)) "
            "order by \"position\", id"
        )
        res = await fdb.execute(sql, {"sid": section_id, "v": version})
    rows = [dict(r._mapping) for r in res.fetchall()]
    if not rows:
        res = await fdb.execute(
            text(
                "select * from form_field where section_id = :sid "
                "order by \"position\", id"
            ),
            {"sid": section_id},
        )
        rows = [dict(r._mapping) for r in res.fetchall()]
    return [_field_dict(r) for r in rows]


def _field_dict(r: dict) -> dict:
    return {
        "id": r["id"],
        "form_id": r.get("form_id"),
        "section_id": r.get("section_id"),
        "label": _label(r),
        "name": r.get("name"),
        "description": r.get("description") or {},
        "type": r.get("type"),
        "placeholder": r.get("placeholder"),
        "required": r.get("required", False),
        "disabled": r.get("disabled", False),
        "prefix": r.get("prefix"),
        "position": r.get("position", 0),
        "is_active": r.get("is_active", True),
        "version": r.get("version", 1),
    }


async def get_form_responses(fdb: AsyncSession, form_id: int) -> list[dict]:
    res = await fdb.execute(
        text(
            "select id, form_id, shared_id, user_id, email, token, current_section, "
            "submitted_at, metadata, form_version from form_response "
            "where form_id = :fid and submitted_at is not null order by id"
        ),
        {"fid": form_id},
    )
    return [dict(r._mapping) for r in res.fetchall()]


async def get_response(fdb: AsyncSession, response_id: int) -> dict | None:
    res = await fdb.execute(
        text(
            "select id, form_id, shared_id, user_id, email, token, current_section, "
            "submitted_at, metadata, form_version from form_response "
            "where id = :rid"
        ),
        {"rid": response_id},
    )
    row = res.fetchone()
    return dict(row._mapping) if row else None


async def get_response_data(fdb: AsyncSession, response_id: int) -> dict:
    """Valores e metadados dos campos respondidos: {values, fields}."""
    res = await fdb.execute(
        text(
            "select r.field_id, r.value, f.id as fid, f.name, f.label, f.type, "
            "f.prefix, f.section_id, f.\"position\" "
            "from responses r join form_field f on f.id = r.field_id "
            "where r.response_id = :rid order by f.\"position\", f.id"
        ),
        {"rid": response_id},
    )
    values: dict[int, str] = {}
    fields: dict[int, dict] = {}
    for row in res.fetchall():
        r = dict(row._mapping)
        fid = r["fid"]
        values[fid] = r["value"]
        fields[fid] = {
            "id": fid,
            "name": r["name"],
            "label": _label({"label": r["label"]}),
            "type": r["type"],
            "prefix": r["prefix"],
            "section_id": r["section_id"],
            "position": r["position"],
        }
    return {"values": values, "fields": fields}


async def change_form_phase(fdb: AsyncSession, form_id: int, phase: str) -> None:
    await fdb.execute(
        text("select * from change_form_phase(:fid, cast(:ph as form_phase))"),
        {"fid": form_id, "ph": phase},
    )
    await fdb.commit()


async def reopen_response(fdb: AsyncSession, response_id: int) -> None:
    """Reabre a resposta para correção: seção atual volta a zero."""
    await fdb.execute(
        text("select * from update_form_response_section(:rid, 0)"), {"rid": response_id}
    )
    await fdb.commit()


async def create_shared_response(
    fdb: AsyncSession,
    form_id: int,
    email: str,
    expiration_at: datetime | None,
    form_version: int = 1,
) -> dict:
    import uuid

    shared_token = str(uuid.uuid4())
    res = await fdb.execute(
        text(
            "insert into form_shared (form_id, unique_answers, is_public, token, "
            "created_at, expiration_at) values (:fid, true, false, :token, now(), "
            ":exp) returning id, token"
        ),
        {"fid": form_id, "token": shared_token, "exp": expiration_at},
    )
    shared = dict(res.fetchone()._mapping)
    resp_token = str(uuid.uuid4())
    res = await fdb.execute(
        text(
            "insert into form_response (form_id, shared_id, email, token, "
            "current_section, form_version) values (:fid, :sid, :email, :token, 0, "
            ":fv) returning id, token"
        ),
        {
            "fid": form_id,
            "sid": shared["id"],
            "email": email,
            "token": resp_token,
            "fv": form_version,
        },
    )
    resp = dict(res.fetchone()._mapping)
    await fdb.commit()
    return {"shared_id": shared["id"], "response_id": resp["id"], "token": resp["token"]}
