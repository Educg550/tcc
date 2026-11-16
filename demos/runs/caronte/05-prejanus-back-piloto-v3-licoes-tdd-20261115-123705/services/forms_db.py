"""Acesso ao banco do Forms: leitura de estrutura/respostas e escritas
exigidas pelas integrações (fase do formulário, reabertura e aceite)."""

import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

FORM_PHASE_BY_EDICT_PHASE = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


def _title(value) -> str:
    if isinstance(value, dict):
        return value.get("pt") or value.get("en") or ""
    return value or ""


async def list_forms(db: AsyncSession, year: str | None = None, notice: str | None = None):
    result = await db.execute(
        text(
            "select id, title, description, created_at, phase, tags, version "
            "from form order by id"
        )
    )
    rows = result.mappings().all()
    out = []
    for row in rows:
        tags = row["tags"] or {}
        if year and str(year).lower() not in str(tags.get("Ano", "")).lower():
            continue
        if notice and str(notice).lower() not in str(tags.get("Edital", "")).lower():
            continue
        out.append(
            {
                "id": row["id"],
                "title": _title(row["title"]),
                "description": _title(row["description"]),
                "created_at": row["created_at"],
                "phase": row["phase"],
                "tags": tags,
                "version": row["version"],
            }
        )
    return out


async def get_form(db: AsyncSession, form_id: int):
    result = await db.execute(
        text(
            "select id, title, description, created_at, phase, tags, version "
            "from form where id = :id"
        ),
        {"id": form_id},
    )
    row = result.mappings().first()
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": _title(row["title"]),
        "description": _title(row["description"]),
        "created_at": row["created_at"],
        "phase": row["phase"],
        "tags": row["tags"] or {},
        "version": row["version"],
    }


async def get_sections(db: AsyncSession, form_id: int, version: int | None = None):
    """Seções do formulário. Com version, seleciona essa versão (versão 1
    aceita também seções com versão nula); sem o parâmetro, as ativas.
    Sem resultados, fallback para todas as seções por posição."""
    if version is not None:
        if version == 1:
            query = (
                "select * from form_section where form_id = :fid "
                "and (version = 1 or version is null) order by position"
            )
            result = await db.execute(text(query), {"fid": form_id})
        else:
            query = (
                "select * from form_section where form_id = :fid "
                "and version = :ver order by position"
            )
            result = await db.execute(text(query), {"fid": form_id, "ver": version})
        rows = result.mappings().all()
        if not rows:
            result = await db.execute(
                text(
                    "select * from form_section where form_id = :fid order by position"
                ),
                {"fid": form_id},
            )
            rows = result.mappings().all()
    else:
        result = await db.execute(
            text(
                "select * from form_section where form_id = :fid "
                "and is_active = true order by position"
            ),
            {"fid": form_id},
        )
        rows = result.mappings().all()
        if not rows:
            result = await db.execute(
                text(
                    "select * from form_section where form_id = :fid order by position"
                ),
                {"fid": form_id},
            )
            rows = result.mappings().all()
    return [dict(row) for row in rows]


def section_dict(row) -> dict:
    return {
        "id": row["id"],
        "form_id": row["form_id"],
        "title": _title(row["title"]),
        "description": _title(row["description"]),
        "position": row["position"],
        "is_active": row["is_active"],
        "version": row["version"],
    }


def field_dict(row) -> dict:
    return {
        "id": row["id"],
        "form_id": row["form_id"],
        "section_id": row["section_id"],
        "label": _title(row["label"]),
        "name": row["name"],
        "description": _title(row["description"]),
        "type": row["type"],
        "placeholder": row["placeholder"],
        "required": row["required"],
        "disabled": row["disabled"],
        "validation": row["validation"],
        "error_message": _title(row["error_message"]),
        "prefix": row["prefix"],
        "position": row["position"],
        "is_active": row["is_active"],
        "version": row["version"],
    }


async def get_fields(db: AsyncSession, form_id: int, section_id: int):
    result = await db.execute(
        text(
            "select * from form_field where form_id = :fid and section_id = :sid "
            "order by position, id"
        ),
        {"fid": form_id, "sid": section_id},
    )
    return [field_dict(row) for row in result.mappings().all()]


async def get_all_fields(db: AsyncSession, form_id: int):
    result = await db.execute(
        text("select * from form_field where form_id = :fid order by position, id"),
        {"fid": form_id},
    )
    return [field_dict(row) for row in result.mappings().all()]


async def get_submitted_responses(db: AsyncSession, form_id: int):
    result = await db.execute(
        text(
            "select id, token, submitted_at, metadata, email, form_version, "
            "current_section, shared_id from form_response "
            "where form_id = :fid and submitted_at is not null order by id"
        ),
        {"fid": form_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_response(db: AsyncSession, response_id: int):
    result = await db.execute(
        text(
            "select id, form_id, shared_id, email, token, current_section, "
            "submitted_at, metadata, form_version from form_response "
            "where id = :rid"
        ),
        {"rid": response_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_values(db: AsyncSession, response_id: int) -> dict[int, str]:
    result = await db.execute(
        text("select field_id, value from responses where response_id = :rid"),
        {"rid": response_id},
    )
    return {row["field_id"]: row["value"] for row in result.mappings().all()}


async def change_form_phase(db: AsyncSession, form_id: int, phase: str):
    await db.execute(
        text("select * from change_form_phase(:id, :phase)"), {"id": form_id, "phase": phase}
    )
    await db.commit()


async def reopen_response(db: AsyncSession, response_id: int):
    await db.execute(
        text("select * from update_form_response_section(:id, 0)"), {"id": response_id}
    )
    await db.commit()


async def create_shared(
    db: AsyncSession, form_id: int, expiration_at
) -> dict:
    token = str(uuid.uuid4())
    result = await db.execute(
        text(
            "insert into form_shared (form_id, unique_answers, is_public, token, "
            "created_at, expiration_at) values (:fid, true, false, :token, :now, :exp) "
            "returning id, token"
        ),
        {"fid": form_id, "token": token, "now": datetime.now(), "exp": expiration_at},
    )
    row = result.mappings().first()
    await db.commit()
    return dict(row)


async def create_response(
    db: AsyncSession, form_id: int, shared_id: int, email: str
) -> dict:
    token = str(uuid.uuid4())
    result = await db.execute(
        text(
            "insert into form_response (form_id, shared_id, email, token, "
            "current_section, form_version) values (:fid, :sid, :email, :token, 0, 1) "
            "returning id, token"
        ),
        {"fid": form_id, "sid": shared_id, "email": email, "token": token},
    )
    row = result.mappings().first()
    await db.commit()
    return dict(row)
