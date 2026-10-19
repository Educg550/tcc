import uuid
from datetime import date
from typing import Any

from sqlalchemy import text

from database import FormsSessionLocal

FORM_PHASE_MAP = {
    "inscricoes": "Registration",
    "homologacao": "Approval",
    "avaliacao": "Completed",
    "encerrado": "Completed",
}


async def _fetch_all(query: str, params: dict | None = None) -> list[dict]:
    async with FormsSessionLocal() as session:
        result = await session.execute(text(query), params or {})
        return [dict(row._mapping) for row in result.fetchall()]


async def _execute(query: str, params: dict | None = None) -> Any:
    async with FormsSessionLocal() as session:
        result = await session.execute(text(query), params or {})
        await session.commit()
        return result


def _label(label: Any) -> str:
    if isinstance(label, dict):
        return label.get("pt") or label.get("en") or ""
    return label or ""


async def list_forms(year: str | None = None, notice: str | None = None) -> list[dict]:
    rows = await _fetch_all("select id, title, description, created_at, phase, tags, version from form order by id")
    out = []
    for row in rows:
        tags = row["tags"] if isinstance(row["tags"], dict) else {}
        if year and str(tags.get("Ano", "")) != year:
            continue
        if notice and str(tags.get("Edital", "")) != notice:
            continue
        out.append(
            {
                "id": row["id"],
                "title": _label(row["title"]),
                "description": _label(row["description"]),
                "created_at": row["created_at"],
                "tags": tags,
                "phase": row["phase"],
                "version": row["version"],
            }
        )
    return out


async def get_form(form_id: int) -> dict | None:
    rows = await _fetch_all("select * from form where id = :id", {"id": form_id})
    return rows[0] if rows else None


async def get_sections(form_id: int, version: int | None = None) -> list[dict]:
    if version is None:
        rows = await _fetch_all(
            "select * from form_section where form_id = :f and is_active = true order by position, id",
            {"f": form_id},
        )
    else:
        extra = " or version is null" if version == 1 else ""
        rows = await _fetch_all(
            f"select * from form_section where form_id = :f and (version = :v{extra}) order by position, id",
            {"f": form_id, "v": version},
        )
    if not rows:
        rows = await _fetch_all(
            "select * from form_section where form_id = :f order by position, id", {"f": form_id}
        )
    return rows


async def get_section_ids(form_id: int, version: int | None = None) -> list[int]:
    return [s["id"] for s in await get_sections(form_id, version)]


async def get_fields(section_id: int, version: int | None = None, active_only: bool = False) -> list[dict]:
    if version is None and not active_only:
        rows = await _fetch_all(
            "select * from form_field where section_id = :s order by position, id", {"s": section_id}
        )
    elif version is None:
        rows = await _fetch_all(
            "select * from form_field where section_id = :s and is_active = true order by position, id",
            {"s": section_id},
        )
    else:
        extra = " or version is null" if version == 1 else ""
        rows = await _fetch_all(
            f"select * from form_field where section_id = :s and (version = :v{extra}) order by position, id",
            {"s": section_id, "v": version},
        )
    if not rows:
        rows = await _fetch_all(
            "select * from form_field where section_id = :s order by position, id", {"s": section_id}
        )
    return rows


async def get_form_fields(form_id: int) -> list[dict]:
    return await _fetch_all(
        "select * from form_field where form_id = :f order by id", {"f": form_id}
    )


async def get_form_full(form_id: int, version: int | None = None) -> dict | None:
    form = await get_form(form_id)
    if form is None:
        return None
    sections = []
    for section in await get_sections(form_id, version):
        fields = await get_fields(section["id"], version)
        sections.append(
            {
                "id": section["id"],
                "title": _label(section["title"]),
                "description": _label(section["description"]),
                "position": section["position"],
                "version": section["version"],
                "is_active": section["is_active"],
                "fields": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "label": _label(f["label"]),
                        "description": _label(f["description"]),
                        "type": f["type"],
                        "prefix": f["prefix"],
                        "placeholder": f["placeholder"],
                        "required": f["required"],
                        "position": f["position"],
                        "version": f["version"],
                    }
                    for f in fields
                ],
            }
        )
    return {
        "id": form["id"],
        "title": _label(form["title"]),
        "description": _label(form["description"]),
        "tags": form["tags"],
        "phase": form["phase"],
        "version": form["version"],
        "sections": sections,
    }


async def get_form_responses(form_id: int) -> list[dict]:
    return await _fetch_all(
        "select id, token, submitted_at, email, form_version, current_section, shared_id, user_id"
        " from form_response where form_id = :f order by id",
        {"f": form_id},
    )


async def get_response(response_id: int) -> dict | None:
    rows = await _fetch_all(
        "select id, form_id, token, submitted_at, email, form_version, current_section, shared_id, user_id"
        " from form_response where id = :id",
        {"id": response_id},
    )
    return rows[0] if rows else None


async def get_answers(response_ids: list[int]) -> dict[int, dict[int, str]]:
    if not response_ids:
        return {}
    ids = ",".join(str(int(i)) for i in response_ids)
    rows = await _fetch_all(
        f"select response_id, field_id, value from responses where response_id in ({ids})"
    )
    out: dict[int, dict[int, str]] = {}
    for row in rows:
        out.setdefault(row["response_id"], {})[row["field_id"]] = row["value"]
    return out


async def change_form_phase(form_id: int, phase: str) -> None:
    await _execute(
        "select * from change_form_phase(:id, CAST(:phase AS form_phase))",
        {"id": form_id, "phase": phase},
    )


async def reopen_response(response_id: int) -> None:
    await _execute(
        "select * from update_form_response_section(:id, 0)", {"id": response_id}
    )
    await _execute(
        "update form_response set submitted_at = null where id = :id", {"id": response_id}
    )


async def create_shared(form_id: int, expiration_at: date | None) -> dict:
    token = str(uuid.uuid4())
    rows = await _execute(
        "insert into form_shared (form_id, unique_answers, is_public, token, created_at, expiration_at)"
        " values (:f, true, false, :token, now(), :exp) returning id, token",
        {"f": form_id, "token": token, "exp": expiration_at},
    )
    return {"id": rows[0]["id"], "token": rows[0]["token"]}


async def create_response(form_id: int, shared_id: int, email: str, form_version: int) -> dict:
    token = str(uuid.uuid4())
    rows = await _execute(
        "insert into form_response (form_id, shared_id, email, token, current_section, form_version)"
        " values (:f, :s, :e, :token, 0, :v) returning id, token",
        {"f": form_id, "s": shared_id, "e": email, "token": token, "v": form_version},
    )
    return {"id": rows[0]["id"], "token": rows[0]["token"]}
