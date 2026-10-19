"""Acesso ao banco do Forms. As funções SQL do Forms são infraestrutura fornecida:
aqui apenas consultamos e atualizamos as tabelas existentes."""
import json
from datetime import datetime

from sqlalchemy import text


def _rows(fs, sql, **params):
    return [dict(r) for r in fs.execute(text(sql), params).mappings().all()]


def _norm_tags(tags):
    if tags is None:
        return []
    if isinstance(tags, (list, dict)):
        return tags
    try:
        return json.loads(tags)
    except Exception:
        return [t.strip() for t in str(tags).split(",") if t.strip()]


def list_forms(fs):
    rows = _rows(fs, "SELECT id, title, tags, phase FROM forms ORDER BY id")
    for r in rows:
        r["tags"] = _norm_tags(r.get("tags"))
    return rows


def get_form(fs, form_id):
    rows = _rows(fs, "SELECT id, title, tags, phase FROM forms WHERE id = :i", i=str(form_id))
    if not rows:
        return None
    r = rows[0]
    r["tags"] = _norm_tags(r.get("tags"))
    return r


def raw_sections(fs, form_id):
    return _rows(
        fs,
        "SELECT id, name, label, position, version, active FROM sections "
        "WHERE form_id = :f ORDER BY position",
        f=str(form_id),
    )


def select_sections(fs, form_id, version=None):
    """Seleção de seções por versão, com o fallback original (todas, por posição)."""
    rows = raw_sections(fs, form_id)
    if version is not None:
        sel = [
            r for r in rows
            if (r.get("version") is not None and str(r["version"]) == str(version))
            or (str(version) == "1" and r.get("version") is None)
        ]
    else:
        sel = [r for r in rows if r.get("active")]
    return sel or rows


def section_fields(fs, section_id):
    return _rows(
        fs,
        "SELECT id, section_id, name, label, type, prefix, position, options "
        "FROM fields WHERE section_id = :s ORDER BY position",
        s=str(section_id),
    )


def get_answer(fs, answer_id):
    rows = _rows(
        fs,
        "SELECT id, form_id, version, email, finalized, current_section, created_at "
        "FROM answers WHERE id = :a",
        a=str(answer_id),
    )
    return rows[0] if rows else None


def answer_values(fs, answer_id):
    """Valores da resposta com metadados dos campos e seções."""
    return _rows(
        fs,
        "SELECT f.id AS field_id, f.name, f.label, f.type, f.prefix, "
        "s.id AS section_id, s.name AS section_name, v.value "
        "FROM answer_values v "
        "JOIN fields f ON f.id = v.field_id "
        "JOIN sections s ON s.id = f.section_id "
        "WHERE v.answer_id = :a",
        a=str(answer_id),
    )


def answers_for_form(fs, form_id):
    return _rows(
        fs,
        "SELECT id, form_id, version, email, finalized, current_section, created_at "
        "FROM answers WHERE form_id = :f ORDER BY created_at",
        f=str(form_id),
    )


def set_form_phase(fs, form_id, phase):
    fs.execute(text("UPDATE forms SET phase = :p WHERE id = :i"), {"p": phase, "i": str(form_id)})
    fs.commit()


def reopen_answer(fs, answer_id):
    fs.execute(
        text("UPDATE answers SET current_section = 0, finalized = false WHERE id = :a"),
        {"a": str(answer_id)},
    )
    fs.commit()


def share_for_answer(fs, answer_id):
    rows = _rows(
        fs,
        "SELECT id, token, email, expiration, single FROM shares WHERE answer_id = :a",
        a=str(answer_id),
    )
    return rows[0] if rows else None


def create_share(fs, answer_id, email, expires=None, single=True):
    import uuid

    token = uuid.uuid4().hex
    rows = _rows(
        fs,
        "INSERT INTO shares (answer_id, email, token, expiration, single, private) "
        "VALUES (:a, :e, :t, :x, :s, true) RETURNING id, token",
        a=str(answer_id), e=email, t=token,
        x=expires, s=single,
    )
    fs.commit()
    return rows[0]


def create_answer(fs, form_id, email, version="1"):
    rows = _rows(
        fs,
        "INSERT INTO answers (form_id, email, version, finalized, current_section) "
        "VALUES (:f, :e, :v, false, 0) RETURNING id",
        f=str(form_id), e=email, v=str(version),
    )
    fs.commit()
    return rows[0]["id"]
