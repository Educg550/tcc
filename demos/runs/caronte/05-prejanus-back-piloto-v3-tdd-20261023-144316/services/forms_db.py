import uuid

from fastapi import HTTPException
from sqlalchemy import text

from database import FormsSessionLocal


def _new_token() -> str:
    return str(uuid.uuid4())


async def list_forms(year: str | None, notice: str | None) -> list[dict]:
    async with FormsSessionLocal() as session:
        sql = (
            "select id, title, created_at, tags, phase, version from form"
            " where unaccent(coalesce(title->>'pt','')) is not null"
        )
        params: dict = {}
        if year:
            sql += " and form.tags->>'Ano' = :year"
            params["year"] = year
        if notice:
            sql += " and form.tags->>'Edital' = :notice"
            params["notice"] = notice
        sql += " order by form.id desc"
        rows = await session.execute(text(sql), params)
        result = []
        for r in rows.fetchall():
            result.append(
                {
                    "id": r.id,
                    "title": r.title.get("pt", "") if r.title else "",
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "tags": r.tags or {},
                    "phase": r.phase,
                    "version": r.version,
                }
            )
        return result


async def get_sections(form_id: int, version: int | None) -> list[dict]:
    """Seleciona seções conforme a versão, com o fallback original."""
    async with FormsSessionLocal() as session:
        if version is None:
            rows = await session.execute(
                text(
                    "select id, title, description, position, version, is_active"
                    " from form_section where form_id = :fid and is_active = true"
                    " order by position, id"
                ),
                {"fid": form_id},
            )
        else:
            rows = await session.execute(
                text(
                    "select id, title, description, position, version, is_active"
                    " from form_section where form_id = :fid and"
                    " (version = :v or (:v = 1 and version is null))"
                    " order by position, id"
                ),
                {"fid": form_id, "v": version},
            )
        sections = rows.fetchall()
        if not sections:
            rows = await session.execute(
                text(
                    "select id, title, description, position, version, is_active"
                    " from form_section where form_id = :fid"
                    " order by position, id"
                ),
                {"fid": form_id},
            )
            sections = rows.fetchall()
        return [
            {
                "id": s.id,
                "title": s.title.get("pt", "") if s.title else "",
                "description": s.description.get("pt", "") if s.description else "",
                "position": s.position,
                "version": s.version,
                "is_active": s.is_active,
            }
            for s in sections
        ]


async def get_fields(section_id: int, version: int | None = None) -> list[dict]:
    async with FormsSessionLocal() as session:
        if version is None:
            rows = await session.execute(
                text(
                    "select id, form_id, section_id, label, name, description, type,"
                    " placeholder, required, disabled, validation, error_message,"
                    " prefix, position, is_active, version"
                    " from form_field where section_id = :sid and is_active = true"
                    " order by position, id"
                ),
                {"sid": section_id},
            )
        else:
            rows = await session.execute(
                text(
                    "select id, form_id, section_id, label, name, description, type,"
                    " placeholder, required, disabled, validation, error_message,"
                    " prefix, position, is_active, version"
                    " from form_field where section_id = :sid and version = :v"
                    " order by position, id"
                ),
                {"sid": section_id, "v": version},
            )
        fields = rows.fetchall()
        if version is not None and not fields:
            rows = await session.execute(
                text(
                    "select id, form_id, section_id, label, name, description, type,"
                    " placeholder, required, disabled, validation, error_message,"
                    " prefix, position, is_active, version"
                    " from form_field where section_id = :sid"
                    " order by position, id"
                ),
                {"sid": section_id},
            )
            fields = rows.fetchall()
        return [_field_dict(f) for f in fields]


def _field_dict(f) -> dict:
    return {
        "id": f.id,
        "form_id": f.form_id,
        "section_id": f.section_id,
        "label": f.label.get("pt", "") if f.label else "",
        "name": f.name,
        "description": f.description.get("pt", "") if f.description else "",
        "type": f.type,
        "placeholder": f.placeholder,
        "required": f.required,
        "disabled": f.disabled,
        "validation": f.validation,
        "error_message": f.error_message,
        "prefix": f.prefix,
        "position": f.position,
        "is_active": f.is_active,
        "version": f.version,
    }


async def get_form_full(form_id: int, version: int | None) -> list[dict]:
    sections = await get_sections(form_id, version)
    for section in sections:
        section["fields"] = await get_fields(section["id"], version)
    return sections


async def get_submitted_responses(form_id: int) -> list:
    async with FormsSessionLocal() as session:
        rows = await session.execute(
            text(
                "select id, token, submitted_at, metadata, email, form_version"
                " from form_response where form_id = :fid and submitted_at is not null"
                " order by id"
            ),
            {"fid": form_id},
        )
        return rows.fetchall()


async def get_response(response_id: int):
    async with FormsSessionLocal() as session:
        rows = await session.execute(
            text(
                "select id, form_id, shared_id, user_id, email, token,"
                " current_section, submitted_at, metadata, form_version"
                " from form_response where id = :rid"
            ),
            {"rid": response_id},
        )
        return rows.fetchone()


async def get_response_values(response_id: int) -> dict[int, str]:
    async with FormsSessionLocal() as session:
        rows = await session.execute(
            text("select field_id, value from responses where response_id = :rid"),
            {"rid": response_id},
        )
        return {r.field_id: r.value for r in rows.fetchall()}


async def change_form_phase(form_id: int, phase: str) -> None:
    async with FormsSessionLocal() as session:
        await session.execute(
            text("select * from change_form_phase(:fid, :phase::form_phase)"),
            {"fid": form_id, "phase": phase},
        )
        await session.commit()


async def reopen_response(response_id: int) -> None:
    async with FormsSessionLocal() as session:
        await session.execute(
            text("select * from update_form_response_section(:rid, 0)"),
            {"rid": response_id},
        )
        await session.execute(
            text(
                "update form_response set submitted_at = null where id = :rid"
            ),
            {"rid": response_id},
        )
        await session.commit()


async def create_accept_share(form_id: int, expiration_at) -> tuple[int, str]:
    async with FormsSessionLocal() as session:
        token = _new_token()
        rows = await session.execute(
            text(
                "insert into form_shared (form_id, unique_answers, is_public, token,"
                " created_at, expiration_at)"
                " values (:fid, true, false, :token, now(), :exp) returning id"
            ),
            {"fid": form_id, "token": token, "exp": expiration_at},
        )
        shared_id = rows.fetchone().id
        await session.commit()
        return shared_id, token


async def create_accept_response(
    form_id: int, shared_id: int, email: str, form_version: int
) -> tuple[int, str]:
    async with FormsSessionLocal() as session:
        token = _new_token()
        rows = await session.execute(
            text(
                "insert into form_response (form_id, shared_id, email, token,"
                " current_section, form_version)"
                " values (:fid, :sid, :email, :token, 0, :version) returning id"
            ),
            {
                "fid": form_id,
                "sid": shared_id,
                "email": email,
                "token": token,
                "version": form_version,
            },
        )
        response_id = rows.fetchone().id
        await session.commit()
        return response_id, token


async def get_form(form_id: int):
    async with FormsSessionLocal() as session:
        rows = await session.execute(
            text("select id, title, version, phase from form where id = :fid"),
            {"fid": form_id},
        )
        return rows.fetchone()


async def form_exists(form_id: int) -> bool:
    return await get_form(form_id) is not None
