from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_forms(db: AsyncSession, year=None, notice=None):
    query = "select id, title, description, created_at, phase, tags, version from form where true"
    params = {}
    if year is not None:
        query += " and tags ->> 'Ano' = :year"
        params["year"] = str(year)
    if notice is not None:
        query += " and tags ->> 'Edital' = :notice"
        params["notice"] = str(notice)
    query += " order by id"
    rows = await db.execute(text(query), params)
    forms = []
    for row in rows:
        data = dict(row._mapping)
        title = data.get("title") or {}
        data["title"] = title.get("pt") or title.get("en") or ""
        forms.append(data)
    return forms


async def get_form(db: AsyncSession, form_id: int):
    row = await db.execute(
        text("select id, title, description, created_at, phase, tags, version from form where id = :fid"),
        {"fid": form_id},
    )
    row = row.first()
    if not row:
        return None
    data = dict(row._mapping)
    title = data.get("title") or {}
    data["title"] = title.get("pt") or title.get("en") or ""
    return data


async def select_sections(db: AsyncSession, form_id: int, version=None):
    """Seções do formulário para a versão pedida, com o fallback original."""
    if version is None:
        rows = await db.execute(
            text(
                "select id, form_id, title, description, position, is_active, version "
                "from form_section where form_id = :fid and is_active = true order by position, id"
            ),
            {"fid": form_id},
        )
        return [dict(r._mapping) for r in rows]

    if version == 1:
        rows = await db.execute(
            text(
                "select id, form_id, title, description, position, is_active, version "
                "from form_section where form_id = :fid and (version = 1 or version is null) "
                "order by position, id"
            ),
            {"fid": form_id},
        )
    else:
        rows = await db.execute(
            text(
                "select id, form_id, title, description, position, is_active, version "
                "from form_section where form_id = :fid and version = :v "
                "order by position, id"
            ),
            {"fid": form_id, "v": version},
        )
    sections = [dict(r._mapping) for r in rows]
    if not sections:
        rows = await db.execute(
            text(
                "select id, form_id, title, description, position, is_active, version "
                "from form_section where form_id = :fid order by position, id"
            ),
            {"fid": form_id},
        )
        sections = [dict(r._mapping) for r in rows]
    return sections


async def select_fields(db: AsyncSession, section_id: int, version=None):
    """Campos da seção para a versão, com fallback para os campos existentes."""
    base = (
        "select id, form_id, section_id, label, name, description, type, placeholder, "
        "required, disabled, prefix, position, is_active, version from form_field "
        "where section_id = :sid"
    )
    if version is None:
        query = base + " and is_active = true order by position, id"
        rows = await db.execute(text(query), {"sid": section_id})
        return [_field_dict(r) for r in rows]

    if version == 1:
        query = base + " and is_active = true and (version = 1 or version is null) order by position, id"
        rows = await db.execute(text(query), {"sid": section_id})
    else:
        query = base + " and is_active = true and version = :v order by position, id"
        rows = await db.execute(text(query), {"sid": section_id, "v": version})
    fields = [_field_dict(r) for r in rows]
    if not fields:
        rows = await db.execute(
            text(base + " order by position, id"), {"sid": section_id}
        )
        fields = [_field_dict(r) for r in rows]
    return fields


def _field_dict(row):
    data = dict(row._mapping)
    label = data.get("label") or {}
    data["label"] = label.get("pt") or label.get("en") or ""
    return data


async def get_form_responses(db: AsyncSession, form_id: int, submitted_only=True):
    """Respostas do formulário: {response_id: metadados + valores por field_id}."""
    query = (
        "select fr.id, fr.token, fr.submitted_at, fr.metadata, fr.email, fr.form_version, "
        "fr.shared_id, fr.current_section, r.field_id, r.value "
        "from form_response fr left join responses r on r.response_id = fr.id "
        "where fr.form_id = :fid"
    )
    if submitted_only:
        query += " and fr.submitted_at is not null"
    rows = await db.execute(text(query), {"fid": form_id})
    result = {}
    for row in rows:
        data = dict(row._mapping)
        entry = result.setdefault(
            data["id"],
            {
                "id": data["id"],
                "token": str(data["token"]) if data["token"] else None,
                "submitted_at": data["submitted_at"],
                "metadata": data["metadata"],
                "email": data["email"],
                "form_version": data["form_version"],
                "shared_id": data["shared_id"],
                "current_section": data["current_section"],
                "values": {},
            },
        )
        if data["field_id"] is not None:
            entry["values"][data["field_id"]] = data["value"]
    return result


async def get_response(db: AsyncSession, response_id: int):
    row = await db.execute(
        text(
            "select id, token, submitted_at, metadata, email, form_version, shared_id, "
            "current_section from form_response where id = :rid"
        ),
        {"rid": response_id},
    )
    row = row.first()
    if not row:
        return None
    data = dict(row._mapping)
    values = {}
    value_rows = await db.execute(
        text("select field_id, value from responses where response_id = :rid"),
        {"rid": response_id},
    )
    for value_row in value_rows:
        values[value_row[0]] = value_row[1]
    data["values"] = values
    return data


async def change_form_phase(db: AsyncSession, form_id: int, phase: str):
    await db.execute(
        text("select * from change_form_phase(:fid, cast(:phase as form_phase))"),
        {"fid": form_id, "phase": phase},
    )
    await db.commit()


async def reopen_response(db: AsyncSession, response_id: int):
    await db.execute(
        text("select * from update_form_response_section(:rid, 0)"), {"rid": response_id}
    )
    await db.execute(
        text("update form_response set submitted_at = null where id = :rid"),
        {"rid": response_id},
    )
    await db.commit()


async def create_shared_response(
    db: AsyncSession, form_id: int, email: str, expiration_at, form_version: int
):
    """Cria compartilhamento privado de resposta única e resposta vinculada."""
    shared_token = str(uuid4())
    row = await db.execute(
        text(
            "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
            "values (:fid, true, false, :token, now(), :exp) returning id, token"
        ),
        {"fid": form_id, "token": shared_token, "exp": expiration_at},
    )
    shared = row.first()
    response_token = str(uuid4())
    row = await db.execute(
        text(
            "insert into form_response (form_id, shared_id, email, token, current_section, form_version) "
            "values (:fid, :sid, :email, :token, 0, :v) returning id, token"
        ),
        {"fid": form_id, "sid": shared.id, "email": email, "token": response_token, "v": form_version},
    )
    response = row.first()
    await db.commit()
    return {
        "shared_id": shared.id,
        "shared_token": str(shared.token),
        "response_id": response.id,
        "response_token": str(response.token),
    }
