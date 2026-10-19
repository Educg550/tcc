import copy
import json
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import services.forms_service as forms_service

BOOL_KEYS = {"will_apply_scholarship", "disabilities", "ethnicity_race"}
INT_KEYS = {"year"}

SUMMARY_DEFAULTS = {
    "name": "",
    "email": "",
    "phone_number": "",
    "nationality": "",
    "personal_website": "",
    "gender": "",
    "birth_date": "",
    "graduation": {"country": "", "course": "", "institution": "", "year": 0},
    "poscomp": None,
    "current_occupation": None,
    "research": {
        "program": "",
        "semester": "",
        "field": {"primary": "", "secondary": ""},
        "will_apply_scholarship": False,
        "dedication_level": "",
    },
    "lattes_curriculum": "",
    "disabilities": False,
    "ethnicity_race": False,
}


def _is_leaf(node):
    return (
        isinstance(node, dict)
        and isinstance(node.get("section"), int)
        and isinstance(node.get("field"), int)
    )


def _coerce(key, value):
    if value is None:
        return None
    if key in BOOL_KEYS:
        return str(value).strip().lower() in ("true", "1", "yes", "sim", "verdadeiro")
    if key in INT_KEYS:
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    return value


def resolve_tree(tree, values):
    """Resolve a árvore de mapeamento contra {field_id: value} das respostas."""
    out = {}
    if not isinstance(tree, dict):
        return out
    for key, node in tree.items():
        if node is None:
            continue
        if _is_leaf(node):
            out[key] = _coerce(key, values.get(node["field"]))
        elif isinstance(node, dict):
            out[key] = resolve_tree(node, values)
    return out


def _deep_merge(base, override):
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def build_summary_data(mapping_tree, values):
    data = copy.deepcopy(SUMMARY_DEFAULTS)
    resolved = resolve_tree(mapping_tree, values)
    _deep_merge(data, resolved)
    if data.get("poscomp") is None and "poscomp" in (resolved or {}):
        data["poscomp"] = resolved["poscomp"]
    return data


async def get_mapping(db: AsyncSession, edict_id: int, form_type: str, version: int):
    row = await db.execute(
        text(
            "select id, edict_id, form_type, mapping, is_active, form_id, user_id, form_version "
            "from edict_form_mappings where edict_id = :eid and form_type = :ft "
            "and form_version = :v"
        ),
        {"eid": edict_id, "ft": form_type, "v": version},
    )
    row = row.first()
    return dict(row._mapping) if row else None


async def get_mappings(db: AsyncSession, edict_id: int, form_type: str):
    rows = await db.execute(
        text(
            "select id, edict_id, form_type, mapping, is_active, form_id, user_id, form_version "
            "from edict_form_mappings where edict_id = :eid and form_type = :ft order by id"
        ),
        {"eid": edict_id, "ft": form_type},
    )
    return [dict(r._mapping) for r in rows]


async def get_edict(db: AsyncSession, edict_id: int):
    row = await db.execute(text("select * from edict where id = :eid"), {"eid": edict_id})
    row = row.first()
    return dict(row._mapping) if row else None


async def get_submission(db: AsyncSession, submission_id: int):
    row = await db.execute(
        text("select * from submission where id = :sid"), {"sid": submission_id}
    )
    row = row.first()
    return dict(row._mapping) if row else None


async def get_user(db: AsyncSession, user_id: int):
    row = await db.execute(
        text('select id, name, email, role, nusp from "user" where id = :uid'),
        {"uid": user_id},
    )
    row = row.first()
    return dict(row._mapping) if row else None


async def sync_submissions(db: AsyncSession, fdb: AsyncSession, edict: dict):
    """Cria inscrições locais para respostas finalizadas e associa recomendações."""
    candidate_form_id = _to_int(edict.get("candidate_forms"))
    if candidate_form_id is None:
        return

    responses = await forms_service.get_form_responses(fdb, candidate_form_id)
    existing = await db.execute(
        text("select id, candidate_form_id, recommenders_form_ids from submission where edict_id = :eid"),
        {"eid": edict["id"]},
    )
    rows = [dict(r._mapping) for r in existing]
    known = {r["candidate_form_id"] for r in rows}

    for response_id, meta in responses.items():
        if response_id in known:
            continue
        await db.execute(
            text(
                "insert into submission (edict_id, candidate_form_id, recommender_form_ids, stats, "
                "recommender_form_version, candidate_form_version) "
                "values (:eid, :cfid, '[]', 'underreview', 1, :v) "
                "on conflict (candidate_form_id, edict_id) do nothing"
            ),
            {
                "eid": edict["id"],
                "cfid": response_id,
                "v": meta.get("form_version") or 1,
            },
        )
    await db.commit()

    # dados de candidato por resposta, para associar recomendações
    candidate_info = {}
    for response_id, meta in responses.items():
        mapping = await get_mapping(
            db, edict["id"], "candidate", meta.get("form_version") or 1
        )
        data = build_summary_data(mapping.get("mapping") if mapping else {}, meta["values"])
        candidate_info[response_id] = {
            "email": (data.get("email") or "").strip().lower(),
            "name": (data.get("name") or "").strip().lower(),
        }

    recommender_form_id = _to_int(edict.get("recommenders_forms"))
    recommendations = {}
    if recommender_form_id is not None:
        rec_responses = await forms_service.get_form_responses(fdb, recommender_form_id)
        for response_id, meta in rec_responses.items():
            mapping = await get_mapping(
                db, edict["id"], "recommender", meta.get("form_version") or 1
            )
            resolved = resolve_tree(mapping.get("mapping") if mapping else {}, meta["values"])
            recommendations[response_id] = resolved

    if not recommendations:
        return
    rows = await db.execute(
        text("select id, candidate_form_id, recommender_form_ids from submission where edict_id = :eid"),
        {"eid": edict["id"]},
    )
    for row in rows:
        sub = dict(row._mapping)
        info = candidate_info.get(sub["candidate_form_id"], {})
        if not (info.get("email") or info.get("name")):
            continue
        matched = []
        for response_id, resolved in recommendations.items():
            rec_email = str(
                resolved.get("candidate_email") or resolved.get("email") or ""
            ).strip().lower()
            rec_name = str(
                resolved.get("candidate_name") or resolved.get("name") or ""
            ).strip().lower()
            if (info.get("email") and rec_email == info["email"]) or (
                info.get("name") and rec_name == info["name"]
            ):
                matched.append(response_id)
        current = sub["recommender_form_ids"]
        current_ids = current if isinstance(current, list) else json.loads(current or "[]")
        if set(current_ids) != set(matched):
            await db.execute(
                text(
                    "update submission set recommender_form_ids = cast(:ids as json), "
                    "updated_at = now() where id = :sid"
                ),
                {"ids": json.dumps(sorted(matched)), "sid": sub["id"]},
            )
    await db.commit()


def _to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def user_labels_for(db: AsyncSession, user_id: int, submission_id: int):
    rows = await db.execute(
        text(
            "select id, label, color from labels where user_id = :uid and submission_id = :sid "
            "and coalesce(context_type, 'candidate') <> 'bidding' order by id"
        ),
        {"uid": user_id, "sid": submission_id},
    )
    return [dict(r._mapping) for r in rows]


async def user_bidding(db: AsyncSession, user_id: int, submission_id: int):
    row = await db.execute(
        text(
            "select label from labels where user_id = :uid and submission_id = :sid "
            "and context_type = 'bidding' limit 1"
        ),
        {"uid": user_id, "sid": submission_id},
    )
    row = row.first()
    return row[0] if row else ""


async def bidding_users(db: AsyncSession, edict_id: int, submission_id: int):
    rows = await db.execute(
        text(
            "select l.label, u.id, u.name, u.email, s.slots from labels l "
            'join "user" u on u.id = l.user_id '
            "left join user_edict_slots s on s.user_id = l.user_id and s.edict_id = :eid "
            "where l.submission_id = :sid and l.context_type = 'bidding' order by u.id"
        ),
        {"eid": edict_id, "sid": submission_id},
    )
    data = {}
    for row in rows:
        entry = {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "slots": str(row.slots) if row.slots is not None else None,
        }
        data.setdefault(row.label, []).append(entry)
    return {"data": data}


async def accept_status(fdb: AsyncSession, sub: dict):
    if not sub.get("accept_form_id"):
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    response = await forms_service.get_response(fdb, sub["accept_form_id"])
    if not response or not response.get("submitted_at"):
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    accept_value = None
    comments = None
    for field_id, value in (response.get("values") or {}).items():
        row = await fdb.execute(
            text("select name, label from form_field where id = :fid"), {"fid": field_id}
        )
        row = row.first()
        if not row:
            continue
        name = (row.name or "").lower()
        label = (row.label or {}).get("pt", "") if isinstance(row.label, dict) else ""
        lowered = f"{name} {label}".lower()
        if accept_value is None and ("aceite" in lowered or "accept" in lowered or "decision" in lowered):
            accept_value = value
        if comments is None and ("observa" in lowered or "comment" in lowered):
            comments = value
    return {
        "sent": "replied",
        "accept": accept_value,
        "comments": comments,
        "submitted_at": response.get("submitted_at"),
    }


async def build_recommendations(db: AsyncSession, fdb: AsyncSession, edict: dict, sub: dict):
    recommender_form_id = _to_int(edict.get("recommenders_forms"))
    if recommender_form_id is None:
        return []
    ids = sub.get("recommender_form_ids") or []
    if isinstance(ids, str):
        ids = json.loads(ids or "[]")
    if not ids:
        return []
    responses = await forms_service.get_form_responses(fdb, recommender_form_id)
    result = []
    for response_id in ids:
        meta = responses.get(response_id)
        if not meta:
            continue
        mapping = await get_mapping(
            db, edict["id"], "recommender", meta.get("form_version") or 1
        )
        resolved = resolve_tree(mapping.get("mapping") if mapping else {}, meta["values"])
        resolved.setdefault("id", response_id)
        resolved.setdefault("email", meta.get("email"))
        resolved.setdefault("submitted_at", meta.get("submitted_at"))
        result.append(resolved)
    return result


def fallback_view(sub: dict):
    """Item mínimo quando a construção completa falha; mantém a listagem íntegra."""
    item = copy.deepcopy(SUMMARY_DEFAULTS)
    item.update(
        {
            "id": sub["id"],
            "token": "",
            "advisor": None,
            "stats": sub["stats"],
            "is_favorite": False,
            "bidding_users": {"data": {}},
            "labels": [],
            "accept": {
                "sent": "not_sent",
                "accept": None,
                "comments": None,
                "submitted_at": None,
            },
        }
    )
    return item


async def _safe_accept_status(fdb: AsyncSession, sub: dict):
    try:
        return await accept_status(fdb, sub)
    except Exception:
        logging.exception("falha ao consultar aceite da inscrição %s", sub.get("id"))
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}


async def build_submission_view(
    db: AsyncSession, fdb: AsyncSession, edict: dict, sub: dict, user: dict
):
    """Monta o dicionário de listagem de uma inscrição."""
    response = None
    mapping = None
    try:
        response = await forms_service.get_response(fdb, sub["candidate_form_id"])
        mapping = await get_mapping(
            db, edict["id"], "candidate", sub["candidate_form_version"]
        )
    except Exception as exc:  # Forms indisponível não pode derrubar a listagem
        logging.exception("falha ao consultar Forms para a inscrição %s", sub["id"])
        response, mapping = None, None
    values = (response or {}).get("values") or {}
    data = build_summary_data(mapping.get("mapping") if mapping else {}, values)

    advisor = None
    if sub.get("advisor_id"):
        advisor_user = await get_user(db, sub["advisor_id"])
        if advisor_user:
            advisor = {
                "id": advisor_user["id"],
                "name": advisor_user["name"],
                "email": advisor_user["email"],
            }

    fav = await db.execute(
        text(
            "select 1 from favorites where user_id = :uid and submission_id = :sid"
        ),
        {"uid": user["id"], "sid": sub["id"]},
    )

    item = dict(data)
    item.update(
        {
            "id": sub["id"],
            "token": (response or {}).get("token") or "",
            "advisor": advisor,
            "stats": sub["stats"],
            "is_favorite": fav.first() is not None,
            "bidding_users": await bidding_users(db, edict["id"], sub["id"]),
            "labels": await user_labels_for(db, user["id"], sub["id"]),
            "accept": await _safe_accept_status(fdb, sub),
        }
    )
    return item
