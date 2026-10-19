import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import services.forms_service as forms_service
from models import (
    Edict,
    EdictFormMapping,
    Label,
    Submission,
    User,
    UserEdictSlot,
)
from services.mapping import build_candidate_values, extract_values


def _now():
    return datetime.now(timezone.utc)


async def get_mapping(db: AsyncSession, edict: Edict, form_type: str, version: int | None = None):
    stmt = select(EdictFormMapping).where(
        EdictFormMapping.edict_id == edict.id,
        EdictFormMapping.form_type == form_type,
        EdictFormMapping.is_active.is_(True),
    )
    if version is not None:
        stmt = stmt.where(EdictFormMapping.form_version == version)
        mapping = (await db.execute(stmt)).scalars().first()
        if mapping is not None:
            return mapping
        return None
    mappings = (await db.execute(stmt.order_by(EdictFormMapping.form_version.desc()))).scalars().all()
    return mappings[0] if mappings else None


async def get_mapping_or_latest(db: AsyncSession, edict: Edict, form_type: str, version: int):
    mapping = await get_mapping(db, edict, form_type, version)
    if mapping is not None:
        return mapping
    return await get_mapping(db, edict, form_type, None)


async def sync_edict_submissions(db: AsyncSession, edict: Edict) -> list[Submission]:
    """Ensures local submissions exist for every finalized candidate response."""
    try:
        candidate_form_id = int(edict.candidate_forms)
    except (TypeError, ValueError):
        return []
    responses = await forms_service.get_form_responses(candidate_form_id)
    submitted = [r for r in responses if r["submitted_at"] is not None]

    subs = (
        await db.execute(select(Submission).where(Submission.edict_id == edict.id))
    ).scalars().all()
    by_form = {s.candidate_form_id: s for s in subs}

    rec_mapping = await get_mapping(db, edict, "recommender")
    rec_version = rec_mapping.form_version if rec_mapping else 1

    changed = False
    for resp in submitted:
        sub = by_form.get(resp["id"])
        if sub is None:
            sub = Submission(
                edict_id=edict.id,
                candidate_form_id=resp["id"],
                candidate_form_version=resp["form_version"],
                recommender_form_version=rec_version,
                stats="underreview",
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(sub)
            by_form[resp["id"]] = sub
            changed = True
        elif sub.candidate_form_version != resp["form_version"]:
            sub.candidate_form_version = resp["form_version"]
            changed = True
    if changed:
        await db.commit()
        await db.refresh(edict)

    subs = (
        await db.execute(select(Submission).where(Submission.edict_id == edict.id))
    ).scalars().all()
    await associate_recommenders(db, edict, subs)
    return subs


async def associate_recommenders(db: AsyncSession, edict: Edict, subs: list[Submission]) -> None:
    try:
        recommender_form_id = int(edict.recommenders_forms)
    except (TypeError, ValueError):
        return
    rec_responses = await forms_service.get_form_responses(recommender_form_id)
    rec_submitted = [r for r in rec_responses if r["submitted_at"] is not None]
    if not rec_submitted:
        return
    rec_answers = await forms_service.get_answers([r["id"] for r in rec_submitted])

    changed = False
    for sub in subs:
        mapping = await get_mapping_or_latest(db, edict, "candidate", sub.candidate_form_version)
        candidate_answers = (await forms_service.get_answers([sub.candidate_form_id])).get(
            sub.candidate_form_id, {}
        )
        if mapping is not None:
            values = extract_values(mapping.mapping, candidate_answers)
            cand = build_candidate_values(values)
        else:
            cand = {"name": "", "email": ""}
        email = (cand.get("email") or "").strip().lower()
        name = (cand.get("name") or "").strip().lower()
        matched = []
        for resp in rec_submitted:
            answers = rec_answers.get(resp["id"], {})
            answer_values = {str(v or "").strip().lower() for v in answers.values()}
            if (email and email in answer_values) or (name and name in answer_values):
                matched.append(resp["id"])
        current = sub.recommenders_form_ids or []
        if set(current) != set(matched):
            sub.recommenders_form_ids = matched
            sub.updated_at = _now()
            changed = True
    if changed:
        await db.commit()


async def load_submission_context(db: AsyncSession, edict: Edict, sub: Submission) -> dict:
    """Loads Forms response, answers and mapped values for a local submission."""
    response = await forms_service.get_response(sub.candidate_form_id)
    answers = (
        (await forms_service.get_answers([sub.candidate_form_id])).get(sub.candidate_form_id, {})
        if response
        else {}
    )
    mapping = await get_mapping_or_latest(db, edict, "candidate", sub.candidate_form_version)
    values = extract_values(mapping.mapping, answers) if mapping else {}
    cand = build_candidate_values(values)
    return {"response": response, "answers": answers, "mapping": mapping, "values": cand}


async def accept_status(sub: Submission) -> dict:
    if not sub.accept_form_id:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms_service.get_response(sub.accept_form_id)
    if resp is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    if resp["submitted_at"] is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    fields = await forms_service.get_form_fields(resp["form_id"])
    answers = (await forms_service.get_answers([resp["id"]])).get(resp["id"], {})
    accept_val = None
    comments_val = None
    for field in fields:
        value = answers.get(field["id"])
        if value is None:
            continue
        label = field["label"] if isinstance(field["label"], dict) else {}
        blob = ((field["name"] or "") + " " + str(label.get("pt", ""))).lower()
        if accept_val is None and ("accept" in blob or "aceit" in blob or "decision" in blob):
            accept_val = value
        elif comments_val is None and ("comment" in blob or "observ" in blob):
            comments_val = value
    return {
        "sent": "replied",
        "accept": accept_val,
        "comments": comments_val,
        "submitted_at": resp["submitted_at"],
    }


async def bidding_users_for(db: AsyncSession, edict: Edict, sub: Submission) -> dict:
    rows = (
        await db.execute(
            select(Label, User).join(User, User.id == Label.user_id).where(
                Label.submission_id == sub.id,
                Label.context_type == "bidding",
            )
        )
    ).all()
    slots_rows = (
        await db.execute(
            select(UserEdictSlot).where(UserEdictSlot.edict_id == edict.id)
        )
    ).scalars().all()
    slots_by_user = {s.user_id: s.slots for s in slots_rows}
    data: dict[str, list[dict]] = {}
    for label, user in rows:
        data.setdefault(label.label, []).append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "slots": str(slots_by_user.get(user.id) or 0),
            }
        )
    return {"data": data}


async def labels_for(db: AsyncSession, sub: Submission) -> list[dict]:
    rows = (
        await db.execute(
            select(Label).where(
                Label.submission_id == sub.id, Label.context_type == "candidate"
            )
        )
    ).scalars().all()
    return [{"id": l.id, "label": l.label, "color": l.color} for l in rows]


async def user_bidding(db: AsyncSession, sub: Submission, user_id: int) -> str:
    row = (
        await db.execute(
            select(Label).where(
                Label.submission_id == sub.id,
                Label.user_id == user_id,
                Label.context_type == "bidding",
            )
        )
    ).scalars().first()
    return row.label if row else ""


async def build_submission_item(
    db: AsyncSession, edict: Edict, sub: Submission, user: User, context: dict
) -> dict:
    cand = context["values"]
    response = context["response"]
    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    from models import Favorite

    is_favorite_row = (
        await db.execute(
            select(Favorite).where(
                Favorite.submission_id == sub.id, Favorite.user_id == user.id
            )
        )
    ).scalars().first()
    item = {
        "id": sub.id,
        "token": str(response["token"]) if response else "",
        "name": cand["name"],
        "email": cand["email"],
        "phone_number": cand["phone_number"],
        "nationality": cand["nationality"],
        "personal_website": cand["personal_website"],
        "gender": cand["gender"],
        "advisor": (
            {"id": advisor.id, "name": advisor.name, "email": advisor.email} if advisor else None
        ),
        "birth_date": cand["birth_date"],
        "graduation": cand["graduation"],
        "poscomp": cand["poscomp"],
        "current_occupation": cand["current_occupation"],
        "research": cand["research"],
        "lattes_curriculum": cand["lattes_curriculum"],
        "stats": sub.stats,
        "is_favorite": is_favorite_row is not None,
        "bidding_users": await bidding_users_for(db, edict, sub),
        "labels": await labels_for(db, sub),
        "disabilities": cand["disabilities"],
        "ethnicity_race": cand["ethnicity_race"],
        "accept": await accept_status(sub),
    }
    return item


async def build_submission_form(sub: Submission, context: dict) -> dict:
    response = context["response"]
    if response is None:
        return {"form_id": None, "sections": []}
    form = await forms_service.get_form(response["form_id"])
    sections_out = []
    for section in await forms_service.get_sections(response["form_id"], sub.candidate_form_version):
        fields = await forms_service.get_fields(section["id"], sub.candidate_form_version)
        title = section["title"] if isinstance(section["title"], dict) else {}
        fields_out = []
        for field in fields:
            label = field["label"] if isinstance(field["label"], dict) else {}
            fields_out.append(
                {
                    "id": field["id"],
                    "name": field["name"],
                    "label": label.get("pt") or label.get("en") or "",
                    "type": field["type"],
                    "prefix": field["prefix"],
                    "position": field["position"],
                    "value": context["answers"].get(field["id"]),
                }
            )
        sections_out.append(
            {
                "id": section["id"],
                "title": title.get("pt") or title.get("en") or "",
                "position": section["position"],
                "fields": fields_out,
            }
        )
    return {"form_id": response["form_id"], "sections": sections_out}


async def build_recommendations(sub: Submission) -> list[dict]:
    ids = sub.recommenders_form_ids or []
    if not ids:
        return []
    out = []
    answers_map = await forms_service.get_answers(ids)
    for rid in ids:
        resp = await forms_service.get_response(rid)
        if resp is None:
            continue
        fields = await forms_service.get_form_fields(resp["form_id"])
        answers = answers_map.get(rid, {})
        responses = {}
        for field in fields:
            if field["id"] in answers:
                label = field["label"] if isinstance(field["label"], dict) else {}
                responses[field["name"]] = {
                    "label": label.get("pt") or label.get("en") or "",
                    "value": answers[field["id"]],
                }
        out.append(
            {
                "id": rid,
                "token": str(resp["token"]),
                "email": resp["email"],
                "submitted_at": resp["submitted_at"],
                "responses": responses,
            }
        )
    return out


def find_upload(filename: str, token: str | None = None) -> str | None:
    from config import settings

    root = settings.uploads_dir
    if not os.path.isdir(root):
        return None
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        if filename in filenames:
            matches.append(os.path.join(dirpath, filename))
    if not matches:
        return None
    if token:
        for path in matches:
            if token in path:
                return path
    return matches[0]
