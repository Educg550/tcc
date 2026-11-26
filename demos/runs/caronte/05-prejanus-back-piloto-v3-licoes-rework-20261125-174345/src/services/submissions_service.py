import json

from ..db import fetch, fetch_one, forms_engine, prejanus_engine, run
from . import forms_service

BIDDING_VALUES = ["decline", "available", "interested", "agreed", "interested_scholarship", ""]


def _s(v) -> str:
    return "" if v is None else str(v)


def _b(v) -> bool:
    t = _s(v).strip().lower()
    if not t:
        return False
    negativos = ("não", "nao", "no", "false", "0", "nenhum", "nenhuma", "nunca")
    return not any(t == n or t.startswith(n + " ") or t.startswith(n + ",") for n in negativos)


def _i(v):
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


async def get_edict(edict_id: int) -> dict | None:
    return await fetch_one(prejanus_engine, "SELECT * FROM edict WHERE id=:i", {"i": edict_id})


async def get_submission(submission_id: int) -> dict | None:
    return await fetch_one(prejanus_engine, "SELECT * FROM submission WHERE id=:i", {"i": submission_id})


async def active_mapping(edict_id: int, form_type: str, version: int | None = None) -> dict | None:
    if version is not None:
        row = await fetch_one(
            prejanus_engine,
            "SELECT * FROM edict_form_mappings WHERE edict_id=:e AND form_type=:t AND form_version=:v "
            "AND is_active ORDER BY form_version DESC, id DESC LIMIT 1",
            {"e": edict_id, "t": form_type, "v": version},
        )
        if row:
            return row
    return await fetch_one(
        prejanus_engine,
        "SELECT * FROM edict_form_mappings WHERE edict_id=:e AND form_type=:t AND is_active "
        "ORDER BY form_version DESC, id DESC LIMIT 1",
        {"e": edict_id, "t": form_type},
    )


def walk_mapping(mapping: dict, values: dict) -> dict:
    def walk(node):
        out = {}
        for key, val in (node or {}).items():
            if val is None:
                out[key] = None
            elif isinstance(val, dict) and isinstance(val.get("field"), int) and isinstance(val.get("section"), int):
                out[key] = values.get(val["field"])
            elif isinstance(val, dict):
                out[key] = walk(val)
            else:
                out[key] = val
        return out

    return walk(mapping)


async def mapped_values(response_id: int, mapping: dict | None) -> dict:
    if not mapping:
        return {}
    values = await forms_service.response_values(response_id)
    return walk_mapping(mapping, values)


async def candidate_mapped(sub: dict) -> dict:
    row = await active_mapping(sub["edict_id"], "candidate", sub["candidate_form_version"])
    return await mapped_values(sub["candidate_form_id"], row["mapping"] if row else {})


async def recommender_mapped(response_id: int, edict_id: int, version: int) -> dict:
    row = await active_mapping(edict_id, "recommender", version)
    return await mapped_values(response_id, row["mapping"] if row else {})


async def ensure_submissions(edict: dict) -> None:
    form_id = int(edict["candidate_forms"])
    rec_map = await active_mapping(edict["id"], "recommender")
    rec_version = rec_map["form_version"] if rec_map else 1
    for resp in await forms_service.submitted_responses(form_id):
        existing = await fetch_one(
            prejanus_engine,
            "SELECT id FROM submission WHERE candidate_form_id=:c AND edict_id=:e",
            {"c": resp["id"], "e": edict["id"]},
        )
        if existing:
            continue
        await run(
            prejanus_engine,
            "INSERT INTO submission (edict_id, candidate_form_id, candidate_form_version, "
            "recommender_form_version, stats, recommenders_form_ids, created_at, updated_at) "
            "VALUES (:e, :c, :cv, :rv, 'underreview', '[]'::json, now(), now())",
            {"e": edict["id"], "c": resp["id"], "cv": resp["form_version"], "rv": rec_version},
        )


async def associate_recommenders(edict: dict) -> None:
    subs = await fetch(
        prejanus_engine,
        "SELECT id, edict_id, candidate_form_id, candidate_form_version, recommender_form_version, "
        "recommenders_form_ids FROM submission WHERE edict_id=:e ORDER BY id",
        {"e": edict["id"]},
    )
    rec_form = int(edict["recommenders_forms"])
    recs = await forms_service.submitted_responses(rec_form)
    used = {rid for s in subs for rid in (s["recommenders_form_ids"] or [])}
    for resp in recs:
        if resp["id"] in used:
            continue
        values = await forms_service.response_values(resp["id"])
        textos = {_s(v).strip().lower() for v in values.values() if _s(v).strip()}
        if not textos:
            continue
        for sub in subs:
            mapped = await candidate_mapped(sub)
            alvos = {_s(mapped.get("name")).strip().lower(), _s(mapped.get("email")).strip().lower()}
            alvos.discard("")
            if alvos & textos:
                ids = list(sub["recommenders_form_ids"] or []) + [resp["id"]]
                await run(
                    prejanus_engine,
                    "UPDATE submission SET recommenders_form_ids=CAST(:r AS json), "
                    "updated_at=now() WHERE id=:i",
                    {"r": json.dumps(ids), "i": sub["id"]},
                )
                used.add(resp["id"])
                break


async def accept_state(sub: dict) -> dict:
    if not sub["accept_form_id"]:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms_service.get_response(sub["accept_form_id"])
    if resp is None:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if resp["submitted_at"] is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values = await forms_service.response_values(resp["id"])
    fields = await fetch(
        forms_engine,
        "SELECT id, name FROM form_field WHERE form_id=:f AND is_active ORDER BY position, id",
        {"f": resp["form_id"]},
    )
    accept = comments = None
    for field in fields:
        value = values.get(field["id"])
        if field["name"] == "accept":
            accept = value
        elif value is not None:
            comments = value
    return {"sent": "replied", "accept": accept, "comments": comments, "submitted_at": resp["submitted_at"]}


async def _advisor(sub: dict) -> dict | None:
    if not sub["advisor_id"]:
        return None
    return await fetch_one(
        prejanus_engine, 'SELECT id, name, email FROM "user" WHERE id=:i', {"i": sub["advisor_id"]}
    )


async def _user_labels(submission_id: int, user_id: int) -> list[dict]:
    return await fetch(
        prejanus_engine,
        "SELECT id, label, color FROM labels WHERE user_id=:u AND submission_id=:s "
        "AND context_type='candidate' ORDER BY id",
        {"u": user_id, "s": submission_id},
    )


async def build_payload(sub: dict, user: dict) -> dict:
    resp = await forms_service.get_response(sub["candidate_form_id"])
    mapped = await candidate_mapped(sub)
    grad = mapped.get("graduation") or {}
    research = mapped.get("research") or {}
    field = research.get("field") or {}
    poscomp = mapped.get("poscomp") or None
    fav = await fetch_one(
        prejanus_engine,
        "SELECT 1 AS x FROM favorites WHERE user_id=:u AND submission_id=:s",
        {"u": user["id"], "s": sub["id"]},
    )
    bids = await fetch(
        prejanus_engine,
        "SELECT l.label, u.id AS uid, u.name, u.email FROM labels l "
        'JOIN "user" u ON u.id = l.user_id '
        "WHERE l.submission_id=:s AND l.context_type='bidding' ORDER BY l.id",
        {"s": sub["id"]},
    )
    data = {v: [] for v in BIDDING_VALUES}
    for b in bids:
        data.setdefault(b["label"], []).append({"id": b["uid"], "name": b["name"], "email": b["email"]})
    return {
        "id": sub["id"],
        "token": str(resp["token"]) if resp else "",
        "name": _s(mapped.get("name")),
        "email": _s(mapped.get("email")) or (resp["email"] if resp else "") or "",
        "phone_number": _s(mapped.get("phone_number")),
        "nationality": _s(mapped.get("nationality")),
        "personal_website": _s(mapped.get("personal_website")),
        "gender": _s(mapped.get("gender")),
        "advisor": await _advisor(sub),
        "birth_date": _s(mapped.get("birth_date")),
        "graduation": {
            "country": _s(grad.get("country")),
            "course": _s(grad.get("course")),
            "institution": _s(grad.get("institution")),
            "year": _i(grad.get("year")),
        },
        "poscomp": ({"year": _i(poscomp.get("year")), "score": poscomp.get("score")} if poscomp else None),
        "current_occupation": mapped.get("current_occupation"),
        "research": {
            "program": _s(research.get("program")),
            "semester": _s(research.get("semester")),
            "field": {"primary": _s(field.get("primary")), "secondary": _s(field.get("secondary"))},
            "will_apply_scholarship": _b(research.get("will_apply_scholarship")),
            "dedication_level": _s(research.get("dedication_level")),
        },
        "lattes_curriculum": _s(mapped.get("lattes_curriculum")),
        "stats": sub["stats"],
        "is_favorite": fav is not None,
        "bidding_users": {"data": data},
        "labels": await _user_labels(sub["id"], user["id"]),
        "disabilities": _b(mapped.get("disabilities")),
        "ethnicity_race": _b(mapped.get("ethnicity_race")),
        "accept": await accept_state(sub),
    }


async def build_summary(sub: dict, user: dict) -> dict:
    resp = await forms_service.get_response(sub["candidate_form_id"])
    mapped = await candidate_mapped(sub)
    grad = mapped.get("graduation") or {}
    research = mapped.get("research") or {}
    field = research.get("field") or {}
    poscomp = mapped.get("poscomp") or None
    recs = []
    for rid in (sub["recommenders_form_ids"] or []):
        rec = await recommender_mapped(rid, sub["edict_id"], sub["recommender_form_version"])
        if "sent" not in rec:
            rec_resp = await forms_service.get_response(rid)
            rec["sent"] = bool(rec_resp and rec_resp["submitted_at"] is not None)
        recs.append(rec)
    note = await fetch_one(
        prejanus_engine,
        "SELECT note FROM private_note WHERE user_id=:u AND submission_id=:s",
        {"u": user["id"], "s": sub["id"]},
    )
    return {
        "id": sub["id"],
        "token": str(resp["token"]) if resp else "",
        "name": _s(mapped.get("name")),
        "email": _s(mapped.get("email")) or (resp["email"] if resp else "") or "",
        "phone_number": _s(mapped.get("phone_number")),
        "birth_date": _s(mapped.get("birth_date")),
        "nationality": _s(mapped.get("nationality")),
        "gender": _s(mapped.get("gender")),
        "personal_website": _s(mapped.get("personal_website")),
        "current_occupation": mapped.get("current_occupation"),
        "lattes_curriculum": _s(mapped.get("lattes_curriculum")),
        "graduation": {
            "country": _s(grad.get("country")),
            "course": _s(grad.get("course")),
            "institution": _s(grad.get("institution")),
            "year": _i(grad.get("year")),
        },
        "poscomp": ({"year": _i(poscomp.get("year")), "score": poscomp.get("score")} if poscomp else None),
        "research": {
            "program": _s(research.get("program")),
            "semester": _s(research.get("semester")),
            "field": {"primary": _s(field.get("primary")), "secondary": _s(field.get("secondary"))},
            "will_apply_scholarship": _b(research.get("will_apply_scholarship")),
            "dedication_level": _s(research.get("dedication_level")),
        },
        "stats": sub["stats"],
        "letter_sent": sub["letter_sent"],
        "private_note": note["note"] if note else "",
        "entry_semester": sub["entry_semester"] or "",
        "recommenders": recs,
        "accept": await accept_state(sub),
        "labels": await _user_labels(sub["id"], user["id"]),
        "advisor": await _advisor(sub),
        "disabilities": _b(mapped.get("disabilities")),
        "ethnicity_race": _b(mapped.get("ethnicity_race")),
    }


async def submission_sections(sub: dict) -> list[dict]:
    resp = await forms_service.get_response(sub["candidate_form_id"])
    if resp:
        form_id = resp["form_id"]
    else:
        edict = await get_edict(sub["edict_id"])
        form_id = int(edict["candidate_forms"])
    sections = await forms_service.form_sections(form_id, sub["candidate_form_version"])
    values = await forms_service.response_values(sub["candidate_form_id"])
    out = []
    for section in sections:
        fields = await forms_service.section_fields(section["id"])
        out.append({**section, "fields": [{**f, "value": values.get(f["id"])} for f in fields]})
    return out
