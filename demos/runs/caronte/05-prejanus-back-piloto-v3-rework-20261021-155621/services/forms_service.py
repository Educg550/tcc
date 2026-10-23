"""Acesso ao banco Forms e aos mapeamentos de edital."""
from sqlalchemy import text


def _title(jsonb) -> str:
    if not jsonb:
        return ""
    if isinstance(jsonb, str):
        return jsonb
    for key in ("pt", "en"):
        if jsonb.get(key):
            return jsonb[key]
    for value in jsonb.values():
        if value:
            return value
    return ""


async def list_forms(fsession) -> list[dict]:
    rows = (
        await fsession.execute(
            text("SELECT id, title, description, tags, phase::text AS phase FROM form ORDER BY id")
        )
    ).mappings().all()
    return [
        {
            "id": r["id"],
            "title": _title(r["title"]),
            "description": r["description"],
            "tags": r["tags"],
            "phase": r["phase"],
        }
        for r in rows
    ]


async def get_sections(fsession, form_id: int, version: int | None = None) -> list[dict]:
    base = "SELECT id, form_id, title, description, position, is_active, version FROM form_section"
    if version is None:
        rows = (
            await fsession.execute(
                text(f"{base} WHERE form_id = :f AND is_active = true ORDER BY position, id"),
                {"f": form_id},
            )
        ).mappings().all()
    else:
        rows = (
            await fsession.execute(
                text(f"{base} WHERE form_id = :f AND version = :v ORDER BY position, id"),
                {"f": form_id, "v": version},
            )
        ).mappings().all()
        if not rows:
            rows = (
                await fsession.execute(
                    text(f"{base} WHERE form_id = :f ORDER BY position, id"), {"f": form_id}
                )
            ).mappings().all()
    out = []
    for r in rows:
        d = dict(r)
        d["title"] = _title(r["title"])
        out.append(d)
    return out


async def get_fields_for_section(fsession, section_id: int) -> list[dict]:
    rows = (
        await fsession.execute(
            text(
                "SELECT id, section_id, form_id, label, name, description, type::text AS type, "
                "placeholder, required, disabled, validation, error_message, prefix, position, "
                "is_active, version FROM form_field WHERE section_id = :s ORDER BY position, id"
            ),
            {"s": section_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_response(fsession, response_id: int) -> dict | None:
    row = (
        await fsession.execute(
            text(
                "SELECT id, form_id, shared_id, user_id, email, token::text AS token, "
                "current_section, submitted_at, metadata, form_version "
                "FROM form_response WHERE id = :i"
            ),
            {"i": response_id},
        )
    ).mappings().first()
    return dict(row) if row else None


async def get_responses_for_form(fsession, form_id: int, submitted_only: bool = True) -> list[dict]:
    where = "AND submitted_at IS NOT NULL" if submitted_only else ""
    rows = (
        await fsession.execute(
            text(
                "SELECT id, form_id, shared_id, user_id, email, token::text AS token, "
                f"current_section, submitted_at, metadata, form_version "
                f"FROM form_response WHERE form_id = :f {where} ORDER BY id"
            ),
            {"f": form_id},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


async def get_response_values(fsession, response_id: int) -> dict[int, str]:
    rows = (
        await fsession.execute(
            text("SELECT field_id, value FROM responses WHERE response_id = :i"),
            {"i": response_id},
        )
    ).all()
    return {r[0]: r[1] for r in rows}


async def get_values_for_responses(fsession, response_ids: list[int]) -> dict[int, dict[int, str]]:
    if not response_ids:
        return {}
    ids = ",".join(str(int(i)) for i in response_ids)
    rows = (
        await fsession.execute(
            text(f"SELECT response_id, field_id, value FROM responses WHERE response_id IN ({ids})")
        )
    ).all()
    out: dict[int, dict[int, str]] = {}
    for rid, fid, val in rows:
        out.setdefault(rid, {})[fid] = val
    return out


async def get_values_by_field_name(fsession, response_id: int) -> dict[str, str]:
    rows = (
        await fsession.execute(
            text(
                "SELECT f.name, r.value FROM responses r "
                "JOIN form_field f ON f.id = r.field_id WHERE r.response_id = :i"
            ),
            {"i": response_id},
        )
    ).all()
    return {r[0]: r[1] for r in rows}


async def count_responses(fsession, form_id: int, submitted: bool) -> int:
    cond = "submitted_at IS NOT NULL" if submitted else "submitted_at IS NULL"
    row = (
        await fsession.execute(
            text(f"SELECT count(*) FROM form_response WHERE form_id = :f AND {cond}"),
            {"f": form_id},
        )
    ).scalar()
    return int(row or 0)


async def form_versions(fsession, form_id: int) -> list[int]:
    rows = (
        await fsession.execute(
            text(
                "SELECT DISTINCT version FROM form_field WHERE form_id = :f "
                "UNION SELECT DISTINCT version FROM form_section WHERE form_id = :f"
            ),
            {"f": form_id},
        )
    ).all()
    return sorted(r[0] for r in rows)


async def valid_leaf_pairs(fsession, form_id: int, version: int) -> set[tuple[int, int]]:
    rows = (
        await fsession.execute(
            text("SELECT section_id, id FROM form_field WHERE form_id = :f AND version = :v"),
            {"f": form_id, "v": version},
        )
    ).all()
    if not rows:
        rows = (
            await fsession.execute(
                text("SELECT section_id, id FROM form_field WHERE form_id = :f"), {"f": form_id}
            )
        ).all()
    return {(r[0], r[1]) for r in rows}


async def fetch_mappings(db, edict_id: int, form_type: str) -> list[dict]:
    rows = (
        await db.execute(
            text(
                "SELECT id, edict_id, form_type, mapping, is_active, created_at, form_id, "
                "user_id, form_version FROM edict_form_mappings "
                "WHERE edict_id = :e AND form_type = :t ORDER BY form_version, id"
            ),
            {"e": edict_id, "t": form_type},
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def choose_mapping(mappings: list[dict], version: int | None) -> dict | None:
    if not mappings:
        return None
    if version is not None:
        for m in mappings:
            if m["form_version"] == version:
                return m
    return mappings[-1]
