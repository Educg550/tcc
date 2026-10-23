import json

from sqlalchemy import text

import services.forms_db as forms_db
from database import SessionLocal

TRUE_VALUES = {"true", "sim", "yes", "1", "verdadeiro"}


def as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in TRUE_VALUES


def as_int(v):
    try:
        return int(str(v))
    except (TypeError, ValueError):
        return v


def _node(resolved, key):
    node = resolved.get(key) if isinstance(resolved, dict) else None
    return node if isinstance(node, dict) else {}


def _val(resolved, key, default=""):
    if not isinstance(resolved, dict):
        return default
    v = resolved.get(key)
    return default if v is None else v


async def get_edict(edict_id: int) -> dict | None:
    async with SessionLocal() as s:
        rows = await s.execute(text("select * from edict where id = :id"), {"id": edict_id})
        r = rows.fetchone()
        return dict(r._mapping) if r else None


async def get_submission(submission_id: int) -> dict | None:
    async with SessionLocal() as s:
        rows = await s.execute(
            text("select * from submission where id = :id"), {"id": submission_id}
        )
        r = rows.fetchone()
        return dict(r._mapping) if r else None


async def get_user(user_id: int) -> dict | None:
    async with SessionLocal() as s:
        rows = await s.execute(
            text('select id, name, email, role, nusp from "user" where id = :id'),
            {"id": user_id},
        )
        r = rows.fetchone()
        return dict(r._mapping) if r else None


async def ensure_submission(edict_id: int, candidate_form_id: int, form_version: int) -> dict:
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select * from submission where candidate_form_id = :c and edict_id = :e"
            ),
            {"c": candidate_form_id, "e": edict_id},
        )
        r = rows.fetchone()
        if r:
            return dict(r._mapping)
        rows = await s.execute(
            text(
                "insert into submission (edict_id, candidate_form_id,"
                " candidate_form_version, recommender_form_version, recommenders_form_ids,"
                " created_at, updated_at)"
                " values (:e, :c, :v, 1, '[]'::json, now(), now()) returning *"
            ),
            {"e": edict_id, "c": candidate_form_id, "v": form_version},
        )
        await s.commit()
        return dict(rows.fetchone()._mapping)


async def get_mapping(edict_id: int, form_type: str, version: int) -> dict | None:
    async with SessionLocal() as s:
        rows = await s.execute(
            text(
                "select mapping from edict_form_mappings where edict_id = :e"
                " and form_type = :t and form_version = :v and is_active = true"
            ),
            {"e": edict_id, "t": form_type, "v": version},
        )
        r = rows.fetchone()
        if r:
            return r.mapping
        rows = await s.execute(
            text(
                "select mapping from edict_form_mappings where edict_id = :e"
                " and form_type = :t and is_active = true"
                " order by form_version desc limit 1"
            ),
            {"e": edict_id, "t": form_type},
        )
        r = rows.fetchone()
        return r.mapping if r else None


async def all_form_fields(form_id: int, version: int | None) -> list[dict]:
    sections = await forms_db.get_sections(form_id, version)
    fields: list[dict] = []
    for section in sections:
        fields.extend(await forms_db.get_fields(section["id"], version))
    return fields


async def accept_info(accept_form_id) -> dict:
    empty = {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if not accept_form_id:
        return empty
    fr = await forms_db.get_response(accept_form_id)
    if not fr:
        return empty
    if fr.submitted_at is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values = await forms_db.get_response_values(accept_form_id)
    fields = await all_form_fields(fr.form_id, fr.form_version)
    accept_val = None
    comments_val = None
    for f in fields:
        name = (f["name"] or "").lower()
        if accept_val is None and any(k in name for k in ("accept", "decision", "aceite")):
            accept_val = values.get(f["id"])
        if comments_val is None and any(
            k in name for k in ("comment", "observ", "note", "descricao")
        ):
            comments_val = values.get(f["id"])
    if accept_val is None and comments_val is None:
        vals = [v for v in values.values() if v]
        if vals:
            accept_val = vals[0]
        if len(vals) > 1:
            comments_val = vals[1]
    return {
        "sent": "replied",
        "accept": accept_val,
        "comments": comments_val,
        "submitted_at": fr.submitted_at.isoformat(),
    }


def _candidate_key(name, email):
    return (
        (name or "").strip().lower(),
        (email or "").strip().lower(),
    )


async def load_recommendations(edict: dict) -> dict:
    """Agrupa respostas de recomendação pela candidatura (nome/e-mail)."""
    result: dict = {}
    form_id = edict.get("recommenders_forms")
    if form_id is None:
        return result
    responses = await forms_db.get_submitted_responses(int(form_id))
    for fr in responses:
        values = await forms_db.get_response_values(fr.id)
        mapping = await get_mapping(edict["id"], "recommender", fr.form_version)
        resolved = {}
        if mapping:
            from services.mappings import resolve_mapping

            resolved = resolve_mapping(mapping, values) or {}
        cand_name = None
        cand_email = None
        for key in ("name", "nome", "candidate_name", "candidate"):
            if _val(resolved, key):
                cand_name = _val(resolved, key)
                break
        for key in ("email", "candidate_email", "email_candidate"):
            if _val(resolved, key):
                cand_email = _val(resolved, key)
                break
        rec = {
            "id": fr.id,
            "email": fr.email,
            "submitted_at": fr.submitted_at.isoformat() if fr.submitted_at else None,
            "name": _val(resolved, "recommender_name")
            or _val(resolved, "recommender")
            or fr.email,
        }
        key = _candidate_key(cand_name, cand_email)
        if key[0] or key[1]:
            result.setdefault(key, []).append(rec)
        else:
            result.setdefault(("by_response", fr.id), []).append(rec)
    return result


async def associate_recommendations(
    submission: dict, cand_name: str, cand_email: str, recommendations: dict
) -> list[dict]:
    key = _candidate_key(cand_name, cand_email)
    recs = recommendations.get(key, [])
    ids = [r["id"] for r in recs]
    current = submission.get("recommenders_form_ids") or []
    if isinstance(current, str):
        current = json.loads(current)
    if sorted(current) != sorted(ids):
        async with SessionLocal() as s:
            await s.execute(
                text(
                    "update submission set recommenders_form_ids = :ids::json,"
                    " updated_at = now() where id = :id"
                ),
                {"ids": json.dumps(ids), "id": submission["id"]},
            )
            await s.commit()
    return recs


async def build_submission_form(form_id: int, version: int, values: dict) -> list[dict]:
    sections = await forms_db.get_sections(form_id, version)
    out = []
    for section in sections:
        fields = await forms_db.get_fields(section["id"], version)
        out.append(
            {
                "id": section["id"],
                "name": section["title"],
                "label": section["title"],
                "description": section["description"],
                "position": section["position"],
                "fields": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "label": f["label"],
                        "type": f["type"],
                        "prefix": f["prefix"],
                        "position": f["position"],
                        "required": f["required"],
                        "value": values.get(f["id"]),
                    }
                    for f in fields
                ],
            }
        )
    return out


def build_summary_fields(resolved: dict) -> dict:
    graduation = _node(resolved, "graduation")
    poscomp_node = _node(resolved, "poscomp")
    poscomp = None
    if poscomp_node or _val(resolved, "poscomp"):
        if not poscomp_node and _val(resolved, "poscomp"):
            poscomp = {"year": as_int(_val(resolved, "poscomp")), "score": ""}
        else:
            poscomp = {
                "year": as_int(_val(poscomp_node, "year")),
                "score": str(_val(poscomp_node, "score")),
            }
    research = _node(resolved, "research")
    field = _node(research, "field")
    return {
        "name": str(_val(resolved, "name")),
        "email": str(_val(resolved, "email")),
        "phone_number": str(_val(resolved, "phone_number")),
        "nationality": str(_val(resolved, "nationality")),
        "personal_website": str(_val(resolved, "personal_website")),
        "gender": str(_val(resolved, "gender")),
        "birth_date": str(_val(resolved, "birth_date")),
        "graduation": {
            "country": str(_val(graduation, "country")),
            "course": str(_val(graduation, "course")),
            "institution": str(_val(graduation, "institution")),
            "year": as_int(_val(graduation, "year")),
        },
        "poscomp": poscomp,
        "current_occupation": _val(resolved, "current_occupation"),
        "research": {
            "program": str(_val(research, "program")),
            "semester": str(_val(research, "semester")),
            "field": {
                "primary": str(_val(field, "primary")),
                "secondary": str(_val(field, "secondary")),
            },
            "will_apply_scholarship": as_bool(_val(research, "will_apply_scholarship")),
            "dedication_level": str(_val(research, "dedication_level")),
        },
        "lattes_curriculum": str(_val(resolved, "lattes_curriculum")),
        "disabilities": as_bool(_val(resolved, "disabilities")),
        "ethnicity_race": as_bool(_val(resolved, "ethnicity_race")),
    }


async def edict_context(edict_id: int, user_id: int) -> dict:
    """Favoritos, etiquetas, interesses e vagas do edital para montagem."""
    async with SessionLocal() as s:
        favs = await s.execute(
            text(
                "select submission_id from favorites where user_id = :u"
                " and submission_id in (select id from submission where edict_id = :e)"
            ),
            {"u": user_id, "e": edict_id},
        )
        favorites = {r.submission_id for r in favs.fetchall()}
        labels = await s.execute(
            text(
                "select id, user_id, submission_id, label, color, context_type"
                " from labels where submission_id in"
                " (select id from submission where edict_id = :e)"
            ),
            {"e": edict_id},
        )
        all_labels = [dict(r._mapping) for r in labels.fetchall()]
        slots = await s.execute(
            text(
                'select u.id, u.name, u.email, coalesce(s.slots, 0) as slots'
                ' from "user" u left join user_edict_slots s'
                " on s.user_id = u.id and s.edict_id = :e"
                " where u.id in (select user_id from user_edict_slots"
                " where edict_id = :e union select user_id from labels"
                " where context_type = 'bidding' and submission_id in"
                " (select id from submission where edict_id = :e))"
            ),
            {"e": edict_id},
        )
        slot_rows = [dict(r._mapping) for r in slots.fetchall()]
        return {"favorites": favorites, "labels": all_labels, "slots": slot_rows}


def _bidding_users(labels: list[dict], slots: list[dict]) -> dict:
    data: dict = {}
    slot_by_user = {s["id"]: s for s in slots}
    for lab in labels:
        if (lab.get("context_type") or "") != "bidding":
            continue
        entry = data.setdefault(lab["label"], [])
        s = slot_by_user.get(lab["user_id"])
        entry.append(
            {
                "id": lab["user_id"],
                "name": s["name"] if s else str(lab["user_id"]),
                "email": s["email"] if s else None,
                "slots": str(s["slots"]) if s else "0",
            }
        )
    return {"data": data}


def _submission_labels(labels: list[dict], submission_id: int) -> list[dict]:
    out = []
    for lab in labels:
        if lab["submission_id"] != submission_id:
            continue
        if (lab.get("context_type") or "candidate") == "bidding":
            continue
        out.append({"id": lab["id"], "label": lab["label"], "color": lab["color"]})
    return out
