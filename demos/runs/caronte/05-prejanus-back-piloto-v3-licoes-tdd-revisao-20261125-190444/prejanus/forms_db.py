"""Acesso ao banco do Forms (somente consultas e integrações contratadas)."""

import json
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _label_str(label) -> str:
    if isinstance(label, dict):
        return label.get("pt") or next(iter(label.values()), "") or ""
    return label or ""


async def list_forms(session: AsyncSession, year: str | None = None, notice: str | None = None):
    tags = {}
    if year:
        tags["Ano"] = year
    if notice:
        tags["Edital"] = notice
    result = await session.execute(
        text(
            "select * from get_all_user_forms(NULL, 0, 0, cast(:tags as jsonb), '', 'pt', true)"
        ),
        {"tags": json.dumps(tags) if tags else None},
    )
    rows = result.mappings().all()
    out = []
    for row in rows:
        out.append(
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "created_by": row["created_by"],
                "tags": row["tags"] or {},
                "phase": row["phase"],
            }
        )
    return out


async def get_form(session: AsyncSession, form_id: int):
    result = await session.execute(text("select * from form where id = :i"), {"i": form_id})
    return result.mappings().first()


async def get_sections(session: AsyncSession, form_id: int, version: int | None = None):
    if version is not None:
        if version == 1:
            q = text(
                "select * from form_section where form_id = :f and (version = :v or version is null)"
                " order by position, id"
            )
        else:
            q = text(
                "select * from form_section where form_id = :f and version = :v order by position, id"
            )
        rows = (await session.execute(q, {"f": form_id, "v": version})).mappings().all()
        if rows:
            return [dict(r) for r in rows]
        rows = (
            await session.execute(
                text("select * from form_section where form_id = :f order by position, id"),
                {"f": form_id},
            )
        ).mappings().all()
        return [dict(r) for r in rows]
    rows = (
        await session.execute(
            text("select * from form_section where form_id = :f and is_active = true order by position, id"),
            {"f": form_id},
        )
    ).mappings().all()
    if rows:
        return [dict(r) for r in rows]
    rows = (
        await session.execute(
            text("select * from form_section where form_id = :f order by position, id"),
            {"f": form_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_fields(session: AsyncSession, form_id: int, section_ids: list, version: int | None = None):
    if not section_ids:
        return []
    ids = ",".join(str(int(i)) for i in section_ids)
    if version is not None:
        if version == 1:
            q = text(
                f"select * from form_field where section_id in ({ids})"
                " and (version = :v or version is null) order by position, id"
            )
        else:
            q = text(
                f"select * from form_field where section_id in ({ids})"
                " and version = :v order by position, id"
            )
        rows = (await session.execute(q, {"v": version})).mappings().all()
        if rows:
            return [dict(r) for r in rows]
    rows = (
        await session.execute(
            text(f"select * from form_field where section_id in ({ids}) order by position, id")
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_all_fields(session: AsyncSession, form_id: int):
    rows = (
        await session.execute(
            text("select * from form_field where form_id = :f order by position, id"),
            {"f": form_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_fields_of_section(session: AsyncSession, section_id: int):
    rows = (
        await session.execute(
            text("select * from form_field where section_id = :s order by position, id"),
            {"s": section_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def field_dict(field: dict) -> dict:
    return {
        "id": field["id"],
        "form_id": field.get("form_id"),
        "section_id": field.get("section_id"),
        "name": field["name"],
        "label": _label_str(field.get("label")),
        "description": _label_str(field.get("description")),
        "type": field["type"],
        "placeholder": field.get("placeholder"),
        "required": field.get("required"),
        "disabled": field.get("disabled"),
        "validation": field.get("validation"),
        "error_message": field.get("error_message") or {},
        "prefix": field.get("prefix"),
        "position": field.get("position"),
        "is_active": field.get("is_active"),
        "version": field.get("version"),
    }


def section_dict(section: dict) -> dict:
    return {
        "id": section["id"],
        "form_id": section.get("form_id"),
        "title": _label_str(section.get("title")),
        "description": _label_str(section.get("description")),
        "position": section.get("position"),
        "is_active": section.get("is_active"),
        "version": section.get("version"),
    }


async def get_submissions_raw(session: AsyncSession, form_id: int):
    """Respostas finalizadas do formulário: id, token, datas, e-mail e valores por field_id."""
    result = await session.execute(
        text(
            "select fr.id, fr.token, fr.submitted_at, fr.email, fr.form_version,"
            " r.field_id, r.value"
            " from form_response fr left join responses r on r.response_id = fr.id"
            " where fr.form_id = :f and fr.submitted_at is not null order by fr.id"
        ),
        {"f": form_id},
    )
    subs: dict = {}
    for row in result.mappings():
        entry = subs.setdefault(
            row["id"],
            {
                "id": row["id"],
                "token": str(row["token"]),
                "submitted_at": row["submitted_at"],
                "email": row["email"],
                "form_version": row["form_version"] or 1,
                "values": {},
            },
        )
        if row["field_id"] is not None:
            entry["values"][row["field_id"]] = row["value"]
    return list(subs.values())


async def get_response(session: AsyncSession, response_id: int):
    result = await session.execute(
        text("select * from form_response where id = :i"), {"i": response_id}
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_response_values(session: AsyncSession, response_id: int):
    result = await session.execute(
        text(
            "select ff.name, ff.label, r.value from responses r"
            " join form_field ff on ff.id = r.field_id where r.response_id = :i"
        ),
        {"i": response_id},
    )
    return [dict(r) for r in result.mappings().all()]


async def change_form_phase(session: AsyncSession, form_id: int, phase: str):
    await session.execute(
        text("select * from change_form_phase(:i, :p)"), {"i": form_id, "p": phase}
    )
    await session.commit()


async def update_response_section(session: AsyncSession, response_id: int, current_section: int):
    await session.execute(
        text("select * from update_form_response_section(:i, :s)"),
        {"i": response_id, "s": current_section},
    )
    await session.commit()


async def create_shared(session: AsyncSession, form_id: int, expiration_at: datetime | None):
    token = str(uuid.uuid4())
    result = await session.execute(
        text(
            "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at)"
            " values (:f, true, false, :t, now(), :e) returning id, token"
        ),
        {"f": form_id, "t": token, "e": expiration_at},
    )
    row = result.mappings().first()
    await session.commit()
    return dict(row)


async def create_response(session: AsyncSession, form_id: int, shared_id: int, email: str, form_version: int):
    token = str(uuid.uuid4())
    result = await session.execute(
        text(
            "insert into form_response (form_id, shared_id, email, token, current_section, form_version)"
            " values (:f, :s, :e, :t, 0, :v) returning id, token"
        ),
        {"f": form_id, "s": shared_id, "e": email, "t": token, "v": form_version},
    )
    row = result.mappings().first()
    await session.commit()
    return dict(row)
