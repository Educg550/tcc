import json

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import formsdb
from prejanus.models import (
    Comment,
    Edict,
    EdictFormMapping,
    Favorite,
    Label,
    PrivateNote,
    Submission,
    User,
    UserEdictSlots,
)


def apply_mapping(tree, values: dict) -> dict:
    out: dict = {}
    if not isinstance(tree, dict):
        return out
    for key, node in tree.items():
        if node is None:
            continue
        if isinstance(node, dict) and set(node.keys()) == {"section", "field"}:
            value = values.get(node["field"])
            if value is not None:
                out[key] = value
        elif isinstance(node, dict):
            sub = apply_mapping(node, values)
            if sub:
                out[key] = sub
    return out


def deep_merge(base: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def _flatten(node, out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, dict):
                _flatten(value, out)
            elif isinstance(value, str):
                out.append((key, value))
    return out


async def get_mapping(db: AsyncSession, edict_id: int, form_type: str, version: int):
    result = await db.execute(
        select(EdictFormMapping).where(
            EdictFormMapping.edict_id == edict_id,
            EdictFormMapping.form_type == form_type,
            EdictFormMapping.form_version == version,
            EdictFormMapping.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def candidate_identity(db: AsyncSession, edict: Edict, sub: Submission):
    resp = await formsdb.get_response(sub.candidate_form_id)
    values, _fields = await formsdb.get_response_data(sub.candidate_form_id)
    mapping = await get_mapping(db, edict.id, "candidate", sub.candidate_form_version)
    mapped = apply_mapping(mapping.mapping, values) if mapping else {}
    name = mapped.get("name") or ""
    email = mapped.get("email") or (resp["email"] if resp else "") or ""
    return name, email, resp, mapped, values


async def sync_submissions(db: AsyncSession, edict: Edict) -> list[Submission]:
    async def _load():
        result = await db.execute(
            select(Submission).where(Submission.edict_id == edict.id).order_by(Submission.id)
        )
        return list(result.scalars().all())

    subs = await _load()
    try:
        form_id = int(edict.candidate_forms)
    except (TypeError, ValueError):
        return subs
    responses = await formsdb.get_submitted_responses(form_id)
    existing = {s.candidate_form_id for s in subs}
    added = False
    for r in responses:
        if r["id"] in existing:
            continue
        await db.execute(
            text(
                "insert into submission (edict_id, candidate_form_id, "
                "candidate_form_version, recommender_form_version, "
                "recommenders_form_ids, stats, letter_sent) "
                "values (:e, :c, :cv, 1, cast(:r as json), 'underreview', false)"
            ),
            {"e": edict.id, "c": r["id"], "cv": r["form_version"] or 1, "r": "[]"},
        )
        added = True
    if added:
        await db.commit()
        subs = await _load()
    return subs


async def associate_recommendations(db: AsyncSession, edict: Edict, subs) -> None:
    try:
        rec_form = int(edict.recommenders_forms)
    except (TypeError, ValueError):
        return
    recs = await formsdb.get_submitted_responses(rec_form)
    if not recs:
        return
    rec_values = {}
    for r in recs:
        values, _fields = await formsdb.get_response_data(r["id"])
        rec_values[r["id"]] = [v.strip().lower() for v in values.values() if isinstance(v, str)]
    changed = False
    for sub in subs:
        name, email, _resp, _mapped, _values = await candidate_identity(db, edict, sub)
        identifiers = [i for i in (email, name) if i and len(i) >= 3]
        if not identifiers:
            continue
        matched = [
            rid
            for rid, vals in rec_values.items()
            if any(any(ident.lower() in v for v in vals) for ident in identifiers)
        ]
        current = list(sub.recommender_form_ids or [])
        new = [rid for rid in matched if rid not in current]
        if new:
            await db.execute(
                text(
                    "update submission set recommenders_form_ids = cast(:r as json) "
                    "where id = :i"
                ),
                {"r": json.dumps(current + new), "i": sub.id},
            )
            changed = True
    if changed:
        await db.commit()


async def bidding_users(db: AsyncSession, edict_id: int, submission_id: int) -> dict:
    result = await db.execute(
        select(Label, User)
        .join(User, User.id == Label.user_id)
        .where(Label.submission_id == submission_id, Label.context_type == "bidding")
        .order_by(Label.id)
    )
    data: dict = {}
    for label, user in result:
        slot_row = (
            await db.execute(
                select(UserEdictSlots).where(
                    UserEdictSlots.user_id == user.id, UserEdictSlots.edict_id == edict_id
                )
            )
        ).scalar_one_or_none()
        slots = str(slot_row.slots) if slot_row and slot_row.slots is not None else None
        data.setdefault(label.label, []).append(
            {"id": user.id, "name": user.name, "email": user.email, "slots": slots}
        )
    return {"data": data}


async def accept_payload(db: AsyncSession, sub: Submission) -> dict:
    empty = {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if not sub.accept_form_id:
        return empty
    resp = await formsdb.get_response(sub.accept_form_id)
    if not resp or not resp["submitted_at"]:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values, fields = await formsdb.get_response_data(sub.accept_form_id)
    accept_value = None
    comments_value = None
    for f in fields:
        key = f"{f['name'] or ''} {f['label'] or ''}".lower()
        value = values.get(f["id"])
        if value is None:
            continue
        if accept_value is None and any(k in key for k in ("accept", "aceite", "decision", "decis")):
            accept_value = value
        elif comments_value is None and any(k in key for k in ("comment", "observ", "coment")):
            comments_value = value
    if accept_value is None and values:
        accept_value = next(iter(values.values()))
    return {
        "sent": "replied",
        "accept": accept_value,
        "comments": comments_value,
        "submitted_at": resp["submitted_at"],
    }


async def build_submission_payload(db: AsyncSession, edict: Edict, sub: Submission, user_id: int) -> dict:
    name, email, resp, mapped, _values = await candidate_identity(db, edict, sub)
    payload = {
        "id": sub.id,
        "token": str(resp["token"]) if resp else "",
        "name": name,
        "email": email,
        "phone_number": "",
        "nationality": "",
        "personal_website": "",
        "gender": "",
        "advisor": None,
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
        "stats": sub.stats,
        "is_favorite": False,
        "bidding_users": {"data": {}},
        "labels": [],
        "disabilities": False,
        "ethnicity_race": False,
        "accept": {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None},
    }
    deep_merge(payload, mapped)
    if sub.advisor_id:
        advisor = await db.get(User, sub.advisor_id)
        if advisor:
            payload["advisor"] = {"id": advisor.id, "name": advisor.name, "email": advisor.email}
    fav = (
        await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    payload["is_favorite"] = fav is not None
    labels = (
        await db.execute(
            select(Label).where(
                Label.submission_id == sub.id, Label.context_type == "candidate"
            )
        )
    ).scalars().all()
    payload["labels"] = [{"id": l.id, "label": l.label, "color": l.color} for l in labels]
    payload["bidding_users"] = await bidding_users(db, edict.id, sub.id)
    payload["accept"] = await accept_payload(db, sub)
    return payload


async def list_submissions(db: AsyncSession, edict: Edict, user_id: int,
                           stats: str | None = None, only_favorites: bool = False) -> list[dict]:
    subs = await sync_submissions(db, edict)
    await associate_recommendations(db, edict, subs)
    if only_favorites:
        fav_ids = {
            f.submission_id
            for f in (
                await db.execute(select(Favorite).where(Favorite.user_id == user_id))
            ).scalars()
        }
        subs = [s for s in subs if s.id in fav_ids]
    payloads = [await build_submission_payload(db, edict, s, user_id) for s in subs]
    if stats:
        payloads = [p for p in payloads if p["stats"] == stats]
    return payloads


async def recommendations(db: AsyncSession, edict: Edict, sub: Submission) -> list[dict]:
    out = []
    mapping = await get_mapping(db, edict.id, "recommender", sub.recommender_form_version)
    for rid in sub.recommender_form_ids or []:
        resp = await formsdb.get_response(rid)
        if not resp:
            continue
        values, fields = await formsdb.get_response_data(rid)
        mapped = apply_mapping(mapping.mapping, values) if mapping else {}
        pairs = _flatten(mapped)
        if not pairs:
            pairs = [
                (f["name"] or "", values[f["id"]])
                for f in fields
                if values.get(f["id"]) is not None
            ]

        def find(*keys):
            for key, value in pairs:
                if any(k in key.lower() for k in keys):
                    return value
            return None

        out.append(
            {
                "name": find("name", "nome"),
                "email": find("email"),
                "text": find("text", "carta", "letter", "coment", "relat"),
                "submitted_at": resp["submitted_at"],
            }
        )
    return out


async def submission_form_structure(edict: Edict, sub: Submission) -> dict:
    try:
        form_id = int(edict.candidate_forms)
    except (TypeError, ValueError):
        return {"sections": []}
    version = sub.candidate_form_version
    sections = await formsdb.get_sections(form_id, version)
    values, _fields = await formsdb.get_response_data(sub.candidate_form_id)
    out = []
    for section in sections:
        fields = await formsdb.get_fields_for_version(section["id"], version)
        out.append(
            {
                "id": section["id"],
                "title": section["title"],
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
    return {"sections": out}


async def comments_list(db: AsyncSession, sub: Submission) -> list[dict]:
    result = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.user_id)
        .where(Comment.submission_id == sub.id)
        .order_by(Comment.created_at, Comment.id)
    )
    return [
        {
            "id": c.id,
            "user": {"id": u.id, "name": u.name},
            "submission_id": c.submission_id,
            "comment": c.comment,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c, u in result
    ]


async def build_detail(db: AsyncSession, edict: Edict, sub: Submission, user_id: int,
                       include_comments: bool = False) -> dict:
    payload = await build_submission_payload(db, edict, sub, user_id)
    summary = dict(payload)
    note = (
        await db.execute(
            select(PrivateNote).where(
                PrivateNote.user_id == user_id, PrivateNote.submission_id == sub.id
            )
        )
    ).scalar_one_or_none()
    summary["private_note"] = note.note if note else ""
    research_semester = (payload.get("research") or {}).get("semester") or ""
    summary["semester"] = sub.entry_semester or research_semester
    summary["letter_sent"] = sub.letter_sent
    bidding = (
        await db.execute(
            select(Label).where(
                Label.submission_id == sub.id,
                Label.user_id == user_id,
                Label.context_type == "bidding",
            )
        )
    ).scalars().first()
    summary["bidding"] = bidding.label if bidding else ""
    summary["recommendations"] = await recommendations(db, edict, sub)
    if include_comments:
        summary["comments"] = await comments_list(db, sub)
    form_struct = await submission_form_structure(edict, sub)
    return {"summary": summary, "submission_form": form_struct}
