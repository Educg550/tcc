"""Sincronização e leitura de candidaturas entre Forms e PreJanus."""
import json
import re

from sqlalchemy import text

from .forms_integration import extract_data, get_response, response_values

BIDDING_VALUES = (
    "decline", "available", "interested", "agreed", "interested_scholarship",
)


def get_edict(db, edict_id):
    return db.execute(
        text("SELECT * FROM edict WHERE id = :i"), {"i": edict_id}
    ).mappings().first()


def get_submission(db, submission_id):
    return db.execute(
        text("SELECT * FROM submission WHERE id = :i"), {"i": submission_id}
    ).mappings().first()


def edict_mappings(db, edict_id, form_type) -> dict:
    rows = db.execute(
        text("SELECT form_version, mapping FROM edict_form_mappings "
             "WHERE edict_id = :e AND form_type = CAST(:t AS form_type_enum)"),
        {"e": edict_id, "t": form_type},
    ).mappings().all()
    return {r["form_version"]: r["mapping"] for r in rows}


def pick_mapping(mappings: dict, form_version):
    if not mappings:
        return None
    if form_version in mappings:
        return mappings[form_version]
    return mappings[max(mappings)]


def candidate_data(fdb, db, sub, edict):
    resp = get_response(fdb, sub["candidate_form_id"])
    if resp is None:
        return None, {}
    mapping = pick_mapping(edict_mappings(db, edict["id"], "candidate"), resp["form_version"])
    data = extract_data(response_values(fdb, resp["id"]), mapping) if mapping else {}
    return resp, data


def _norm(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _flatten(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _flatten(v, f"{prefix}{k} ")
    else:
        yield prefix.strip(), node


def _leaf_values(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _leaf_values(value)
    else:
        yield node


def _rec_identifiers(fdb, rr, rec_maps) -> set:
    identifiers = {_norm(rr["email"])}
    md = rr["metadata"] if isinstance(rr["metadata"], dict) else {}
    for value in md.values():
        if isinstance(value, str):
            identifiers.add(_norm(value))
    mapping = pick_mapping(rec_maps, rr["form_version"])
    if mapping:
        data = extract_data(response_values(fdb, rr["id"]), mapping)
        for value in _leaf_values(data):
            if isinstance(value, str):
                identifiers.add(_norm(value))
    identifiers.discard("")
    return identifiers


def _matches(identifiers: set, targets: set) -> bool:
    for value in identifiers:
        for target in targets:
            if value == target:
                return True
            if len(value) >= 5 and len(target) >= 5 and (value in target or target in value):
                return True
    return False


def associate_recommenders(db, fdb, edict) -> None:
    try:
        rec_form = int(edict["recommenders_forms"])
    except (TypeError, ValueError):
        return
    rec_resps = fdb.execute(
        text("SELECT id, email, form_version, metadata FROM form_response WHERE form_id = :f"),
        {"f": rec_form},
    ).mappings().all()
    if not rec_resps:
        return
    rec_maps = edict_mappings(db, edict["id"], "recommender")
    subs = db.execute(
        text("SELECT id, candidate_form_id, recommenders_form_ids FROM submission "
             "WHERE edict_id = :e ORDER BY id"),
        {"e": edict["id"]},
    ).mappings().all()
    for sub in subs:
        if sub["recommenders_form_ids"]:
            continue
        resp, data = candidate_data(fdb, db, sub, edict)
        if resp is None:
            continue
        targets = {
            _norm(data.get("email") or resp["email"]),
            _norm(data.get("name")),
            str(sub["candidate_form_id"]),
            str(resp["token"]),
        }
        for key, value in _flatten(data):
            if "recommend" in key.lower() and isinstance(value, str):
                targets.add(_norm(value))
        targets.discard("")
        ids = [
            rr["id"] for rr in rec_resps
            if _matches(_rec_identifiers(fdb, rr, rec_maps), targets)
        ]
        if ids:
            db.execute(
                text("UPDATE submission SET recommenders_form_ids = CAST(:r AS json), "
                     "updated_at = now() WHERE id = :i"),
                {"r": json.dumps(ids), "i": sub["id"]},
            )


def sync_edict_submissions(db, fdb, edict) -> None:
    try:
        cand_form = int(edict["candidate_forms"])
    except (TypeError, ValueError):
        return
    mappings = edict_mappings(db, edict["id"], "candidate")
    responses = fdb.execute(
        text("SELECT id, form_version FROM form_response "
             "WHERE form_id = :f AND submitted_at IS NOT NULL ORDER BY id"),
        {"f": cand_form},
    ).mappings().all()
    existing = {
        r["candidate_form_id"] for r in db.execute(
            text("SELECT candidate_form_id FROM submission WHERE edict_id = :e"),
            {"e": edict["id"]},
        ).mappings().all()
    }
    rec_version = db.execute(
        text("SELECT coalesce(max(form_version), 1) FROM edict_form_mappings "
             "WHERE edict_id = :e AND form_type = 'recommender'"),
        {"e": edict["id"]},
    ).scalar()
    for resp in responses:
        if resp["id"] in existing or pick_mapping(mappings, resp["form_version"]) is None:
            continue
        db.execute(
            text("INSERT INTO submission (edict_id, created_at, updated_at, "
                 "candidate_form_id, recommenders_form_ids, stats, "
                 "recommender_form_version, candidate_form_version) "
                 "VALUES (:e, now(), now(), :c, CAST(:r AS json), 'underreview', :rv, :cv)"),
            {
                "e": edict["id"], "c": resp["id"], "r": "[]",
                "rv": rec_version, "cv": resp["form_version"],
            },
        )
    associate_recommenders(db, fdb, edict)
    db.commit()


def user_by_id(db, user_id):
    return db.execute(
        text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :i'),
        {"i": user_id},
    ).mappings().first()


def user_slots(db, user_id, edict_id):
    return db.execute(
        text("SELECT slots FROM user_edict_slots WHERE user_id = :u AND edict_id = :e"),
        {"u": user_id, "e": edict_id},
    ).scalar()


_FALSY_EXACT = {"", "false", "no", "não", "nao", "0", "null", "none"}


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().lower()
    return s not in _FALSY_EXACT and not s.startswith(("não", "nao "))


def _norm_date(value):
    if not value:
        return value
    s = str(value).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return s


def _as_int(value):
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return value


def normalize_semester(value: str) -> str:
    v = (value or "").strip().lower()
    if not v:
        return value
    if "primeiro" in v or "first" in v:
        return "Primeiro semestre."
    if "segundo" in v or "second" in v:
        return "Segundo semestre."
    return value


def user_labels_on(db, user_id, submission_id) -> list[dict]:
    rows = db.execute(
        text("SELECT id, label, color FROM labels "
             "WHERE user_id = :u AND submission_id = :s AND context_type = 'candidate' "
             "ORDER BY id"),
        {"u": user_id, "s": submission_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def bidding_users(db, sub, edict) -> dict:
    data = {value: [] for value in BIDDING_VALUES}
    rows = db.execute(
        text("SELECT user_id, label FROM labels "
             "WHERE submission_id = :s AND context_type = 'bidding' ORDER BY id"),
        {"s": sub["id"]},
    ).mappings().all()
    for row in rows:
        user = user_by_id(db, row["user_id"])
        if user is None:
            continue
        slots = user_slots(db, user["id"], edict["id"])
        data.setdefault(row["label"], []).append({
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "slots": str(slots) if slots is not None else None,
        })
    return {"data": data}


def accept_info(fdb, sub) -> dict:
    if not sub["accept_form_id"]:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = get_response(fdb, sub["accept_form_id"])
    if resp is None:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if resp["submitted_at"] is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values = response_values(fdb, resp["id"])
    fields = fdb.execute(
        text("SELECT id, name FROM form_field WHERE form_id = :f"),
        {"f": resp["form_id"]},
    ).mappings().all()
    accept_value = comments_value = None
    for field in fields:
        if field["name"] == "accept":
            accept_value = values.get(field["id"])
        elif field["name"] == "comments":
            comments_value = values.get(field["id"])
    return {
        "sent": "replied",
        "accept": accept_value,
        "comments": comments_value,
        "submitted_at": resp["submitted_at"],
    }


def build_submission_item(db, fdb, sub, edict, user_id) -> dict:
    resp, data = candidate_data(fdb, db, sub, edict)
    resp = resp or {}
    grad = data.get("graduation") or {}
    poscomp = data.get("poscomp")
    research = data.get("research") or {}
    field = research.get("field") or {}
    advisor = user_by_id(db, sub["advisor_id"]) if sub["advisor_id"] else None
    is_favorite = False
    if user_id:
        is_favorite = db.execute(
            text("SELECT 1 FROM favorites WHERE user_id = :u AND submission_id = :s"),
            {"u": user_id, "s": sub["id"]},
        ).first() is not None
    return {
        "id": sub["id"],
        "token": str(resp.get("token", "")),
        "name": data.get("name") or "",
        "email": data.get("email") or resp.get("email") or "",
        "phone_number": data.get("phone_number") or "",
        "nationality": data.get("nationality") or "",
        "personal_website": data.get("personal_website") or "",
        "gender": data.get("gender") or "",
        "advisor": (
            {"id": advisor["id"], "name": advisor["name"], "email": advisor["email"]}
            if advisor else None
        ),
        "birth_date": _norm_date(data.get("birth_date")),
        "graduation": {
            "country": grad.get("country"),
            "course": grad.get("course"),
            "institution": grad.get("institution"),
            "year": _as_int(grad.get("year")),
        },
        "poscomp": (
            {"year": _as_int(poscomp.get("year")), "score": str(poscomp.get("score"))}
            if isinstance(poscomp, dict) and poscomp.get("score") is not None else None
        ),
        "current_occupation": data.get("current_occupation"),
        "research": {
            "program": research.get("program"),
            "semester": research.get("semester"),
            "field": {"primary": field.get("primary"), "secondary": field.get("secondary")},
            "will_apply_scholarship": _to_bool(research.get("will_apply_scholarship")),
            "dedication_level": research.get("dedication_level"),
        },
        "lattes_curriculum": data.get("lattes_curriculum") or "",
        "stats": sub["stats"],
        "is_favorite": bool(is_favorite),
        "bidding_users": bidding_users(db, sub, edict),
        "labels": user_labels_on(db, user_id, sub["id"]) if user_id else [],
        "disabilities": _to_bool(data.get("disabilities")),
        "ethnicity_race": _to_bool(data.get("ethnicity_race")),
        "accept": accept_info(fdb, sub),
    }


def build_summary(db, fdb, sub, edict, user_id) -> dict:
    summary = build_submission_item(db, fdb, sub, edict, user_id)
    recommenders = []
    rec_maps = edict_mappings(db, edict["id"], "recommender")
    for rid in sub["recommenders_form_ids"] or []:
        rr = get_response(fdb, rid)
        if rr is None:
            continue
        mapping = pick_mapping(rec_maps, rr["form_version"])
        rdata = extract_data(response_values(fdb, rid), mapping) if mapping else {}
        recommenders.append({
            "fullname": rdata.get("fullname"),
            "rating": rdata.get("rating"),
            "affiliation": rdata.get("affiliation"),
            "sent": rr["submitted_at"] is not None,
        })
    note = None
    if user_id:
        row = db.execute(
            text("SELECT note FROM private_note WHERE user_id = :u AND submission_id = :s"),
            {"u": user_id, "s": sub["id"]},
        ).first()
        note = row[0] if row else None
    summary.update({
        "entry_semester": sub["entry_semester"],
        "letter_sent": sub["letter_sent"],
        "private_note": note or "",
        "recommenders": recommenders,
    })
    return summary


def build_submission_form(fdb, sub) -> list[dict]:
    from .forms_integration import form_sections, section_fields

    resp = get_response(fdb, sub["candidate_form_id"])
    if resp is None:
        return []
    values = response_values(fdb, resp["id"])
    sections = form_sections(fdb, resp["form_id"], version=resp["form_version"])
    out = []
    for section in sections:
        fields = section_fields(fdb, section["id"], version=resp["form_version"])
        out.append({
            "id": section["id"],
            "form_id": section["form_id"],
            "title": (section["title"] or {}).get("pt"),
            "description": (section["description"] or {}).get("pt"),
            "position": section["position"],
            "is_active": section["is_active"],
            "version": section["version"],
            "fields": [
                {
                    "id": f["id"],
                    "form_id": f["form_id"],
                    "section_id": f["section_id"],
                    "label": (f["label"] or {}).get("pt"),
                    "name": f["name"],
                    "description": (f["description"] or {}).get("pt"),
                    "type": str(f["type"]),
                    "placeholder": f["placeholder"],
                    "required": f["required"],
                    "disabled": f["disabled"],
                    "validation": f["validation"],
                    "error_message": (f["error_message"] or {}).get("pt"),
                    "prefix": f["prefix"],
                    "position": f["position"],
                    "is_active": f["is_active"],
                    "version": f["version"],
                    "value": values.get(f["id"]),
                }
                for f in fields
            ],
        })
    return out
