import json

from sqlalchemy import text

from database import Session
from services import forms_service as forms


def iso(value):
    return value.isoformat() if value is not None else None


def get_edict(edict_id):
    with Session() as s:
        row = s.execute(text("select * from edict where id = :i"), {"i": edict_id}).mappings().first()
        return dict(row) if row else None


def get_submission(submission_id):
    with Session() as s:
        row = s.execute(text("select * from submission where id = :i"), {"i": submission_id}).mappings().first()
        return dict(row) if row else None


def get_mapping(edict_id, form_type, version):
    with Session() as s:
        row = s.execute(
            text(
                "select * from edict_form_mappings"
                " where edict_id = :e and form_type = :t and form_version = :v and is_active"
            ),
            {"e": edict_id, "t": form_type, "v": version},
        ).mappings().first()
        return dict(row) if row else None


def apply_tree(node, values):
    """Resolves a mapping tree against {field_id: value}; None means unmapped."""
    out = {}
    if not isinstance(node, dict):
        return out
    for key, value in node.items():
        if value is None:
            out[key] = None
        elif isinstance(value, dict) and "section" in value and "field" in value:
            out[key] = values.get(value["field"])
        elif isinstance(value, dict):
            out[key] = apply_tree(value, values)
        else:
            out[key] = value
    return out


def _to_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "sim", "yes", "1", "on")


def is_favorite(user_id, submission_id):
    with Session() as s:
        return bool(
            s.execute(
                text("select 1 from favorites where user_id = :u and submission_id = :s"),
                {"u": user_id, "s": submission_id},
            ).first()
        )


def advisor_json(advisor_id):
    if advisor_id is None:
        return None
    with Session() as s:
        row = s.execute(
            text('select id, name, email from "user" where id = :i'), {"i": advisor_id}
        ).mappings().first()
    if not row:
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def submission_labels(submission_id):
    with Session() as s:
        rows = s.execute(
            text(
                "select id, label, color from labels"
                " where submission_id = :s and coalesce(context_type, 'candidate') = 'candidate'"
                " order by id"
            ),
            {"s": submission_id},
        ).mappings().all()
    return [{"id": r["id"], "label": r["label"], "color": r["color"]} for r in rows]


def bidding_users(submission_id, edict_id):
    with Session() as s:
        rows = s.execute(
            text(
                'select l.label, u.id, u.name, u.email from labels l join "user" u on u.id = l.user_id'
                " where l.submission_id = :s and l.context_type = 'bidding' order by u.id"
            ),
            {"s": submission_id},
        ).mappings().all()
        slots = {
            r["user_id"]: r["slots"]
            for r in s.execute(
                text("select user_id, slots from user_edict_slots where edict_id = :e"),
                {"e": edict_id},
            ).mappings().all()
        }
    data = {}
    for r in rows:
        amount = slots.get(r["id"])
        data.setdefault(r["label"], []).append(
            {
                "id": r["id"],
                "name": r["name"],
                "email": r["email"],
                "slots": str(amount) if amount is not None else None,
            }
        )
    return {"data": data}


def accept_status(sub):
    if not sub["accept_form_id"]:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = forms.get_response(sub["accept_form_id"])
    if not resp or not resp["submitted_at"]:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    by_name = {r["name"].lower(): r["value"] for r in forms.get_response_values(sub["accept_form_id"])}
    accept = None
    comments = None
    for name, value in by_name.items():
        if accept is None and ("accept" in name or "decision" in name or "aceite" in name):
            accept = value
        if comments is None and ("comment" in name or "observ" in name):
            comments = value
    return {
        "sent": "replied",
        "accept": accept,
        "comments": comments,
        "submitted_at": iso(resp["submitted_at"]),
    }


def candidate_payload(sub, edict, user_id):
    resp = forms.get_response(sub["candidate_form_id"])
    values = {r["field_id"]: r["value"] for r in forms.get_response_values(sub["candidate_form_id"])}
    mapping = get_mapping(edict["id"], "candidate", sub["candidate_form_version"])
    data = apply_tree(mapping["mapping"], values) if mapping else {}
    grad = data.get("graduation") or {}
    research = data.get("research") or {}
    rfield = research.get("field") or {}
    poscomp = data.get("poscomp")
    if not isinstance(poscomp, dict):
        poscomp = None
    return {
        "id": sub["id"],
        "token": str(resp["token"]) if resp else "",
        "name": data.get("name") or "",
        "email": data.get("email") or ((resp or {}).get("email") or ""),
        "phone_number": data.get("phone_number") or "",
        "nationality": data.get("nationality") or "",
        "personal_website": data.get("personal_website") or "",
        "gender": data.get("gender") or "",
        "advisor": advisor_json(sub["advisor_id"]),
        "birth_date": data.get("birth_date") or "",
        "graduation": {
            "country": grad.get("country") or "",
            "course": grad.get("course") or "",
            "institution": grad.get("institution") or "",
            "year": _to_int(grad.get("year")),
        },
        "poscomp": (
            {"year": _to_int(poscomp.get("year")), "score": str(poscomp.get("score") or "")}
            if poscomp and poscomp.get("year") is not None
            else None
        ),
        "current_occupation": data.get("current_occupation"),
        "research": {
            "program": research.get("program") or "",
            "semester": research.get("semester") or "",
            "field": {
                "primary": rfield.get("primary") or "",
                "secondary": rfield.get("secondary") or "",
            },
            "will_apply_scholarship": _to_bool(research.get("will_apply_scholarship")),
            "dedication_level": research.get("dedication_level") or "",
        },
        "lattes_curriculum": data.get("lattes_curriculum") or "",
        "stats": sub["stats"],
        "is_favorite": is_favorite(user_id, sub["id"]),
        "bidding_users": bidding_users(sub["id"], edict["id"]),
        "labels": submission_labels(sub["id"]),
        "disabilities": _to_bool(data.get("disabilities")),
        "ethnicity_race": _to_bool(data.get("ethnicity_race")),
        "accept": accept_status(sub),
    }


def sync_submissions(edict):
    """Creates local submissions for candidate responses finalized in Forms."""
    try:
        form_id = int(edict["candidate_forms"])
    except (TypeError, ValueError):
        return
    responses = forms.get_submitted_responses(form_id)
    if not responses:
        return
    with Session() as s:
        existing = {
            r[0]
            for r in s.execute(
                text("select candidate_form_id from submission where edict_id = :e"),
                {"e": edict["id"]},
            ).all()
        }
        for resp in responses:
            if resp["id"] in existing:
                continue
            s.execute(
                text(
                    "insert into submission (edict_id, candidate_form_id, candidate_form_version,"
                    " recommender_form_version, stats, created_at, updated_at)"
                    " values (:e, :c, :cv, 1, 'underreview', now(), now())"
                ),
                {"e": edict["id"], "c": resp["id"], "cv": resp["form_version"]},
            )
        s.commit()


def sync_recommendations(edict):
    """Associates recommender responses to submissions using candidate data."""
    try:
        rform = int(edict["recommenders_forms"])
    except (TypeError, ValueError):
        return
    responses = forms.get_submitted_responses(rform)
    if not responses:
        return
    with Session() as s:
        subs = s.execute(
            text("select * from submission where edict_id = :e order by id"),
            {"e": edict["id"]},
        ).mappings().all()
    if not subs:
        return
    targets = []
    for sub in subs:
        sub = dict(sub)
        resp = forms.get_response(sub["candidate_form_id"])
        values = {r["field_id"]: r["value"] for r in forms.get_response_values(sub["candidate_form_id"])}
        mapping = get_mapping(edict["id"], "candidate", sub["candidate_form_version"])
        data = apply_tree(mapping["mapping"], values) if mapping else {}
        email = (data.get("email") or (resp or {}).get("email") or "").strip().lower()
        name = (data.get("name") or "").strip().lower()
        targets.append((sub, email, name))
    for r in responses:
        value_set = {
            (v["value"] or "").strip().lower() for v in forms.get_response_values(r["id"])
        }
        matches = [t for t in targets if t[1] and t[1] in value_set]
        if not matches:
            matches = [t for t in targets if t[2] and t[2] in value_set]
        if len(matches) != 1:
            continue
        sub = matches[0][0]
        ids = set(sub["recommenders_form_ids"] or [])
        if r["id"] in ids:
            continue
        ids.add(r["id"])
        with Session() as s:
            s.execute(
                text(
                    "update submission set recommenders_form_ids = cast(:j as json), updated_at = now()"
                    " where id = :i"
                ),
                {"j": json.dumps(sorted(ids)), "i": sub["id"]},
            )
            s.commit()


def recommendations(sub, edict):
    mapping = get_mapping(edict["id"], "recommender", sub["recommender_form_version"])
    out = []
    for rid in sub["recommenders_form_ids"] or []:
        resp = forms.get_response(rid)
        if not resp:
            continue
        values = {r["field_id"]: r["value"] for r in forms.get_response_values(rid)}
        data = apply_tree(mapping["mapping"], values) if mapping else {}
        out.append(
            {
                "id": rid,
                "submitted_at": iso(resp["submitted_at"]),
                "email": resp["email"],
                "answers": data,
            }
        )
    return out


def submission_form(sub):
    resp = forms.get_response(sub["candidate_form_id"])
    if not resp:
        return []
    sections = forms.select_sections(resp["form_id"], version=sub["candidate_form_version"])
    values = {r["field_id"]: r["value"] for r in forms.get_response_values(sub["candidate_form_id"])}
    out = []
    for sec in sections:
        fields = []
        for f in forms.get_fields(sec["id"]):
            fj = forms.field_json(f)
            fj["value"] = values.get(f["id"])
            fields.append(fj)
        sj = forms.section_json(sec)
        sj["fields"] = fields
        out.append(sj)
    return out


def private_note_of(user_id, submission_id):
    with Session() as s:
        row = s.execute(
            text("select note from private_note where user_id = :u and submission_id = :s"),
            {"u": user_id, "s": submission_id},
        ).mappings().first()
    return row["note"] if row else ""


def submission_summary(sub, edict, user_id):
    summary = dict(candidate_payload(sub, edict, user_id))
    summary["favorite"] = summary["is_favorite"]
    summary["private_note"] = private_note_of(user_id, sub["id"])
    summary["entry_semester"] = sub["entry_semester"] or ""
    summary["semester"] = sub["entry_semester"] or ""
    summary["letter_sent"] = sub["letter_sent"]
    summary["recommendations"] = recommendations(sub, edict)
    return summary


def list_submissions(edict, user_id, stats=None, only_favorites=False):
    sync_submissions(edict)
    sync_recommendations(edict)
    with Session() as s:
        rows = s.execute(
            text("select * from submission where edict_id = :e order by id"),
            {"e": edict["id"]},
        ).mappings().all()
    items = []
    for row in rows:
        sub = dict(row)
        if stats and sub["stats"] != stats:
            continue
        if only_favorites and not is_favorite(user_id, sub["id"]):
            continue
        items.append(candidate_payload(sub, edict, user_id))
    return items
