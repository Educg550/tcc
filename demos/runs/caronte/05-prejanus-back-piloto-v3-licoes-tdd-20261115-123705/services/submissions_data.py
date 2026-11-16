"""Sincronização das inscrições com o Forms e construção dos dados
exibidos na listagem e no detalhe."""

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import services.forms_db as forms_db
import services.mappings as mappings
from models import (
    Edict,
    EdictFormMapping,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    User,
    UserEdictSlot,
)

TRUTHY = {"true", "sim", "yes", "1", "verdadeiro"}


def _truthy(value) -> bool:
    return value is not None and str(value).strip().lower() in TRUTHY


def _int_or(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


async def load_mappings(pdb: AsyncSession, edict_id: int, form_type: str) -> dict[int, dict]:
    result = await pdb.execute(
        select(EdictFormMapping).where(
            EdictFormMapping.edict_id == edict_id,
            EdictFormMapping.form_type == form_type,
            EdictFormMapping.is_active.is_(True),
        )
    )
    return {m.form_version: m.mapping for m in result.scalars()}


def _leaves_for_version(mapping_by_version: dict[int, dict], version: int):
    tree = mapping_by_version.get(version)
    if tree is None and mapping_by_version:
        tree = next(iter(mapping_by_version.values()))
    return mappings.flatten(tree)


async def sync_submissions(pdb: AsyncSession, fdb: AsyncSession, edict: Edict):
    """Cria inscrições locais para respostas finalizadas do Forms e associa
    as recomendações às inscrições corretas. Nunca remove decisões já
    registradas nem duplica inscrições."""
    try:
        cand_form = int(edict.candidate_forms)
    except (TypeError, ValueError):
        return
    responses = await forms_db.get_submitted_responses(fdb, cand_form)
    for resp in responses:
        result = await pdb.execute(
            select(Submission).where(
                Submission.edict_id == edict.id,
                Submission.candidate_form_id == resp["id"],
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            pdb.add(
                Submission(
                    edict_id=edict.id,
                    candidate_form_id=resp["id"],
                    candidate_form_version=resp["form_version"] or 1,
                    recommender_form_version=1,
                    stats="underreview",
                    created_at=dt.datetime.now(dt.timezone.utc),
                )
            )
    await pdb.flush()

    try:
        rec_form = int(edict.recommenders_forms)
    except (TypeError, ValueError):
        await pdb.commit()
        return
    rec_responses = await forms_db.get_submitted_responses(fdb, rec_form)
    if not rec_responses:
        await pdb.commit()
        return
    subs = (
        (await pdb.execute(select(Submission).where(Submission.edict_id == edict.id)))
        .scalars()
        .all()
    )
    if not subs:
        await pdb.commit()
        return
    cand_mappings = await load_mappings(pdb, edict.id, "candidate")
    rec_mappings = await load_mappings(pdb, edict.id, "recommender")
    cand_values = {}
    cand_leaves = {}
    for sub in subs:
        cand_values[sub.id] = await forms_db.get_values(fdb, sub.candidate_form_id)
        cand_leaves[sub.id] = _leaves_for_version(
            cand_mappings, sub.candidate_form_version
        )
    for resp in rec_responses:
        version = resp["form_version"] or 1
        leaves = _leaves_for_version(rec_mappings, version)
        values = await forms_db.get_values(fdb, resp["id"])
        rec_cand_email = mappings.get_value(leaves, values, "candidate_email")
        rec_cand_name = mappings.get_value(leaves, values, "candidate_name")
        target = None
        for sub in subs:
            sub_email = mappings.get_value(cand_leaves[sub.id], cand_values[sub.id], "email")
            sub_name = mappings.get_value(cand_leaves[sub.id], cand_values[sub.id], "name")
            if rec_cand_email and sub_email and rec_cand_email.strip().lower() == sub_email.strip().lower():
                target = sub
                break
            if (
                rec_cand_name
                and sub_name
                and mappings.normalize_key(rec_cand_name) == mappings.normalize_key(sub_name)
            ):
                target = sub
                break
        if target is not None:
            ids = list(target.recommenders_form_ids or [])
            if resp["id"] not in ids:
                ids.append(resp["id"])
                target.recommenders_form_ids = ids
            target.recommender_form_version = version
    await pdb.commit()


async def _accept_info(fdb: AsyncSession, submission: Submission) -> dict:
    info = {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if not submission.accept_form_id:
        return info
    resp = await forms_db.get_response(fdb, submission.accept_form_id)
    if resp is None:
        return info
    if resp.get("submitted_at") is None:
        info["sent"] = "sent"
        return info
    info["sent"] = "replied"
    info["submitted_at"] = resp["submitted_at"]
    values = await forms_db.get_values(fdb, submission.accept_form_id)
    if resp.get("form_id"):
        fields = await forms_db.get_all_fields(fdb, resp["form_id"])
        by_id = {f["id"]: f for f in fields}
        for field_id, value in values.items():
            field = by_id.get(field_id)
            if not field:
                continue
            name = mappings.normalize_key(field["name"] + field["label"])
            if "aceite" in name or "accept" in name or "decision" in name or "decisao" in name:
                info["accept"] = value
            elif "observ" in name or "comment" in name or "comentario" in name:
                info["comments"] = value
    return info


async def _bidding_users(pdb: AsyncSession, fdb_unused, submission: Submission, edict: Edict) -> dict:
    result = await pdb.execute(
        select(Label).where(
            Label.submission_id == submission.id,
            Label.context_type == "bidding",
        )
    )
    data = {}
    for label in result.scalars():
        user = await pdb.get(User, label.user_id)
        if user is None:
            continue
        slots = "0"
        slot_result = await pdb.execute(
            select(UserEdictSlot).where(
                UserEdictSlot.user_id == user.id,
                UserEdictSlot.edict_id == edict.id,
            )
        )
        slot = slot_result.scalar_one_or_none()
        if slot is not None and slot.slots is not None:
            slots = str(slot.slots)
        data[str(user.id)] = [
            {"id": user.id, "name": user.name, "email": user.email, "slots": slots}
        ]
    return {"data": data}


async def _submission_labels(pdb: AsyncSession, submission: Submission) -> list[dict]:
    result = await pdb.execute(
        select(Label).where(
            Label.submission_id == submission.id,
            (Label.context_type.is_(None)) | (Label.context_type == "candidate"),
        )
    )
    return [
        {"id": l.id, "label": l.label, "color": l.color}
        for l in result.scalars()
    ]


async def build_item(
    pdb: AsyncSession,
    fdb: AsyncSession,
    submission: Submission,
    edict: Edict,
    user: User,
    cand_mappings: dict[int, dict],
) -> dict:
    values = await forms_db.get_values(fdb, submission.candidate_form_id)
    leaves = _leaves_for_version(cand_mappings, submission.candidate_form_version)
    resp = await forms_db.get_response(fdb, submission.candidate_form_id)

    def val(prop):
        return mappings.get_value(leaves, values, prop)

    advisor = None
    if submission.advisor_id:
        adv = await pdb.get(User, submission.advisor_id)
        if adv:
            advisor = {"id": adv.id, "name": adv.name, "email": adv.email}

    fav = await pdb.get(Favorite, (user.id, submission.id))

    poscomp = None
    poscomp_year = val("poscomp_year")
    poscomp_score = val("poscomp_score")
    if poscomp_year is not None or poscomp_score is not None:
        poscomp = {
            "year": _int_or(poscomp_year),
            "score": poscomp_score or "",
        }

    return {
        "id": submission.id,
        "token": str(resp["token"]) if resp else "",
        "name": val("name") or "",
        "email": val("email") or (resp or {}).get("email") or "",
        "phone_number": val("phone_number") or "",
        "nationality": val("nationality") or "",
        "personal_website": val("personal_website") or "",
        "gender": val("gender") or "",
        "advisor": advisor,
        "birth_date": val("birth_date") or "",
        "graduation": {
            "country": val("country") or "",
            "course": val("course") or "",
            "institution": val("institution") or "",
            "year": _int_or(val("graduation_year")),
        },
        "poscomp": poscomp,
        "current_occupation": val("current_occupation"),
        "research": {
            "program": val("program") or "",
            "semester": val("semester") or "",
            "field": {
                "primary": val("primary") or "",
                "secondary": val("secondary") or "",
            },
            "will_apply_scholarship": _truthy(val("will_apply_scholarship")),
            "dedication_level": val("dedication_level") or "",
        },
        "lattes_curriculum": val("lattes_curriculum") or "",
        "stats": submission.stats,
        "is_favorite": fav is not None,
        "bidding_users": await _bidding_users(pdb, fdb, submission, edict),
        "labels": await _submission_labels(pdb, submission),
        "disabilities": _truthy(val("disabilities")),
        "ethnicity_race": _truthy(val("ethnicity_race")),
        "accept": await _accept_info(fdb, submission),
    }


async def build_submission_form(fdb: AsyncSession, submission: Submission) -> list[dict]:
    resp = await forms_db.get_response(fdb, submission.candidate_form_id)
    if resp is None:
        return []
    values = await forms_db.get_values(fdb, submission.candidate_form_id)
    sections = await forms_db.get_sections(
        fdb, resp["form_id"], submission.candidate_form_version
    )
    out = []
    for section in sections:
        fields = await forms_db.get_fields(fdb, resp["form_id"], section["id"])
        out.append(
            {
                "id": section["id"],
                "title": forms_db._title(section["title"]),
                "description": forms_db._title(section["description"]),
                "position": section["position"],
                "fields": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "label": f["label"],
                        "type": f["type"],
                        "prefix": f["prefix"],
                        "position": f["position"],
                        "value": values.get(f["id"]),
                    }
                    for f in fields
                ],
            }
        )
    return out


async def build_recommendations(fdb: AsyncSession, submission: Submission) -> list[dict]:
    out = []
    for rid in submission.recommenders_form_ids or []:
        resp = await forms_db.get_response(fdb, rid)
        if resp is None:
            continue
        out.append(
            {
                "id": rid,
                "email": resp.get("email"),
                "submitted_at": resp.get("submitted_at"),
            }
        )
    return out


async def build_detail(
    pdb: AsyncSession,
    fdb: AsyncSession,
    submission: Submission,
    edict: Edict,
    user: User,
) -> dict:
    cand_mappings = await load_mappings(pdb, edict.id, "candidate")
    item = await build_item(pdb, fdb, submission, edict, user, cand_mappings)

    note_result = await pdb.execute(
        select(PrivateNote).where(
            PrivateNote.user_id == user.id,
            PrivateNote.submission_id == submission.id,
        )
    )
    note = note_result.scalar_one_or_none()

    bidding_result = await pdb.execute(
        select(Label).where(
            Label.user_id == user.id,
            Label.submission_id == submission.id,
            Label.context_type == "bidding",
        )
    )
    bidding_label = bidding_result.scalars().first()

    summary = dict(item)
    summary.update(
        {
            "recommendations": await build_recommendations(fdb, submission),
            "private_note": note.note if note else "",
            "bidding": bidding_label.label if bidding_label else "",
            "entry_semester": submission.entry_semester or "",
            "letter_sent": submission.letter_sent,
        }
    )
    return {
        **summary,
        "id": submission.id,
        "stats": submission.stats,
        "summary": summary,
        "submission_form": await build_submission_form(fdb, submission),
    }
