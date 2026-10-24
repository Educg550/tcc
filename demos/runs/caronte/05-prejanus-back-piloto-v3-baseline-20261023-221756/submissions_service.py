import json
import unicodedata

from sqlalchemy import text

import forms_service as forms
from forms_service import _label
from mapping_utils import (build_candidate_payload, extract_candidate, extract_recommender,
                           flat_values)


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


async def get_edict(psession, edict_id):
    row = (await psession.execute(text("select * from edict where id = :i"), {"i": edict_id})).mappings().first()
    return dict(row) if row else None


async def get_submission(psession, submission_id):
    row = (await psession.execute(text("select * from submission where id = :i"), {"i": submission_id})).mappings().first()
    return dict(row) if row else None


async def get_mapping(psession, edict_id, form_type, version=None):
    q = ("select * from edict_form_mappings where edict_id = :e and form_type = :t and is_active = true")
    params = {"e": edict_id, "t": form_type}
    if version is not None:
        row = (await psession.execute(text(q + " and form_version = :v"), {**params, "v": version})).mappings().first()
        if row:
            return dict(row)
    row = (await psession.execute(text(q + " order by form_version desc limit 1"), params)).mappings().first()
    return dict(row) if row else None


async def sync_submissions(psession, fsession, edict):
    """Ensure a local submission exists for each finalized candidate response."""
    cand_form = int(edict["candidate_forms"])
    responses = await forms.get_submitted_responses(cand_form)
    subs = {}
    for r in responses:
        row = (await psession.execute(
            text("select * from submission where edict_id = :e and candidate_form_id = :c"),
            {"e": edict["id"], "c": r["id"]})).mappings().first()
        if row is None:
            await psession.execute(text(
                "insert into submission (edict_id, candidate_form_id, recommenders_form_ids, stats, "
                "recommender_form_version, candidate_form_version, created_at, updated_at) "
                "values (:e, :c, '[]'::json, 'underreview', 1, :v, now(), now())"),
                {"e": edict["id"], "c": r["id"], "v": r["form_version"]})
            await psession.commit()
            row = (await psession.execute(
                text("select * from submission where edict_id = :e and candidate_form_id = :c"),
                {"e": edict["id"], "c": r["id"]})).mappings().first()
        subs[r["id"]] = dict(row)
    return responses, subs


async def associate_recommendations(psession, fsession, edict, responses, subs):
    """Link recommender responses to submissions using candidate data; never mix candidates."""
    rec_form = int(edict["recommenders_forms"])
    recs = await forms.get_submitted_responses(rec_form)
    if not recs:
        return
    mapping = await get_mapping(psession, edict["id"], "recommender")
    by_email = {}
    by_name = {}
    for resp_id, sub in subs.items():
        cand = responses_lookup(responses, resp_id)
        if cand and cand.get("email"):
            by_email[cand["email"].strip().lower()] = sub
        payload = await candidate_payload(psession, fsession, edict, sub)
        if payload.get("name"):
            by_name[payload["name"].strip().lower()] = sub
    for rec in recs:
        values = await forms.get_response_values(rec["id"])
        flat = flat_values(mapping["mapping"], values) if mapping else {}
        data = extract_recommender(flat)
        target = None
        cand_email = data.get("candidate_email") or _metadata_email(rec.get("metadata"))
        if cand_email:
            target = by_email.get(str(cand_email).strip().lower())
        if target is None and data.get("candidate_name"):
            target = by_name.get(str(data["candidate_name"]).strip().lower())
        if target is None:
            continue
        ids = target.get("recommenders_form_ids") or []
        if isinstance(ids, str):
            ids = json.loads(ids)
        if rec["id"] not in ids:
            ids.append(rec["id"])
        await psession.execute(text(
            "update submission set recommenders_form_ids = :r, recommender_form_version = :v, "
            "updated_at = now() where id = :i"),
            {"r": json.dumps(ids), "v": rec["form_version"], "i": target["id"]})
        target["recommenders_form_ids"] = ids
        target["recommender_form_version"] = rec["form_version"]
    await psession.commit()


def responses_lookup(responses, resp_id):
    for r in responses:
        if r["id"] == resp_id:
            return r
    return None


def _metadata_email(metadata):
    if not isinstance(metadata, dict):
        return None
    for k, v in metadata.items():
        if "email" in _norm(k) and isinstance(v, str):
            return v
    return None


async def candidate_payload(psession, fsession, edict, sub):
    values = await forms.get_response_values(sub["candidate_form_id"])
    mapping = await get_mapping(psession, edict["id"], "candidate", sub["candidate_form_version"])
    flat = flat_values(mapping["mapping"], values) if mapping else {}
    return build_candidate_payload(extract_candidate(flat))


async def get_recommendations(psession, fsession, edict, sub):
    ids = sub.get("recommenders_form_ids") or []
    if isinstance(ids, str):
        ids = json.loads(ids)
    mapping = await get_mapping(psession, edict["id"], "recommender", sub["recommender_form_version"])
    result = []
    for rid in ids:
        resp = await forms.get_response(rid)
        if not resp:
            continue
        values = await forms.get_response_values(rid)
        flat = flat_values(mapping["mapping"], values) if mapping else {}
        data = extract_recommender(flat)
        result.append({
            "id": rid,
            "name": str(data.get("name") or ""),
            "email": str(data.get("email") or ""),
            "text": str(data.get("text") or ""),
            "submitted_at": resp["submitted_at"],
        })
    return result


async def accept_info(fsession, sub):
    if not sub.get("accept_form_id"):
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms.get_response(sub["accept_form_id"])
    if not resp or not resp.get("submitted_at"):
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values = await forms.get_response_values(sub["accept_form_id"])
    fields = (await fsession.execute(
        text("select id, name, label from form_field where form_id = :f"),
        {"f": resp["form_id"]})).mappings().all()
    accept_value = None
    comments = None
    for f in fields:
        v = values.get(f["id"])
        if v is None:
            continue
        label = _norm(f["name"] + " " + str((f["label"] or {}).get("pt", "")))
        if accept_value is None and ("accept" in label or "decision" in label or "aceite" in label):
            accept_value = v
        elif comments is None and ("comment" in label or "observation" in label or "observac" in label):
            comments = v
    return {"sent": "replied", "accept": accept_value, "comments": comments,
            "submitted_at": resp["submitted_at"]}


async def bidding_users(psession, sub):
    rows = (await psession.execute(text(
        "select l.label, u.id, u.name, u.email, s.slots from labels l "
        'join "user" u on u.id = l.user_id '
        "left join user_edict_slots s on s.user_id = l.user_id and s.edict_id = "
        "(select edict_id from submission where id = :i) "
        "where l.submission_id = :i and l.context_type = 'bidding'"),
        {"i": sub["id"]})).mappings().all()
    data = {}
    for r in rows:
        data.setdefault(r["label"], []).append({
            "id": r["id"], "name": r["name"], "email": r["email"],
            "slots": str(r["slots"]) if r["slots"] is not None else None,
        })
    return {"data": data}


async def submission_labels(psession, sub):
    rows = (await psession.execute(text(
        "select id, label, color from labels where submission_id = :i "
        "and (context_type = 'candidate' or context_type is null) order by id"),
        {"i": sub["id"]})).all()
    return [{"id": r[0], "label": r[1], "color": r[2]} for r in rows]


async def user_bidding(psession, sub, user_id):
    row = (await psession.execute(text(
        "select label from labels where submission_id = :i and user_id = :u and context_type = 'bidding'"),
        {"i": sub["id"], "u": user_id})).scalar()
    return row


async def is_favorite(psession, sub, user_id):
    row = (await psession.execute(text(
        "select 1 from favorites where submission_id = :i and user_id = :u"),
        {"i": sub["id"], "u": user_id})).scalar()
    return row is not None


async def advisor_info(psession, sub):
    if not sub.get("advisor_id"):
        return None
    row = (await psession.execute(text('select id, name, email from "user" where id = :i'),
                                   {"i": sub["advisor_id"]})).mappings().first()
    return dict(row) if row else None


async def build_submission_item(psession, fsession, edict, sub, user_id):
    payload = await candidate_payload(psession, fsession, edict, sub)
    payload.update({
        "id": sub["id"],
        "token": (await forms.get_response(sub["candidate_form_id"]) or {}).get("token", ""),
        "advisor": await advisor_info(psession, sub),
        "stats": sub["stats"],
        "is_favorite": await is_favorite(psession, sub, user_id),
        "bidding_users": await bidding_users(psession, sub),
        "labels": await submission_labels(psession, sub),
        "accept": await accept_info(fsession, sub),
    })
    return payload


async def build_detail(psession, fsession, edict, sub, user_id, include_comments=False):
    item = await build_submission_item(psession, fsession, edict, sub, user_id)
    note = (await psession.execute(text(
        "select note from private_note where submission_id = :i and user_id = :u"),
        {"i": sub["id"], "u": user_id})).scalar()
    item.update({
        "recommendations": await get_recommendations(psession, fsession, edict, sub),
        "private_note": note or "",
        "entry_semester": sub.get("entry_semester"),
        "letter_sent": sub.get("letter_sent", False),
        "bidding": await user_bidding(psession, sub, user_id),
    })
    cand = await forms.get_response(sub["candidate_form_id"])
    if cand and cand.get("email"):
        item["email"] = cand["email"]
    if include_comments:
        item["comments"] = await list_comments(psession, sub["id"])
    return item


async def list_comments(psession, submission_id):
    rows = (await psession.execute(text(
        "select c.id, c.comment, c.created_at, c.updated_at, u.id as uid, u.name as uname "
        'from comment c join "user" u on u.id = c.user_id where c.submission_id = :i order by c.created_at'),
        {"i": submission_id})).mappings().all()
    return [{"id": r["id"], "user": {"id": r["uid"], "name": r["uname"]}, "comment": r["comment"],
             "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]


async def build_submission_form(fsession, sub):
    """All sections and fields of the registered version, with the answered values."""
    sections = await forms.get_sections(sub["candidate_form_id"], sub["candidate_form_version"])
    values = await forms.get_response_values(sub["candidate_form_id"])
    out = []
    for sec in sections:
        fields = await forms.get_fields(sec["id"], sub["candidate_form_version"])
        out.append({
            "id": sec["id"],
            "title": _label(sec["title"]),
            "description": _label(sec["description"]),
            "position": sec["position"],
            "fields": [
                {"id": f["id"], "name": f["name"], "label": _label(f["label"]), "type": f["type"],
                 "prefix": f["prefix"], "position": f["position"], "required": f["required"],
                 "value": values.get(f["id"])}
                for f in fields
            ],
        })
    return {"sections": out}
