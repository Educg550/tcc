import json

from sqlalchemy import text

from services import forms_service
from services.common import get_user_row, parse_form_ids, user_brief


def flatten_mapping(node, prefix=()):
    out = {}
    if not isinstance(node, dict):
        return out
    for key, value in node.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(value.get("section"), int) and isinstance(value.get("field"), int):
            out[".".join(prefix + (key,))] = value
        elif isinstance(value, dict):
            out.update(flatten_mapping(value, prefix + (key,)))
    return out


def get_mapping(ps, edict_id, form_type, version):
    row = ps.execute(
        text(
            "select mapping from edict_form_mappings "
            "where edict_id=:e and form_type=:t and form_version=:v and is_active=true"
        ),
        {"e": edict_id, "t": form_type, "v": version},
    ).first()
    if not row:
        row = ps.execute(
            text(
                "select mapping from edict_form_mappings "
                "where edict_id=:e and form_type=:t and is_active=true "
                "order by form_version desc limit 1"
            ),
            {"e": edict_id, "t": form_type},
        ).first()
    return row[0] if row else {}


class Getter:
    def __init__(self, mapping, values):
        self.flat = flatten_mapping(mapping or {})
        self.values = values or {}

    def get(self, *path):
        key = ".".join(path)
        leaf = self.flat.get(key)
        if leaf is None:
            for prop, candidate in self.flat.items():
                if prop.endswith("." + key):
                    leaf = candidate
                    break
        if leaf is None:
            return None
        return self.values.get(leaf["field"])


def _to_bool(value):
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "yes", "sim", "1", "verdadeiro")


def _to_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def candidate_getter(ps, fs, sub, edict):
    values = forms_service.get_values(fs, sub["candidate_form_id"])
    mapping = get_mapping(ps, edict["id"], "candidate", sub["candidate_form_version"])
    return Getter(mapping, values)


def sync_submissions(ps, fs, edict):
    for form_id in parse_form_ids(edict["candidate_forms"]):
        rows = fs.execute(
            text("select id, form_version from form_response where form_id=:f and submitted_at is not null"),
            {"f": form_id},
        ).mappings().all()
        for row in rows:
            exists = ps.execute(
                text("select 1 from submission where candidate_form_id=:c and edict_id=:e"),
                {"c": row["id"], "e": edict["id"]},
            ).first()
            if not exists:
                ps.execute(
                    text(
                        "insert into submission (edict_id, created_at, updated_at, candidate_form_id, "
                        "recommenders_form_ids, stats, recommender_form_version, candidate_form_version) "
                        "values (:e, now(), now(), :c, '[]'::json, 'underreview', 1, :v)"
                    ),
                    {"e": edict["id"], "c": row["id"], "v": row["form_version"] or 1},
                )
    ps.commit()


def sync_recommenders(ps, fs, edict):
    rec_form_ids = parse_form_ids(edict["recommenders_forms"])
    if not rec_form_ids:
        return
    subs = ps.execute(
        text("select * from submission where edict_id=:e order by id"), {"e": edict["id"]}
    ).mappings().all()
    if not subs:
        return
    info = []
    for sub in subs:
        resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
        getter = candidate_getter(ps, fs, sub, edict)
        info.append((sub, getter.get("name") or "", (resp["email"] if resp else "") or ""))
    for form_id in rec_form_ids:
        rows = fs.execute(
            text("select id, metadata from form_response where form_id=:f and submitted_at is not null"),
            {"f": form_id},
        ).mappings().all()
        for row in rows:
            values = forms_service.get_values(fs, row["id"])
            blob = " ".join(str(v) for v in values.values() if v)
            blob += " " + json.dumps(row["metadata"] or {})
            targets = [t for t in info if t[2] and t[2] in blob]
            if not targets:
                named = [t for t in info if t[1] and len(t[1]) > 3 and t[1] in blob]
                if len(named) == 1:
                    targets = named
            if len(targets) == 1:
                sub = targets[0][0]
                current = sub["recommenders_form_ids"] or []
                if isinstance(current, str):
                    current = json.loads(current)
                if row["id"] not in current:
                    current.append(row["id"])
                    ps.execute(
                        text("update submission set recommenders_form_ids=:r, updated_at=now() where id=:i"),
                        {"r": json.dumps(current), "i": sub["id"]},
                    )
    ps.commit()


def accept_info(fs, sub):
    base = {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if not sub["accept_form_id"]:
        return base
    row = fs.execute(
        text("select id, submitted_at from form_response where id=:i"), {"i": sub["accept_form_id"]}
    ).first()
    if not row:
        return base
    if row[1]:
        values = fs.execute(
            text(
                "select r.value from responses r join form_field f on f.id = r.field_id "
                'where r.response_id=:i order by f."position", f.id'
            ),
            {"i": sub["accept_form_id"]},
        ).scalars().all()
        filled = [v for v in values if v]
        return {
            "sent": "replied",
            "accept": filled[0] if filled else None,
            "comments": filled[1] if len(filled) > 1 else None,
            "submitted_at": row[1].isoformat(),
        }
    return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}


def build_bidding_users(ps, sub, edict):
    rows = ps.execute(
        text(
            'select u.id, u.name, u.email from labels l join "user" u on u.id = l.user_id '
            "where l.submission_id=:s and l.context_type='bidding' order by u.id"
        ),
        {"s": sub["id"]},
    ).mappings().all()
    out = []
    for row in rows:
        slots = ps.execute(
            text("select slots from user_edict_slots where user_id=:u and edict_id=:e"),
            {"u": row["id"], "e": edict["id"]},
        ).scalar()
        out.append(
            {"id": row["id"], "name": row["name"], "email": row["email"], "slots": str(slots) if slots is not None else "0"}
        )
    return out


def build_submission(ps, fs, sub, edict, user_id):
    resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
    getter = candidate_getter(ps, fs, sub, edict)
    name = getter.get("name") or ""
    email = getter.get("email") or (resp["email"] if resp else "") or ""
    advisor = user_brief(get_user_row(ps, sub["advisor_id"])) if sub["advisor_id"] else None
    labels = ps.execute(
        text(
            "select id, label, color from labels where submission_id=:s and context_type='candidate' order by id"
        ),
        {"s": sub["id"]},
    ).mappings().all()
    favorite = ps.execute(
        text("select 1 from favorites where user_id=:u and submission_id=:s"),
        {"u": user_id, "s": sub["id"]},
    ).first()
    return {
        "id": sub["id"],
        "token": str(resp["token"]) if resp and resp["token"] else "",
        "name": name,
        "email": email,
        "phone_number": getter.get("phone_number") or "",
        "nationality": getter.get("nationality") or "",
        "personal_website": getter.get("personal_website") or "",
        "gender": getter.get("gender") or "",
        "advisor": advisor,
        "birth_date": getter.get("birth_date") or "",
        "graduation": {
            "country": getter.get("country") or "",
            "course": getter.get("course") or "",
            "institution": getter.get("institution") or "",
            "year": _to_int(getter.get("year")),
        },
        "poscomp": (
            {"year": _to_int(getter.get("poscomp", "year")), "score": getter.get("score") or ""}
            if (getter.get("poscomp", "year") or getter.get("score"))
            else None
        ),
        "current_occupation": getter.get("current_occupation"),
        "research": {
            "program": getter.get("program") or "",
            "semester": getter.get("semester") or "",
            "field": {"primary": getter.get("primary") or "", "secondary": getter.get("secondary") or ""},
            "will_apply_scholarship": _to_bool(getter.get("will_apply_scholarship")),
            "dedication_level": getter.get("dedication_level") or "",
        },
        "lattes_curriculum": getter.get("lattes_curriculum") or "",
        "stats": sub["stats"],
        "is_favorite": favorite is not None,
        "bidding_users": {"data": build_bidding_users(ps, sub, edict)},
        "labels": [{"id": l["id"], "label": l["label"], "color": l["color"]} for l in labels],
        "disabilities": _to_bool(getter.get("disabilities")),
        "ethnicity_race": _to_bool(getter.get("ethnicity_race")),
        "accept": accept_info(fs, sub),
    }


def build_recommendations(fs, sub):
    out = []
    ids = sub["recommenders_form_ids"] or []
    if isinstance(ids, str):
        ids = json.loads(ids)
    for rid in ids:
        resp = forms_service.get_form_response(fs, rid)
        out.append(
            {
                "id": rid,
                "email": resp["email"] if resp else None,
                "submitted_at": resp["submitted_at"].isoformat() if resp and resp["submitted_at"] else None,
            }
        )
    return out


def build_summary(ps, fs, sub, edict, user_id, include_comments=False):
    summary = build_submission(ps, fs, sub, edict, user_id)
    note = ps.execute(
        text("select note from private_note where user_id=:u and submission_id=:s"),
        {"u": user_id, "s": sub["id"]},
    ).scalar()
    summary["favorite"] = summary["is_favorite"]
    summary["private_note"] = note or ""
    summary["entry_semester"] = sub["entry_semester"] or ""
    summary["letter_sent"] = sub["letter_sent"]
    summary["recommendations"] = build_recommendations(fs, sub)
    if include_comments:
        rows = ps.execute(
            text(
                'select c.*, u.name as user_name from comment c join "user" u on u.id = c.user_id '
                "where c.submission_id=:s order by c.created_at, c.id"
            ),
            {"s": sub["id"]},
        ).mappings().all()
        summary["comments"] = [
            {
                "id": r["id"],
                "user": {"id": r["user_id"], "name": r["user_name"]},
                "comment": r["comment"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    return summary


def build_submission_form(fs, sub):
    resp = forms_service.get_form_response(fs, sub["candidate_form_id"])
    if not resp:
        return []
    values = forms_service.get_values(fs, sub["candidate_form_id"])
    sections = fs.execute(
        text('select * from form_section where form_id=:f order by "position", id'),
        {"f": resp["form_id"]},
    ).mappings().all()
    fields_by_section = {}
    for field in forms_service.get_all_fields(fs, resp["form_id"]):
        fields_by_section.setdefault(field["section_id"], []).append(
            forms_service.field_dict(field, values.get(field["id"]))
        )
    out = []
    for section in sections:
        entry = forms_service.section_dict(section)
        entry["fields"] = fields_by_section.get(section["id"], [])
        out.append(entry)
    return out
