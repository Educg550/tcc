import json

from sqlalchemy import text

from db import FormsSession


async def list_forms(year: str | None = None, notice: str | None = None) -> list[dict]:
    tags: dict = {}
    if year:
        tags["Ano"] = year
    if notice:
        tags["Edital"] = notice
    async with FormsSession() as db:
        rows = (
            await db.execute(
                text(
                    "select * from get_all_user_forms(NULL, 0, 0, cast(:tags as jsonb), '', 'pt', true)"
                ),
                {"tags": json.dumps(tags)},
            )
        ).mappings().all()
    seen = set()
    out = []
    for r in rows:
        d = dict(r)
        if d["id"] in seen:
            continue
        seen.add(d["id"])
        out.append(d)
    return out


async def get_form(form_id: int) -> dict | None:
    async with FormsSession() as db:
        row = (
            await db.execute(
                text(
                    "select id, title, description, created_at, phase, tags, metadata, version "
                    "from form where id = :i"
                ),
                {"i": form_id},
            )
        ).mappings().first()
    return dict(row) if row else None


async def get_sections(form_id: int, version: int | None = None) -> list[dict]:
    async with FormsSession() as db:
        if version is not None:
            if version == 1:
                rows = (
                    await db.execute(
                        text(
                            "select id, form_id, title, description, position, is_active, version "
                            "from form_section where form_id = :f and (version = 1 or version is null) "
                            "order by position"
                        ),
                        {"f": form_id},
                    )
                ).mappings().all()
            else:
                rows = (
                    await db.execute(
                        text(
                            "select id, form_id, title, description, position, is_active, version "
                            "from form_section where form_id = :f and version = :v order by position"
                        ),
                        {"f": form_id, "v": version},
                    )
                ).mappings().all()
            if not rows:
                rows = await _all_sections(db, form_id)
        else:
            rows = (
                await db.execute(
                    text(
                        "select id, form_id, title, description, position, is_active, version "
                        "from form_section where form_id = :f and is_active = true order by position"
                    ),
                    {"f": form_id},
                )
            ).mappings().all()
            if not rows:
                rows = await _all_sections(db, form_id)
    return [dict(r) for r in rows]


async def _all_sections(db, form_id: int) -> list:
    return (
        await db.execute(
            text(
                "select id, form_id, title, description, position, is_active, version "
                "from form_section where form_id = :f order by position"
            ),
            {"f": form_id},
        )
    ).mappings().all()


async def get_section_fields(section_id: int) -> list[dict]:
    async with FormsSession() as db:
        rows = (
            await db.execute(
                text(
                    "select id, form_id, section_id, label, name, description, type, placeholder, "
                    "required, disabled, validation, error_message, prefix, position, is_active, version "
                    "from form_field where section_id = :s order by position"
                ),
                {"s": section_id},
            )
        ).mappings().all()
    return [dict(r) for r in rows]


async def get_form_fields(form_id: int, version: int | None = None) -> list[dict]:
    """Fields of a form, optionally filtered by version (with fallback to all)."""
    async with FormsSession() as db:
        if version is not None:
            if version == 1:
                rows = (
                    await db.execute(
                        text(
                            "select * from form_field where form_id = :f "
                            "and (version = 1 or version is null) order by position"
                        ),
                        {"f": form_id},
                    )
                ).mappings().all()
            else:
                rows = (
                    await db.execute(
                        text(
                            "select * from form_field where form_id = :f and version = :v order by position"
                        ),
                        {"f": form_id, "v": version},
                    )
                ).mappings().all()
            if not rows:
                rows = (
                    await db.execute(
                        text("select * from form_field where form_id = :f order by position"),
                        {"f": form_id},
                    )
                ).mappings().all()
        else:
            rows = (
                await db.execute(
                    text(
                        "select * from form_field where form_id = :f and is_active = true order by position"
                    ),
                    {"f": form_id},
                )
            ).mappings().all()
    return [dict(r) for r in rows]


async def get_responses(response_id: int) -> dict[int, str]:
    """Map field_id -> value for a form response."""
    async with FormsSession() as db:
        rows = await db.execute(
            text("select field_id, value from responses where response_id = :r"),
            {"r": response_id},
        )
    return {r.field_id: (r.value or "") for r in rows}


async def get_response_row(response_id: int) -> dict | None:
    async with FormsSession() as db:
        row = (
            await db.execute(
                text(
                    "select id, form_id, shared_id, user_id, email, token, current_section, "
                    "submitted_at, metadata, form_version from form_response where id = :i"
                ),
                {"i": response_id},
            )
        ).mappings().first()
    return dict(row) if row else None


async def get_all_form_responses(form_id: int) -> list[dict]:
    async with FormsSession() as db:
        rows = (
            await db.execute(
                text(
                    "select id, form_id, shared_id, user_id, email, token, current_section, "
                    "submitted_at, metadata, form_version from form_response "
                    "where form_id = :f and submitted_at is not null order by id"
                ),
                {"f": form_id},
            )
        ).mappings().all()
    return [dict(r) for r in rows]


async def change_form_phase(form_id: int, phase: str) -> None:
    async with FormsSession() as db:
        await db.execute(
            text("select * from change_form_phase(:i, cast(:p as form_phase))"),
            {"i": form_id, "p": phase},
        )
        await db.commit()


async def reopen_response(response_id: int) -> None:
    async with FormsSession() as db:
        await db.execute(
            text("select * from update_form_response_section(:i, 0)"), {"i": response_id}
        )
        await db.execute(
            text("update form_response set submitted_at = null where id = :i"),
            {"i": response_id},
        )
        await db.commit()


async def create_shared(form_id: int, expiration_at) -> tuple[int, str]:
    import uuid

    async with FormsSession() as db:
        row = (
            await db.execute(
                text(
                    "insert into form_shared (form_id, unique_answers, is_public, token, created_at, "
                    "expiration_at) values (:f, true, false, :t, now(), :e) returning id, token"
                ),
                {"f": form_id, "t": str(uuid.uuid4()), "e": expiration_at},
            )
        ).first()
        await db.commit()
    return row.id, str(row.token)


async def create_response(form_id: int, shared_id: int, email: str, form_version: int) -> tuple[int, str]:
    import uuid

    async with FormsSession() as db:
        row = (
            await db.execute(
                text(
                    "insert into form_response (form_id, shared_id, email, token, current_section, "
                    "form_version) values (:f, :s, :e, :t, 0, :v) returning id, token"
                ),
                {"f": form_id, "s": shared_id, "e": email, "t": str(uuid.uuid4()), "v": form_version},
            )
        ).first()
        await db.commit()
    return row.id, str(row.token)
