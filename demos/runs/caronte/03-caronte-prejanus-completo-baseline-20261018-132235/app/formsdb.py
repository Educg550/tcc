"""Access layer for the Forms database (read and write).

The Forms service owns forms, sections, fields, answers, shares and
versions. This module concentrates every query the backend makes against
that database, using the connection configured in DB_CONNECTION_STRING_FORMS.
"""
from datetime import datetime

from sqlalchemy import text

from .db import forms_engine


def _rows(sql, params=None):
    with forms_engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql), params or {})]


def _execute(sql, params=None):
    with forms_engine.begin() as conn:
        conn.execute(text(sql), params or {})


def _first(sql, params=None):
    rows = _rows(sql, params)
    return rows[0] if rows else None


# --- forms -----------------------------------------------------------------

def list_forms(year: str | None = None, notice: str | None = None) -> list[dict]:
    rows = _rows("SELECT * FROM forms ORDER BY id")
    result = []
    for row in rows:
        tags = row.get("tags")
        tag_values: list[str] = []
        if isinstance(tags, (list, tuple)):
            tag_values = [str(t) for t in tags]
        elif isinstance(tags, dict):
            tag_values = [str(v) for v in tags.values()]
        elif tags is not None:
            tag_values = [str(tags)]
        if year is not None and not any(
            str(year) in t or f"Ano: {year}" in t for t in tag_values
        ):
            continue
        if notice is not None and not any(
            str(notice) in t or f"Edital: {notice}" in t for t in tag_values
        ):
            continue
        result.append(
            {
                "id": row.get("id"),
                "title": row.get("title") or row.get("name"),
                "description": row.get("description"),
                "tags": tags,
                "phase": row.get("phase"),
                "created_at": row.get("created_at"),
            }
        )
    return result


def get_form(form_id: int) -> dict | None:
    return _first("SELECT * FROM forms WHERE id = :id", {"id": form_id})


def set_form_phase(form_id: int, phase: str) -> None:
    _execute("UPDATE forms SET phase = :phase WHERE id = :id",
             {"phase": phase, "id": form_id})


# --- sections and fields ---------------------------------------------------

def get_sections(form_id: int, version: int | None = None) -> list[dict]:
    """Sections of a form, honoring the original selection and fallback rules.

    With a version, select that version (version 1 also accepts null
    versions). Without it, select active sections. When the selection
    finds nothing, fall back to every section of the form ordered by
    position.
    """
    if version is not None:
        rows = _rows(
            "SELECT * FROM sections WHERE form_id = :fid ORDER BY position",
            {"fid": form_id},
        )
        selected = [
            r for r in rows
            if r.get("version") == version
            or (version == 1 and r.get("version") is None)
        ]
    else:
        rows = _rows(
            "SELECT * FROM sections WHERE form_id = :fid ORDER BY position",
            {"fid": form_id},
        )
        selected = [r for r in rows if r.get("active") in (None, True)]
    if not selected:
        selected = rows
    return selected


def get_section(section_id: int) -> dict | None:
    return _first("SELECT * FROM sections WHERE id = :id", {"id": section_id})


def get_fields(section_id: int) -> list[dict]:
    return _rows(
        "SELECT * FROM fields WHERE section_id = :sid ORDER BY position",
        {"sid": section_id},
    )


def field_exists(section_id: int, field_id: int) -> bool:
    return _first(
        "SELECT id FROM fields WHERE id = :fid AND section_id = :sid",
        {"fid": field_id, "sid": section_id},
    ) is not None


# --- answers ---------------------------------------------------------------

def get_answers(form_id: int, email: str | None = None,
                 version: int | None = None) -> list[dict]:
    """Answers of a form, optionally by access email and/or version."""
    sql = "SELECT * FROM answers WHERE form_id = :fid"
    params: dict = {"fid": form_id}
    if email is not None:
        sql += " AND email = :email"
        params["email"] = email
    if version is not None:
        sql += " AND (version = :version OR (version IS NULL AND :version = 1))"
        params["version"] = version
    return _rows(sql + " ORDER BY id", params)


def get_answer(answer_id: int) -> dict | None:
    return _first("SELECT * FROM answers WHERE id = :id", {"id": answer_id})


def get_answer_by_token(token: str) -> dict | None:
    return _first("SELECT * FROM answers WHERE token = :token", {"token": token})


def get_answer_values(answer_id: int) -> dict[tuple[int, int], str]:
    """Values of an answer as {(section_id, field_id): value}."""
    rows = _rows(
        "SELECT av.value, f.id AS field_id, f.section_id AS section_id "
        "FROM answers_fields av JOIN fields f ON av.field_id = f.id "
        "WHERE av.answer_id = :aid",
        {"aid": answer_id},
    )
    return {(r["section_id"], r["field_id"]): r["value"] for r in rows}


def answer_values(answer_id: int) -> dict[int, str]:
    """Values of an answer as {field_id: value}."""
    rows = _rows(
        "SELECT field_id, value FROM answers_fields WHERE answer_id = :aid",
        {"aid": answer_id},
    )
    return {r["field_id"]: r["value"] for r in rows}


def reopen_answer(answer_id: int) -> None:
    """Reopen a finalized answer so the candidate can correct it."""
    _execute(
        "UPDATE answers SET current_state = 'in_progress', current_section = 0 "
        "WHERE id = :id",
        {"id": answer_id},
    )


def create_answer(form_id: int, email: str, token: str,
                  version: int | None = None) -> int:
    """Create an answer linked to an access email; return its id."""
    _execute(
        "INSERT INTO answers (form_id, email, token, version, current_state, "
        "current_section, created_at) VALUES "
        "(:fid, :email, :token, :version, 'in_progress', 0, :now)",
        {"fid": form_id, "email": email, "token": token,
         "version": version, "now": datetime.utcnow()},
    )
    row = _first("SELECT id FROM answers WHERE token = :token", {"token": token})
    return row["id"]


# --- shares ----------------------------------------------------------------

def create_share(form_id: int, token: str, expires_at=None,
                 single_answer: bool = True, private: bool = True) -> int:
    """Create a share for a form; return its id."""
    _execute(
        "INSERT INTO shares (form_id, token, expires_at, single_answer, private, "
        "created_at) VALUES (:fid, :token, :exp, :single, :private, :now)",
        {"fid": form_id, "token": token, "exp": expires_at,
         "single": single_answer, "private": private,
         "now": datetime.utcnow()},
    )
    row = _first("SELECT id FROM shares WHERE token = :token", {"token": token})
    return row["id"]


def get_share_by_token(token: str) -> dict | None:
    return _first("SELECT * FROM shares WHERE token = :token", {"token": token})