import re

from sqlalchemy import text


async def get_edict(db, edict_id: int) -> dict | None:
    result = await db.execute(text("SELECT * FROM edict WHERE id = :i"), {"i": edict_id})
    row = result.first()
    return dict(row._mapping) if row else None


async def get_mappings(db, edict_id: int, form_type: str) -> list[dict]:
    result = await db.execute(
        text(
            "SELECT * FROM edict_form_mappings "
            "WHERE edict_id = :e AND form_type = :t ORDER BY id"
        ),
        {"e": edict_id, "t": form_type},
    )
    return [dict(r._mapping) for r in result]


def choose_mapping(mappings: list[dict], form_version: int | None) -> dict | None:
    if not mappings:
        return None
    for mapping in mappings:
        if mapping["form_version"] == form_version:
            return mapping
    return max(mappings, key=lambda m: m["form_version"])


async def response_row(fdb, response_id: int) -> dict | None:
    result = await fdb.execute(
        text(
            "SELECT id, form_id, shared_id, email, token::text AS token, "
            "current_section, submitted_at, form_version "
            "FROM form_response WHERE id = :i"
        ),
        {"i": response_id},
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def response_values(fdb, response_id: int) -> dict:
    result = await fdb.execute(
        text("SELECT field_id, value FROM responses WHERE response_id = :i"),
        {"i": response_id},
    )
    return {row[0]: row[1] for row in result}


def _clean(value):
    if isinstance(value, str):
        return value.strip()
    return value


def date_only(value):
    if not isinstance(value, str):
        return value
    value = value.strip()
    if len(value) >= 10 and value[4] == "-" and value[7] == "-":
        return value[:10]
    match = re.match(r"^(\d{2})/(\d{2})/(\d{4})", value)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return value


def extract(mapping: dict | None, values: dict) -> dict:
    output = {}
    for key, node in (mapping or {}).items():
        if node is None:
            output[key] = None
        elif isinstance(node, dict) and set(node) == {"section", "field"}:
            output[key] = _clean(values.get(node["field"]))
        elif isinstance(node, dict):
            output[key] = extract(node, values)
        else:
            output[key] = None
    return output


async def sections_of(fdb, form_id: int, version: int | None = None) -> list[dict]:
    if version is not None:
        result = await fdb.execute(
            text(
                "SELECT * FROM form_section WHERE form_id = :f AND version = :v "
                "ORDER BY position, id"
            ),
            {"f": form_id, "v": version},
        )
        rows = [dict(r._mapping) for r in result]
        if rows:
            return rows
        result = await fdb.execute(
            text("SELECT * FROM form_section WHERE form_id = :f ORDER BY position, id"),
            {"f": form_id},
        )
        return [dict(r._mapping) for r in result]
    result = await fdb.execute(
        text(
            "SELECT * FROM form_section WHERE form_id = :f AND is_active = true "
            "ORDER BY position, id"
        ),
        {"f": form_id},
    )
    return [dict(r._mapping) for r in result]


async def fields_of_section(fdb, section_id: int) -> list[dict]:
    result = await fdb.execute(
        text("SELECT * FROM form_field WHERE section_id = :s ORDER BY position, id"),
        {"s": section_id},
    )
    return [dict(r._mapping) for r in result]


_FALSE_VALUES = ("", "false", "no", "não", "nao", "n", "0", "nenhuma", "nenhum", "não possuo")


def to_bool(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in _FALSE_VALUES


def poscomp_or_none(data: dict):
    poscomp = data.get("poscomp")
    if isinstance(poscomp, dict) and any(v not in (None, "") for v in poscomp.values()):
        return poscomp
    return None
