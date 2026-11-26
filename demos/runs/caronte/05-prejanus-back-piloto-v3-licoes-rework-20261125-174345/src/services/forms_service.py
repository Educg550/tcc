import uuid

from ..db import fetch, fetch_one, forms_engine, run


async def list_forms(year: str | None = None, notice: str | None = None) -> list[dict]:
    rows = await fetch(
        forms_engine,
        "SELECT id, title, description, created_at, phase::text AS phase, created_by, tags, "
        "metadata, version FROM form ORDER BY id",
    )
    out = []
    for row in rows:
        tags = row["tags"] or {}
        if year is not None and tags.get("Ano") != year:
            continue
        if notice is not None and tags.get("Edital") != notice:
            continue
        out.append({
            "id": row["id"],
            "title": (row["title"] or {}).get("pt", ""),
            "description": (row["description"] or {}).get("pt", ""),
            "created_at": row["created_at"],
            "phase": row["phase"],
            "created_by": row["created_by"],
            "tags": tags,
            "metadata": row["metadata"] or {},
            "version": row["version"],
        })
    return out


async def get_form(form_id: int) -> dict | None:
    return await fetch_one(forms_engine, "SELECT * FROM form WHERE id=:i", {"i": form_id})


async def form_sections(form_id: int, version: int | None = None) -> list[dict]:
    if version is not None:
        rows = await fetch(
            forms_engine,
            "SELECT id, form_id, title, description, position, is_active, version "
            "FROM form_section WHERE form_id=:f AND version=:v ORDER BY position, id",
            {"f": form_id, "v": version},
        )
        if rows:
            return rows
        return await fetch(
            forms_engine,
            "SELECT id, form_id, title, description, position, is_active, version "
            "FROM form_section WHERE form_id=:f ORDER BY position, id",
            {"f": form_id},
        )
    return await fetch(
        forms_engine,
        "SELECT id, form_id, title, description, position, is_active, version "
        "FROM form_section WHERE form_id=:f AND is_active ORDER BY position, id",
        {"f": form_id},
    )


async def section_fields(section_id: int) -> list[dict]:
    return await fetch(
        forms_engine,
        "SELECT id, form_id, section_id, label, name, description, type::text AS type, "
        "placeholder, required, disabled, validation, error_message, prefix, position, "
        "is_active, version FROM form_field WHERE section_id=:s ORDER BY position, id",
        {"s": section_id},
    )


async def form_versions(form_id: int) -> list[int]:
    rows = await fetch(
        forms_engine,
        "SELECT DISTINCT version FROM form_section WHERE form_id=:f "
        "UNION SELECT DISTINCT version FROM form_field WHERE form_id=:f",
        {"f": form_id},
    )
    return sorted({r["version"] for r in rows})


async def get_response(response_id: int) -> dict | None:
    return await fetch_one(
        forms_engine,
        "SELECT id, form_id, shared_id, user_id, email, token, current_section, submitted_at, "
        "metadata, form_version FROM form_response WHERE id=:i",
        {"i": response_id},
    )


async def response_values(response_id: int) -> dict[int, str]:
    rows = await fetch(
        forms_engine, "SELECT field_id, value FROM responses WHERE response_id=:i", {"i": response_id}
    )
    return {r["field_id"]: r["value"] for r in rows}


async def submitted_responses(form_id: int) -> list[dict]:
    return await fetch(
        forms_engine,
        "SELECT id, form_id, email, token, form_version FROM form_response "
        "WHERE form_id=:f AND submitted_at IS NOT NULL ORDER BY id",
        {"f": form_id},
    )


async def set_form_phase(form_id: int, phase: str) -> None:
    await run(
        forms_engine,
        "SELECT id, phase::text AS phase FROM change_form_phase(:f, CAST(:p AS form_phase))",
        {"f": form_id, "p": phase},
    )


async def reset_response_section(response_id: int) -> None:
    await run(
        forms_engine,
        "SELECT id, current_section FROM update_form_response_section(:i, 0)",
        {"i": response_id},
    )


async def create_accept_response(form_id: int, email: str, expiration, version: int) -> dict:
    shared_token = uuid.uuid4()
    rows = await run(
        forms_engine,
        "INSERT INTO form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at) "
        "VALUES (:f, true, false, :t, now(), :e) RETURNING id",
        {"f": form_id, "t": shared_token, "e": expiration},
    )
    token = uuid.uuid4()
    resp = await run(
        forms_engine,
        "INSERT INTO form_response (form_id, shared_id, email, token, current_section, submitted_at, "
        "metadata, form_version) VALUES (:f, :s, :e, :t, 0, NULL, '{}'::jsonb, :v) RETURNING id, token",
        {"f": form_id, "s": rows[0]["id"], "e": email, "t": token, "v": version},
    )
    return resp[0]
