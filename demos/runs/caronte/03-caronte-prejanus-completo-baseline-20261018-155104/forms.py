"""Access layer for the Forms database (read-mostly, plus the writes v2 needs)."""

import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from settings import settings

forms_engine = create_async_engine(settings.forms_database_url)


async def _fetch_all(query: str, **params) -> list[dict]:
    async with forms_engine.begin() as conn:
        res = await conn.execute(text(query), params)
        return [dict(r) for r in res.mappings().all()]


async def _fetch_one(query: str, **params) -> dict | None:
    async with forms_engine.begin() as conn:
        res = await conn.execute(text(query), params)
        row = res.mappings().first()
        return dict(row) if row is not None else None


async def _execute(query: str, **params) -> None:
    async with forms_engine.begin() as conn:
        await conn.execute(text(query), params)


def _pick(row: dict, *names: str, default: Any = None) -> Any:
    for n in names:
        if n in row and row[n] is not None:
            return row[n]
    return default


def _norm_tags(tags: Any) -> list[str]:
    if not tags:
        return []
    if isinstance(tags, str):
        return [t for t in (x.strip() for x in tags.split(",")) if t]
    out = []
    for t in tags:
        if isinstance(t, dict):
            out.append(str(_pick(t, "name", "label", "tag", default="")))
        else:
            out.append(str(t))
    return out


async def list_forms(year: str | None = None, notice: str | None = None) -> list[dict]:
    rows = await _fetch_all("SELECT * FROM form ORDER BY id")
    out = []
    for r in rows:
        tags = _norm_tags(_pick(r, "tags", default=[]))
        if year is not None and str(year) not in tags:
            continue
        if notice is not None and str(notice) not in tags:
            continue
        out.append(
            {
                "id": str(r["id"]),
                "title": _pick(r, "title", "name", default=""),
                "tags": tags,
                "phase": _pick(r, "phase", "status", default=""),
            }
        )
    return out


async def get_form_row(form_id: str) -> dict | None:
    return await _fetch_one("SELECT * FROM form WHERE id = :f", f=form_id)


async def get_sections(form_id: str, version: int | None = None) -> list[dict]:
    rows = await _fetch_all(
        "SELECT * FROM section WHERE form_id = :f ORDER BY position", f=form_id
    )

    def active(row: dict) -> bool:
        return str(_pick(row, "active", "is_active", default=True)).lower() not in (
            "false",
            "0",
            "no",
        )

    if version is not None:
        selected = [
            r
            for r in rows
            if _pick(r, "version") == version
            or (version == 1 and _pick(r, "version") is None)
        ]
    else:
        selected = [r for r in rows if active(r)]
    if not selected:
        selected = rows  # original fallback: every section of the form, by position
    return [
        {
            "id": str(r["id"]),
            "name": _pick(r, "name", "label", "title", default=""),
            "position": _pick(r, "position", default=0),
            "version": _pick(r, "version"),
            "active": active(r),
        }
        for r in selected
    ]


async def get_fields(section_id: str) -> list[dict]:
    rows = await _fetch_all(
        "SELECT * FROM field WHERE section_id = :s ORDER BY position", s=section_id
    )
    return [
        {
            "id": str(r["id"]),
            "name": _pick(r, "name", default=""),
            "label": _pick(r, "label", "name", default=""),
            "type": _pick(r, "type", "field_type", default=""),
            "position": _pick(r, "position", default=0),
            "prefix": _pick(r, "prefix", default=""),
        }
        for r in rows
    ]


async def get_form(form_id: str, version: int | None = None) -> dict:
    row = await get_form_row(form_id)
    if row is None:
        return {}
    sections = await get_sections(form_id, version)
    return {
        "id": str(row["id"]),
        "title": _pick(row, "title", "name", default=""),
        "tags": _norm_tags(_pick(row, "tags", default=[])),
        "phase": _pick(row, "phase", "status", default=""),
        "sections": [
            {**s, "fields": await get_fields(s["id"])} for s in sections
        ],
    }


async def get_responses(form_id: str) -> list[dict]:
    rows = await _fetch_all(
        "SELECT * FROM response WHERE form_id = :f ORDER BY id", f=form_id
    )
    out = []
    for r in rows:
        finished = _pick(r, "finished", default=None)
        status = str(_pick(r, "status", default="")).lower()
        is_finished = (
            bool(finished)
            if finished is not None
            else status in ("completed", "finished", "finalized")
        )
        out.append(
            {
                "id": str(r["id"]),
                "form_id": str(r["form_id"]),
                "version": _pick(r, "version", default=1),
                "email": _pick(r, "email", default=""),
                "finished": is_finished,
                "created_at": _pick(r, "created_at", "date", default=None),
                "updated_at": _pick(r, "updated_at", default=None),
                "share_token": _pick(r, "share_token", "token", default=None),
            }
        )
    return out


def _norm_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _pick(value, "filename", "name", "value", default="")
    if isinstance(value, list):
        return [_norm_value(v) for v in value]
    return value


async def get_answers(response_id: str) -> dict[str, Any]:
    """Return {field_id: value} for a response."""
    rows = await _fetch_all(
        "SELECT * FROM answer WHERE response_id = :r", r=response_id
    )
    return {
        str(r["field_id"]): _norm_value(_pick(r, "value", "answer", default=""))
        for r in rows
    }


async def set_form_phase(form_id: str, phase: str) -> None:
    await _execute("UPDATE form SET phase = :p WHERE id = :f", p=phase, f=form_id)


async def reopen_response(response_id: str) -> None:
    await _execute(
        "UPDATE response SET current_section = 0, status = 'in_progress',"
        " finished = false WHERE id = :r",
        r=response_id,
    )


async def get_response_token(response_id: str) -> str | None:
    row = await _fetch_one(
        "SELECT * FROM response WHERE id = :r", r=response_id
    )
    if row is None:
        return None
    return _pick(row, "share_token", "token", default=None)


async def create_share(
    form_id: str, email: str, expiration: datetime | None
) -> str:
    token = secrets.token_urlsafe(24)
    await _execute(
        "INSERT INTO share (form_id, email, token, expiration, single_response,"
        " private) VALUES (:f, :e, :t, :x, true, true)",
        f=form_id,
        e=email,
        t=token,
        x=expiration,
    )
    return token


async def create_response(
    form_id: str, email: str, version: int, share_token: str
) -> str:
    row = await _fetch_one(
        "INSERT INTO response (form_id, version, email, share_token, status)"
        " VALUES (:f, :v, :e, :t, 'in_progress') RETURNING id",
        f=form_id,
        v=version,
        e=email,
        t=share_token,
    )
    return str(row["id"])
