from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from services import forms_db
from services.mapping import (
    extract_accept,
    extract_candidate,
    extract_recommender,
    norm,
)


def to_form_id(value) -> int | None:
    """Converte o id de formulário gravado no edital (string) em inteiro."""
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


async def get_mapping(
    db: AsyncSession, edict_id: int, form_type: str, version: int | None = None
) -> EdictFormMapping | None:
    stmt = (
        select(EdictFormMapping)
        .where(
            EdictFormMapping.edict_id == edict_id,
            EdictFormMapping.form_type == form_type,
        )
        .order_by(EdictFormMapping.id.desc())
    )
    if version is not None:
        stmt = stmt.where(EdictFormMapping.form_version == version)
    return (await db.execute(stmt)).scalars().first()


async def load_edict_submissions(db: AsyncSession, fdb: AsyncSession, edict: Edict):
    """Sincroniza as inscrições do edital com as respostas do Forms.

    Retorna [(submission, resposta, dados_da_resposta)] sem duplicar
    inscrições nem apagar decisões já registradas.
    """
    cand_form = to_form_id(edict.candidate_forms)
    if cand_form is None:
        return []
    rec_form = to_form_id(edict.recommenders_forms)

    responses = await forms_db.get_form_responses(fdb, cand_form)
    loaded: list[tuple[Submission, dict, dict]] = []
    by_response: dict[int, tuple[Submission, dict, dict]] = {}
    for resp in responses:
        stmt = select(Submission).where(
            Submission.candidate_form_id == resp["id"],
            Submission.edict_id == edict.id,
        )
        sub = (await db.execute(stmt)).scalars().first()
        if sub is None:
            sub = Submission(
                edict_id=edict.id,
                candidate_form_id=resp["id"],
                stats="underreview",
                candidate_form_version=resp["form_version"] or 1,
                recommender_form_version=1,
                recommender_form_ids=[],
            )
            db.add(sub)
            await db.flush()
        data = await forms_db.get_response_data(fdb, resp["id"])
        loaded.append((sub, resp, data))
        by_response[resp["id"]] = (sub, resp, data)

    if rec_form:
        rec_mapping = await get_mapping(db, edict.id, "recommender")
        tree = rec_mapping.mapping if rec_mapping else None
        for rec in await forms_db.get_form_responses(fdb, rec_form):
            rdata = await forms_db.get_response_data(fdb, rec["id"])
            ext = extract_recommender(
                tree, rdata["values"], rdata["fields"], rec["email"]
            )
            target = _match_candidate(by_response, ext)
            if target is None:
                continue
            sub, _, _ = target
            ids = list(sub.recommender_form_ids or [])
            if rec["id"] not in ids:
                if not ids and rec["form_version"]:
                    sub.recommender_form_version = rec["form_version"]
                ids.append(rec["id"])
                sub.recommender_form_ids = ids
    await db.commit()
    return loaded


def _match_candidate(by_response, ext):
    email = (ext["candidate_email"] or "").lower()
    name = norm(ext["candidate_name"])
    for sub, resp, data in by_response.values():
        if email and resp["email"] and resp["email"].lower() == email:
            return (sub, resp, data)
    for sub, resp, data in by_response.values():
        cand = extract_candidate(None, data["values"], data["fields"])
        if email and cand["email"].lower() == email:
            return (sub, resp, data)
        if name and norm(cand["name"]) and norm(cand["name"]) == name:
            return (sub, resp, data)
    return None


async def _accept_info(fdb: AsyncSession, submission: Submission) -> dict:
    if not submission.accept_form_id:
        return {"sent": "not_sent", "accept": None, "comments": None,
                "submitted_at": None}
    resp = await forms_db.get_response(fdb, submission.accept_form_id)
    if resp is None:
        return {"sent": "not_sent", "accept": None, "comments": None,
                "submitted_at": None}
    if resp["submitted_at"] is None:
        return {"sent": "sent", "accept": None, "comments": None,
                "submitted_at": None}
    data = await forms_db.get_response_data(fdb, resp["id"])
    decision, comments = extract_accept(data["values"], data["fields"])
    return {
        "sent": "replied",
        "accept": decision,
        "comments": comments,
        "submitted_at": resp["submitted_at"],
    }


async def build_submission_item(
    db: AsyncSession, fdb: AsyncSession, edict: Edict, submission: Submission,
    response: dict, data: dict, user: User,
) -> dict:
    mapping = await get_mapping(
        db, edict.id, "candidate", submission.candidate_form_version
    )
    if mapping is None:
        mapping = await get_mapping(db, edict.id, "candidate")
    extracted = extract_candidate(
        mapping.mapping if mapping else None, data["values"], data["fields"]
    )

    advisor = None
    if submission.advisor_id:
        adv = await db.get(User, submission.advisor_id)
        if adv:
            advisor = {"id": adv.id, "name": adv.name, "email": adv.email}

    fav = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user.id,
                Favorite.submission_id == submission.id,
            )
        )
    ).scalars().first()

    labels = (
        (
            await db.execute(
                select(Label).where(Label.submission_id == submission.id)
            )
        )
        .scalars()
        .all()
    )

    bidding_labels = [l for l in labels if l.context_type == "bidding"]
    data_map: dict[str, list] = {}
    for lab in bidding_labels:
        u = await db.get(User, lab.user_id)
        if u is None:
            continue
        slot = (
            await db.execute(
                select(UserEdictSlot).where(
                    UserEdictSlot.user_id == u.id,
                    UserEdictSlot.edict_id == edict.id,
                )
            )
        ).scalars().first()
        data_map.setdefault(lab.label, []).append(
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "slots": str(slot.slots) if slot and slot.slots is not None else None,
            }
        )

    item = {
        "id": submission.id,
        "token": str(response["token"]),
        **extracted,
        "advisor": advisor,
        "stats": submission.stats,
        "is_favorite": fav is not None,
        "bidding_users": {"data": data_map},
        "labels": [
            {"id": l.id, "label": l.label, "color": l.color}
            for l in labels
            if l.context_type != "bidding"
        ],
        "accept": await _accept_info(fdb, submission),
    }
    return item


async def build_summary(
    db: AsyncSession, fdb: AsyncSession, edict: Edict, submission: Submission,
    response: dict, data: dict, user: User,
) -> dict:
    item = await build_submission_item(db, fdb, edict, submission, response, data,
                                       user)

    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.user_id == user.id,
                PrivateNote.submission_id == submission.id,
            )
        )
    ).scalars().first()

    recommendations = []
    for rid in submission.recommender_form_ids or []:
        rec = await forms_db.get_response(fdb, rid)
        if rec is None:
            continue
        rdata = await forms_db.get_response_data(fdb, rid)
        rec_mapping = await get_mapping(db, edict.id, "recommender")
        ext = extract_recommender(
            rec_mapping.mapping if rec_mapping else None,
            rdata["values"],
            rdata["fields"],
            rec["email"],
        )
        recommendations.append(
            {
                "id": rec["id"],
                "name": ext["recommender_name"],
                "email": ext["recommender_email"],
                "submitted_at": rec["submitted_at"],
            }
        )

    my_bidding = ""
    for lab in (
        await db.execute(
            select(Label).where(
                Label.submission_id == submission.id,
                Label.user_id == user.id,
                Label.context_type == "bidding",
            )
        )
        .scalars()
        .all()
    ):
        my_bidding = lab.label

    summary = dict(item)
    summary.update(
        {
            "favorite": item["is_favorite"],
            "is_favorite": item["is_favorite"],
            "access_email": response["email"],
            "private_note": note.note if note else "",
            "recommendations": recommendations,
            "bidding": my_bidding,
            "entry_semester": submission.entry_semester,
            "letter_sent": submission.letter_sent,
        }
    )
    return summary


async def build_submission_form(
    fdb: AsyncSession, form_id: int, version: int, response_id: int
) -> list[dict]:
    data = await forms_db.get_response_data(fdb, response_id)
    sections = await forms_db.get_sections(fdb, form_id, version)
    out = []
    for section in sections:
        fields = await forms_db.get_fields(fdb, section["id"], version)
        out.append(
            {
                **{k: v for k, v in section.items() if k != "fields"},
                "fields": [
                    {
                        "id": f["id"],
                        "name": f["name"],
                        "label": f["label"],
                        "type": f["type"],
                        "prefix": f["prefix"],
                        "position": f["position"],
                        "value": data["values"].get(f["id"]),
                    }
                    for f in fields
                ],
            }
        )
    return out
