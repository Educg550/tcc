from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _pick(value) -> str:
    """Extrai texto de um campo jsonb multilíngue (pt primeiro)."""
    if not isinstance(value, dict):
        return value if isinstance(value, str) else ""
    for key in ("pt", "pt-br", "pt-BR", "en"):
        if value.get(key):
            return str(value[key])
    for v in value.values():
        if v:
            return str(v)
    return ""


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, (datetime, date)) else None


async def list_forms(s: AsyncSession, year: str | None, notice: str | None) -> list[dict]:
    rows = (
        await s.execute(
            text("SELECT id, title, description, created_at, phase, created_by, tags, version FROM form ORDER BY id")
        )
    ).mappings()
    out = []
    for r in rows:
        tags = r["tags"] if isinstance(r["tags"], dict) else {}
        if year and str(tags.get("Ano", "")) != str(year):
            continue
        if notice and str(tags.get("Edital", "")) != str(notice):
            continue
        out.append(
            {
                "id": r["id"],
                "title": _pick(r["title"]),
                "description": _pick(r["description"]),
                "created_at": _iso(r["created_at"]),
                "phase": r["phase"],
                "created_by": r["created_by"],
                "tags": tags,
                "version": r["version"],
            }
        )
    return out


async def get_form(s: AsyncSession, form_id: int) -> dict | None:
    r = (
        await s.execute(
            text(
                "SELECT id, title, description, created_at, phase, created_by, tags, version FROM form WHERE id = :f"
            ),
            {"f": form_id},
        )
    ).mappings().first()
    if not r:
        return None
    return {
        "id": r["id"],
        "title": _pick(r["title"]),
        "description": _pick(r["description"]),
        "created_at": _iso(r["created_at"]),
        "phase": r["phase"],
        "created_by": r["created_by"],
        "tags": r["tags"] if isinstance(r["tags"], dict) else {},
        "version": r["version"],
    }


async def select_sections(s: AsyncSession, form_id: int, version: int | None = None) -> list[dict]:
    if version is None:
        rows = (
            await s.execute(
                text(
                    "SELECT id, title, description, position, is_active, version FROM form_section"
                    " WHERE form_id = :f AND is_active = true ORDER BY position, id"
                ),
                {"f": form_id},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    rows = (
        await s.execute(
            text(
                "SELECT id, title, description, position, is_active, version FROM form_section"
                " WHERE form_id = :f AND (version = :v"
                + (" OR version IS NULL" if version == 1 else "")
                + ") ORDER BY position, id"
            ),
            {"f": form_id, "v": version},
        )
    ).mappings().all()
    if not rows:
        # fallback original: todas as seções do formulário
        rows = (
            await s.execute(
                text(
                    "SELECT id, title, description, position, is_active, version FROM form_section"
                    " WHERE form_id = :f ORDER BY position, id"
                ),
                {"f": form_id},
            )
        ).mappings().all()
    return [dict(r) for r in rows]


async def get_fields(
    s: AsyncSession, section_id: int, version: int | None = None, active_only: bool = False
) -> list[dict]:
    if version is not None:
        rows = (
            await s.execute(
                text(
                    "SELECT id, form_id, section_id, label, name, description, type, placeholder,"
                    " required, disabled, prefix, position, is_active, version FROM form_field"
                    " WHERE section_id = :s AND (version = :v"
                    + (" OR version IS NULL" if version == 1 else "")
                    + ") ORDER BY position, id"
                ),
                {"s": section_id, "v": version},
            )
        ).mappings().all()
        if rows:
            return [dict(r) for r in rows]
        rows = (
            await s.execute(
                text(
                    "SELECT id, form_id, section_id, label, name, description, type, placeholder,"
                    " required, disabled, prefix, position, is_active, version FROM form_field"
                    " WHERE section_id = :s ORDER BY position, id"
                ),
                {"s": section_id},
            )
        ).mappings().all()
        return [dict(r) for r in rows]

    cond = " AND is_active = true" if active_only else ""
    rows = (
        await s.execute(
            text(
                "SELECT id, form_id, section_id, label, name, description, type, placeholder,"
                " required, disabled, prefix, position, is_active, version FROM form_field"
                f" WHERE section_id = :s{cond} ORDER BY position, id"
            ),
            {"s": section_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_form_fields(s: AsyncSession, form_id: int) -> list[dict]:
    rows = (
        await s.execute(
            text(
                "SELECT id, section_id, name FROM form_field WHERE form_id = :f ORDER BY id"
            ),
            {"f": form_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_form_sections_ids(s: AsyncSession, form_id: int) -> list[int]:
    rows = await s.execute(
        text("SELECT id FROM form_section WHERE form_id = :f"), {"f": form_id}
    )
    return [r[0] for r in rows]


async def get_responses(s: AsyncSession, form_id: int) -> list[dict]:
    rows = (
        await s.execute(
            text(
                "SELECT id, token, email, form_version, submitted_at, current_section, shared_id"
                " FROM form_response WHERE form_id = :f AND submitted_at IS NOT NULL ORDER BY id"
            ),
            {"f": form_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_response(s: AsyncSession, response_id: int) -> dict | None:
    r = (
        await s.execute(
            text(
                "SELECT id, form_id, token, email, form_version, submitted_at, current_section, shared_id"
                " FROM form_response WHERE id = :r"
            ),
            {"r": response_id},
        )
    ).mappings().first()
    return dict(r) if r else None


async def get_response_details(s: AsyncSession, response_id: int) -> list[dict]:
    rows = (
        await s.execute(
            text(
                "SELECT ff.id, ff.name, ff.label, ff.type, ff.prefix, ff.position, ff.required, r.value"
                " FROM responses r JOIN form_field ff ON ff.id = r.field_id"
                " WHERE r.response_id = :rid ORDER BY ff.position, ff.id"
            ),
            {"rid": response_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_response_values(s: AsyncSession, response_id: int) -> dict[int, str]:
    rows = await s.execute(
        text("SELECT field_id, value FROM responses WHERE response_id = :rid"),
        {"rid": response_id},
    )
    return {r[0]: r[1] for r in rows}


async def change_phase(s: AsyncSession, form_id: int, phase: str) -> None:
    await s.execute(text("SELECT * FROM change_form_phase(:f, :p)"), {"f": form_id, "p": phase})
    await s.commit()


async def reopen_response(s: AsyncSession, response_id: int) -> None:
    await s.execute(
        text("SELECT * FROM update_form_response_section(:r, 0)"), {"r": response_id}
    )
    await s.commit()


async def create_accept_response(
    s: AsyncSession, form_id: int, email: str, expiration: date | None
) -> dict:
    shared_token = str(uuid.uuid4())
    resp_token = str(uuid.uuid4())
    shared = (
        await s.execute(
            text(
                "INSERT INTO form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at)"
                " VALUES (:f, true, false, :tok, now(), :exp) RETURNING id, token"
            ),
            {"f": form_id, "tok": shared_token, "exp": expiration},
        )
    ).mappings().first()
    form = await get_form(s, form_id)
    resp = (
        await s.execute(
            text(
                "INSERT INTO form_response (form_id, shared_id, email, token, current_section, form_version)"
                " VALUES (:f, :sid, :email, :tok, 0, :v) RETURNING id, token"
            ),
            {
                "f": form_id,
                "sid": shared["id"],
                "email": email,
                "tok": resp_token,
                "v": (form or {}).get("version") or 1,
            },
        )
    ).mappings().first()
    await s.commit()
    return {
        "shared_id": shared["id"],
        "shared_token": shared["token"],
        "response_id": resp["id"],
        "response_token": resp["token"],
    }
