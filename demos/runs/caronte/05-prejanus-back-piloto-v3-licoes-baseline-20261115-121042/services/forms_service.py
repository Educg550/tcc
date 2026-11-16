import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_forms(db: AsyncSession, year: str | None, notice: str | None) -> list[dict]:
    query = "select id, title, description, created_at, phase, tags, version from form where true"
    params: dict = {}
    if year:
        query += " and tags ->> 'Ano' ilike :year"
        params["year"] = f"%{year}%"
    if notice:
        query += " and tags ->> 'Edital' ilike :notice"
        params["notice"] = f"%{notice}%"
    query += " order by id"
    result = await db.execute(text(query), params)
    rows = [dict(r) for r in result.mappings()]
    for row in rows:
        row["title"] = (row.get("title") or {}).get("pt") or (row.get("title") or {}).get("en")
        row["description"] = (row.get("description") or {}).get("pt")
    return rows


async def get_form(db: AsyncSession, form_id: int) -> dict | None:
    result = await db.execute(
        text("select id, title, description, created_at, phase, tags, version from form where id = :id"),
        {"id": form_id},
    )
    row = result.mappings().first()
    if row is None:
        return None
    data = dict(row)
    data["title"] = (data.get("title") or {}).get("pt") or (data.get("title") or {}).get("en")
    return data


async def select_sections(db: AsyncSession, form_id: int, version: int | None) -> list[dict]:
    if version is None:
        result = await db.execute(
            text(
                "select id, title, description, position, is_active, version from form_section "
                "where form_id = :fid and is_active = true order by position, id"
            ),
            {"fid": form_id},
        )
    else:
        if version == 1:
            result = await db.execute(
                text(
                    "select id, title, description, position, is_active, version from form_section "
                    "where form_id = :fid and (version = 1 or version is null) order by position, id"
                ),
                {"fid": form_id},
            )
        else:
            result = await db.execute(
                text(
                    "select id, title, description, position, is_active, version from form_section "
                    "where form_id = :fid and version = :v order by position, id"
                ),
                {"fid": form_id, "v": version},
            )
    rows = [dict(r) for r in result.mappings()]
    if not rows:
        result = await db.execute(
            text(
                "select id, title, description, position, is_active, version from form_section "
                "where form_id = :fid order by position, id"
            ),
            {"fid": form_id},
        )
        rows = [dict(r) for r in result.mappings()]
    for row in rows:
        row["title"] = (row.get("title") or {}).get("pt") or (row.get("title") or {}).get("en")
        row["description"] = (row.get("description") or {}).get("pt")
    return rows


async def select_fields(db: AsyncSession, section_id: int, version: int | None) -> list[dict]:
    if version is None:
        result = await db.execute(
            text(
                "select id, form_id, section_id, label, name, description, type, placeholder, "
                'required, disabled, validation, prefix, position, is_active, version '
                "from form_field where section_id = :sid and is_active = true order by position, id"
            ),
            {"sid": section_id},
        )
    else:
        if version == 1:
            result = await db.execute(
                text(
                    "select id, form_id, section_id, label, name, description, type, placeholder, "
                    'required, disabled, validation, prefix, position, is_active, version '
                    "from form_field where section_id = :sid and (version = 1 or version is null) "
                    "order by position, id"
                ),
                {"sid": section_id},
            )
        else:
            result = await db.execute(
                text(
                    "select id, form_id, section_id, label, name, description, type, placeholder, "
                    'required, disabled, validation, prefix, position, is_active, version '
                    "from form_field where section_id = :sid and version = :v order by position, id"
                ),
                {"sid": section_id, "v": version},
            )
    rows = [dict(r) for r in result.mappings()]
    if not rows:
        result = await db.execute(
            text(
                "select id, form_id, section_id, label, name, description, type, placeholder, "
                'required, disabled, validation, prefix, position, is_active, version '
                "from form_field where section_id = :sid order by position, id"
            ),
            {"sid": section_id},
        )
        rows = [dict(r) for r in result.mappings()]
    for row in rows:
        row["label"] = (row.get("label") or {}).get("pt") or (row.get("label") or {}).get("en")
        row["description"] = (row.get("description") or {}).get("pt")
    return rows


async def get_submitted_responses(db: AsyncSession, form_id: int) -> list[dict]:
    result = await db.execute(
        text(
            "select id, token, submitted_at, metadata, email, form_version, shared_id "
            "from form_response where form_id = :fid and submitted_at is not null order by id"
        ),
        {"fid": form_id},
    )
    return [dict(r) for r in result.mappings()]


async def get_response(db: AsyncSession, response_id: int) -> dict | None:
    result = await db.execute(
        text(
            "select id, form_id, shared_id, user_id, email, token, current_section, "
            "submitted_at, metadata, form_version from form_response where id = :rid"
        ),
        {"rid": response_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_response_values(db: AsyncSession, response_id: int) -> dict[int, str]:
    result = await db.execute(
        text("select field_id, value from responses where response_id = :rid"),
        {"rid": response_id},
    )
    return {r.field_id: r.value for r in result.mappings()}


async def change_form_phase(db: AsyncSession, form_id: int, phase: str) -> None:
    await db.execute(
        text("select * from change_form_phase(:fid, :phase::form_phase)"),
        {"fid": form_id, "phase": phase},
    )
    await db.commit()


async def reopen_response(db: AsyncSession, response_id: int) -> None:
    await db.execute(
        text("select * from update_form_response_section(:rid, 0)"), {"rid": response_id}
    )
    await db.execute(
        text("update form_response set submitted_at = null where id = :rid"), {"rid": response_id}
    )
    await db.commit()


async def create_shared(db: AsyncSession, form_id: int, expiration_at) -> dict:
    token = str(uuid.uuid4())
    result = await db.execute(
        text(
            "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
            "values (:fid, true, false, :token, :now, :exp) returning id, token"
        ),
        {"fid": form_id, "token": token, "now": datetime.now(), "exp": expiration_at},
    )
    row = result.mappings().first()
    await db.commit()
    return dict(row)


async def create_response(
    db: AsyncSession, form_id: int, shared_id: int, email: str, form_version: int
) -> dict:
    token = str(uuid.uuid4())
    result = await db.execute(
        text(
            "insert into form_response (form_id, shared_id, email, token, current_section, form_version) "
            "values (:fid, :sid, :email, :token, 0, :version) returning id, token"
        ),
        {"fid": form_id, "sid": shared_id, "email": email, "token": token, "version": form_version},
    )
    row = result.mappings().first()
    await db.commit()
    return dict(row)
