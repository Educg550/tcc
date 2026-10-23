from datetime import datetime
from pathlib import Path

from sqlalchemy import text

import forms_service as forms
from db import FormsSession, PrejanusSession

UPLOADS = Path("/shared/uploads")


# --- mappings ---

def flatten_mapping(tree, prefix=()):
    """Flatten a mapping tree into {path_tuple: {"section": id, "field": id}}."""
    out = {}
    if not isinstance(tree, dict):
        return out
    for key, value in tree.items():
        if (
            isinstance(value, dict)
            and set(value.keys()) == {"section", "field"}
        ):
            out[prefix + (key,)] = value
        elif isinstance(value, dict):
            out.update(flatten_mapping(value, prefix + (key,)))
    return out


def _leaf_values(tree: dict, values: dict[int, str]) -> dict:
    flat = flatten_mapping(tree)
    return {path: values.get(leaf["field"], "") for path, leaf in flat.items()}


def _get(vmap: dict, *path) -> str:
    return vmap.get(path, "")


def _to_bool(raw: str) -> bool:
    s = (raw or "").strip().lower()
    return s not in ("", "no", "não", "nao", "false", "0")


async def get_mapping(edict_id: int, form_type: str, version: int) -> dict | None:
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text(
                    "select id, edict_id, form_type, mapping, is_active, form_id, user_id, form_version "
                    "from edict_form_mappings where edict_id = :e and form_type = :t "
                    "and form_version = :v and is_active = true"
                ),
                {"e": edict_id, "t": form_type, "v": version},
            )
        ).mappings().first()
    if not row:
        return None
    d = dict(row)
    d["mapping"] = d["mapping"] if isinstance(d["mapping"], dict) else _load_json(d["mapping"])
    return d


def _load_json(value):
    import json

    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return value


async def get_edict(edict_id: int) -> dict | None:
    async with PrejanusSession() as db:
        row = (
            await db.execute(text("select * from edict where id = :i"), {"i": edict_id})
        ).mappings().first()
    return dict(row) if row else None


async def get_submission(submission_id: int) -> dict | None:
    async with PrejanusSession() as db:
        row = (
            await db.execute(text("select * from submission where id = :i"), {"i": submission_id})
        ).mappings().first()
    return dict(row) if row else None


async def get_user(user_id: int) -> dict | None:
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text('select id, name, email, role from "user" where id = :i'), {"i": user_id}
            )
        ).mappings().first()
    return dict(row) if row else None


async def sync_submissions(edict: dict) -> None:
    """Create local submissions for finalized candidate responses not yet registered."""
    form_id = int(edict["candidate_forms"])
    responses = await forms.get_all_form_responses(form_id)
    async with PrejanusSession() as db:
        existing = {
            r.candidate_form_id
            for r in await db.execute(
                text("select candidate_form_id from submission where edict_id = :e"),
                {"e": edict["id"]},
            )
        }
        rec_version = 1
        if edict.get("recommenders_forms"):
            async with FormsSession() as fdb:
                row = (
                    await fdb.execute(
                        text("select version from form where id = :i"),
                        {"i": int(edict["recommenders_forms"])},
                    )
                ).first()
                if row:
                    rec_version = row.version
        for resp in responses:
            if resp["id"] in existing:
                continue
            await db.execute(
                text(
                    "insert into submission (edict_id, candidate_form_id, stats, "
                    "recommender_form_version, candidate_form_version, created_at) "
                    "values (:e, :c, 'underreview', :r, :v, now())"
                ),
                {
                    "e": edict["id"],
                    "c": resp["id"],
                    "r": rec_version,
                    "v": resp["form_version"] or 1,
                },
            )
        await db.commit()


async def get_recommendations(edict: dict, submission: dict, candidate_name: str, candidate_email: str) -> list[dict]:
    """Recommender responses matched to this candidate by candidate data."""
    form_id = edict.get("recommenders_forms")
    if not form_id:
        return []
    form_id = int(form_id)
    mapping = await get_mapping(edict["id"], "recommender", submission["recommender_form_version"])
    responses = await forms.get_all_form_responses(form_id)
    recs = []
    for resp in responses:
        values = await forms.get_responses(resp["id"])
        if mapping:
            vmap = _leaf_values(mapping["mapping"], values)
            rec_name = _get(vmap, "candidate_name") or _get(vmap, "name")
            rec_email = _get(vmap, "candidate_email") or _get(vmap, "email")
        else:
            rec_name = rec_email = ""
        if not rec_name and not rec_email:
            # fallback: match any response value against candidate identity
            joined = " ".join(str(v) for v in values.values())
            if candidate_name and candidate_name.lower() not in joined.lower():
                continue
        else:
            matched = False
            if rec_name and candidate_name and rec_name.strip().lower() == candidate_name.strip().lower():
                matched = True
            if rec_email and candidate_email and rec_email.strip().lower() == candidate_email.strip().lower():
                matched = True
            if not matched:
                continue
        rec = {"id": resp["id"], "email": resp["email"], "submitted_at": resp["submitted_at"]}
        if mapping:
            vmap = _leaf_values(mapping["mapping"], values)
            for path, value in vmap.items():
                rec[path[-1]] = value
        else:
            rec["values"] = list(values.values())
        recs.append(rec)
    return recs


async def build_accept(submission: dict) -> dict:
    accept_form_id = submission.get("accept_form_id")
    if not accept_form_id:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms.get_response_row(accept_form_id)
    if not resp or not resp["submitted_at"]:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values = await forms.get_responses(accept_form_id)
    accept = comments = None
    for value in values.values():
        low = (value or "").strip().lower()
        if low in ("yes", "sim", "accept", "aceito", "true"):
            accept = value
        elif low in ("no", "não", "nao", "decline", "reject"):
            if accept is None:
                accept = value
        elif len(value or "") > 20 and comments is None:
            comments = value
    return {
        "sent": "replied",
        "accept": accept,
        "comments": comments,
        "submitted_at": resp["submitted_at"],
    }


async def submission_labels(submission_id: int) -> list[dict]:
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select id, label, color from labels where submission_id = :s "
                    "and (context_type = 'candidate' or context_type is null) order by id"
                ),
                {"s": submission_id},
            )
        ).mappings().all()
    return [dict(r) for r in rows]


async def bidding_users(submission_id: int, edict_id: int) -> dict:
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select l.user_id, l.label from labels l where l.submission_id = :s "
                    "and l.context_type = 'bidding'"
                ),
                {"s": submission_id},
            )
        ).all()
        slots = {
            r.user_id: (r.slots if r.slots is not None else 0)
            for r in await db.execute(
                text("select user_id, slots from user_edict_slots where edict_id = :e"),
                {"e": edict_id},
            )
        }
    data: dict[str, list] = {}
    for row in rows:
        user = await get_user(row.user_id)
        if not user:
            continue
        data.setdefault(row.label or "", []).append(
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "slots": str(slots.get(user["id"], 0)),
            }
        )
    return {"data": data}


async def build_submission_item(submission: dict, user_id: int) -> dict:
    edict = await get_edict(submission["edict_id"])
    values = await forms.get_responses(submission["candidate_form_id"])
    resp = await forms.get_response_row(submission["candidate_form_id"])
    mapping = await get_mapping(submission["edict_id"], "candidate", submission["candidate_form_version"])
    vmap = _leaf_values(mapping["mapping"], values) if mapping else {}

    def g(*path):
        return _get(vmap, *path)

    advisor = await get_user(submission["advisor_id"]) if submission.get("advisor_id") else None
    async with PrejanusSession() as db:
        fav = (
            await db.execute(
                text(
                    "select 1 from favorites where user_id = :u and submission_id = :s"
                ),
                {"u": user_id, "s": submission["id"]},
            )
        ).first()

    poscomp = None
    if g("poscomp", "year") or g("poscomp", "score"):
        try:
            poscomp = {"year": int(g("poscomp", "year") or 0), "score": g("poscomp", "score")}
        except ValueError:
            poscomp = {"year": 0, "score": g("poscomp", "score")}

    return {
        "id": submission["id"],
        "token": str(resp["token"]) if resp else "",
        "name": g("name"),
        "email": (resp["email"] if resp and resp["email"] else "") or g("email"),
        "phone_number": g("phone_number"),
        "nationality": g("nationality"),
        "personal_website": g("personal_website"),
        "gender": g("gender"),
        "advisor": (
            {"id": advisor["id"], "name": advisor["name"], "email": advisor["email"]} if advisor else None
        ),
        "birth_date": g("birth_date"),
        "graduation": {
            "country": g("graduation", "country"),
            "course": g("graduation", "course"),
            "institution": g("graduation", "institution"),
            "year": _safe_int(g("graduation", "year")),
        },
        "poscomp": poscomp,
        "current_occupation": g("current_occupation") or None,
        "research": {
            "program": g("research", "program"),
            "semester": g("research", "semester"),
            "field": {
                "primary": g("research", "field", "primary"),
                "secondary": g("research", "field", "secondary"),
            },
            "will_apply_scholarship": _to_bool(g("research", "will_apply_scholarship")),
            "dedication_level": g("research", "dedication_level"),
        },
        "lattes_curriculum": g("lattes_curriculum"),
        "stats": submission["stats"],
        "is_favorite": fav is not None,
        "bidding_users": await bidding_users(submission["id"], submission["edict_id"]),
        "labels": await submission_labels(submission["id"]),
        "disabilities": _to_bool(g("disabilities")),
        "ethnicity_race": _to_bool(g("ethnicity_race")),
        "accept": await build_accept(submission),
    }


def _safe_int(raw: str) -> int:
    try:
        return int((raw or "").strip())
    except ValueError:
        return 0


async def build_detail(submission: dict, user_id: int, include_comments: bool = False) -> dict:
    item = await build_submission_item(submission, user_id)
    edict = await get_edict(submission["edict_id"])
    recommendations = await get_recommendations(
        edict, submission, item["name"], item["email"]
    )
    async with PrejanusSession() as db:
        note_row = (
            await db.execute(
                text(
                    "select note from private_note where user_id = :u and submission_id = :s"
                ),
                {"u": user_id, "s": submission["id"]},
            )
        ).first()
        bidding_row = (
            await db.execute(
                text(
                    "select label from labels where user_id = :u and submission_id = :s "
                    "and context_type = 'bidding'"
                ),
                {"u": user_id, "s": submission["id"]},
            )
        ).first()
    summary = dict(item)
    summary["recommendations"] = recommendations
    summary["private_note"] = note_row.note if note_row else ""
    summary["bidding"] = bidding_row.label if bidding_row else ""
    summary["entry_semester"] = submission.get("entry_semester")
    summary["letter_sent"] = submission.get("letter_sent", False)
    if include_comments:
        summary["comments"] = await get_comments(submission["id"])
    return {"summary": summary, "submission_form": await build_submission_form(submission)}


async def build_submission_form(submission: dict) -> list[dict]:
    edict = await get_edict(submission["edict_id"])
    form_id = int(edict["candidate_forms"])
    version = submission["candidate_form_version"]
    values = await forms.get_responses(submission["candidate_form_id"])
    sections = await forms.get_sections(form_id, version)
    fields = await forms.get_form_fields(form_id, version)
    by_section: dict[int, list] = {}
    for f in fields:
        by_section.setdefault(f["section_id"], []).append(f)
    out = []
    for s in sections:
        s_out = {
            "id": s["id"],
            "title": s["title"],
            "description": s["description"],
            "position": s["position"],
            "fields": [],
        }
        for f in by_section.get(s["id"], []):
            s_out["fields"].append(
                {
                    "id": f["id"],
                    "name": f["name"],
                    "label": f["label"],
                    "type": f["type"],
                    "prefix": f["prefix"],
                    "position": f["position"],
                    "value": values.get(f["id"], ""),
                }
            )
        out.append(s_out)
    return out


async def get_comments(submission_id: int) -> list[dict]:
    async with PrejanusSession() as db:
        rows = (
            await db.execute(
                text(
                    "select c.id, c.user_id, c.submission_id, c.comment, c.created_at, c.updated_at "
                    "from comment c where c.submission_id = :s order by c.created_at"
                ),
                {"s": submission_id},
            )
        ).mappings().all()
    out = []
    for r in rows:
        user = await get_user(r["user_id"])
        d = dict(r)
        d["user"] = {"id": user["id"], "name": user["name"]} if user else None
        out.append(d)
    return out


async def find_submission_file(submission: dict, label: str, filename: str) -> Path | None:
    """Locate the upload for field `label`, confirming it belongs to this submission."""
    edict = await get_edict(submission["edict_id"])
    if not edict or not edict.get("candidate_forms"):
        return None
    form_id = int(edict["candidate_forms"])
    values = await forms.get_responses(submission["candidate_form_id"])
    fields = await forms.get_form_fields(form_id)
    field = next((f for f in fields if f["name"] == label), None)
    if field is None:
        return None
    value = values.get(field["id"], "")
    if value != filename:
        return None
    resp = await forms.get_response_row(submission["candidate_form_id"])
    token = str(resp["token"]) if resp else ""
    candidates = [
        UPLOADS / token / filename,
        UPLOADS / filename,
        UPLOADS / str(submission["candidate_form_id"]) / filename,
    ]
    for c in candidates:
        if c.is_file():
            return c
    for c in UPLOADS.rglob(filename):
        if c.is_file():
            return c
    return None
