"""Regras de negócio de inscrições: sincronização com o Forms e montagem dos payloads."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import forms_db, mapping
from prejanus.models import (
    Edict,
    EdictFormMapping,
    Label,
    Submission,
    User,
    UserEdictSlots,
)


def _int(value) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


async def get_mappings(db: AsyncSession, edict_id: int, form_type: str) -> dict:
    result = await db.execute(
        select(EdictFormMapping).where(
            EdictFormMapping.edict_id == edict_id,
            EdictFormMapping.form_type == form_type,
            EdictFormMapping.is_active.is_(True),
        )
    )
    return {m.form_version: m.mapping for m in result.scalars().all()}


def best_mapping(mappings: dict, version: int) -> dict | None:
    if not mappings:
        return None
    return mappings.get(version) or next(iter(mappings.values()))


def extract_candidate(flat: dict, values: dict) -> dict:
    def v(name, default=""):
        return mapping.value_at(flat, values, name, default)

    poscomp_year = v("poscomp_year")
    poscomp_score = v("poscomp_score")
    poscomp = (
        {"year": mapping.to_int(poscomp_year), "score": poscomp_score}
        if (poscomp_year or poscomp_score)
        else None
    )
    return {
        "name": v("name"),
        "email": v("email"),
        "phone_number": v("phone_number") or v("phone"),
        "nationality": v("nationality"),
        "personal_website": v("personal_website") or v("website"),
        "gender": v("gender"),
        "birth_date": v("birth_date"),
        "graduation": {
            "country": v("graduation_country"),
            "course": v("graduation_course"),
            "institution": v("graduation_institution"),
            "year": mapping.to_int(v("graduation_year")),
        },
        "poscomp": poscomp,
        "current_occupation": v("current_occupation"),
        "research": {
            "program": v("research_program"),
            "semester": v("research_semester"),
            "field": {
                "primary": v("research_field_primary") or v("primary_field") or v("primary"),
                "secondary": v("research_field_secondary") or v("secondary_field") or v("secondary"),
            },
            "will_apply_scholarship": mapping.to_bool(v("will_apply_scholarship")),
            "dedication_level": v("dedication_level"),
        },
        "lattes_curriculum": v("lattes_curriculum"),
        "disabilities": mapping.to_bool(v("disabilities")),
        "ethnicity_race": mapping.to_bool(v("ethnicity_race")),
    }


async def sync_submissions(db: AsyncSession, fdb: AsyncSession, edict: Edict) -> None:
    """Cria inscrições para candidaturas finalizadas e associa recomendações."""
    cand_form = _int(edict.candidate_forms)
    if cand_form is None:
        return
    responses = await forms_db.get_submissions_raw(fdb, cand_form)
    result = await db.execute(select(Submission).where(Submission.edict_id == edict.id))
    subs = result.scalars().all()
    by_form_id = {s.candidate_form_id: s for s in subs}
    created = False
    for resp in responses:
        if resp["id"] not in by_form_id:
            sub = Submission(
                edict_id=edict.id,
                candidate_form_id=resp["id"],
                candidate_form_version=resp["form_version"],
                recommender_form_version=resp["form_version"],
                recommenders_form_ids=[],
                stats="underreview",
                created_at=datetime.now(timezone.utc),
            )
            db.add(sub)
            by_form_id[resp["id"]] = sub
            created = True
    if created:
        await db.flush()

    rec_form = _int(edict.recommenders_forms)
    if rec_form is None:
        return
    rec_responses = await forms_db.get_submissions_raw(fdb, rec_form)
    if not rec_responses:
        return
    cand_mappings = await get_mappings(db, edict.id, "candidate")
    rec_mappings = await get_mappings(db, edict.id, "recommender")

    # identidade dos candidatos
    identities = {}
    for sub in by_form_id.values():
        resp = next((r for r in responses if r["id"] == sub.candidate_form_id), None)
        if resp is None:
            continue
        tree = best_mapping(cand_mappings, sub.candidate_form_version)
        flat = mapping.flatten_tree(tree)
        data = extract_candidate(flat, resp["values"])
        email = (data["email"] or resp["email"] or "").strip().lower()
        identities[sub.id] = (email, mapping.normalize_name(data["name"] or ""))

    for resp in rec_responses:
        tree = best_mapping(rec_mappings, resp["form_version"])
        flat = mapping.flatten_tree(tree)
        values = resp["values"]
        cand_email = mapping.find_candidate_email(flat, values)
        cand_name = mapping.find_candidate_name(flat, values)
        target = None
        if cand_email:
            for sub_id, (email, _name) in identities.items():
                if email and email == cand_email:
                    target = sub_id
                    break
        if target is None and cand_name:
            norm = mapping.normalize_name(cand_name)
            for sub_id, (_email, name) in identities.items():
                if name and name == norm:
                    target = sub_id
                    break
        if target is None:
            # varredura dos valores por e-mail conhecido de candidato
            all_vals = [str(v).strip().lower() for v in values.values() if v]
            for sub_id, (email, _name) in identities.items():
                if email and email in all_vals:
                    target = sub_id
                    break
        if target is None:
            continue
        sub = next((s for s in by_form_id.values() if s.id == target), None)
        if sub is None:
            continue
        ids = list(sub.recommenders_form_ids or [])
        if resp["id"] not in ids:
            ids.append(resp["id"])
            sub.recommenders_form_ids = ids
            sub.recommender_form_version = resp["form_version"]


async def _user_map(db: AsyncSession, user_ids: set) -> dict:
    if not user_ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {u.id: u for u in result.scalars().all()}


async def _slots_map(db: AsyncSession, edict_id: int, user_ids: set) -> dict:
    if not user_ids:
        return {}
    result = await db.execute(
        select(UserEdictSlots).where(
            UserEdictSlots.edict_id == edict_id, UserEdictSlots.user_id.in_(user_ids)
        )
    )
    return {s.user_id: s.slots for s in result.scalars().all()}


async def accept_info(fdb: AsyncSession, sub: Submission) -> dict:
    if not sub.accept_form_id:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    resp = await forms_db.get_response(fdb, sub.accept_form_id)
    if resp is None:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    sent = "replied" if resp.get("submitted_at") else "sent"
    accept_value = None
    comments = None
    for row in await forms_db.get_response_values(fdb, sub.accept_form_id):
        name = (row["name"] or "").lower()
        label = str(row["label"] or "").lower() if not isinstance(row["label"], dict) else ""
        key = name + " " + label
        if accept_value is None and ("accept" in key or "decision" in key or "aceit" in key):
            accept_value = row["value"]
        if comments is None and ("comment" in key or "observ" in key or "coment" in key):
            comments = row["value"]
    return {
        "sent": sent,
        "accept": accept_value,
        "comments": comments,
        "submitted_at": resp.get("submitted_at"),
    }


async def list_submissions(db: AsyncSession, fdb: AsyncSession, edict: Edict, user: User) -> list:
    await sync_submissions(db, fdb, edict)
    await db.commit()

    result = await db.execute(
        select(Submission).where(Submission.edict_id == edict.id).order_by(Submission.id)
    )
    subs = result.scalars().all()

    cand_form = _int(edict.candidate_forms)
    responses = {r["id"]: r for r in (await forms_db.get_submissions_raw(fdb, cand_form))} if cand_form else {}
    cand_mappings = await get_mappings(db, edict.id, "candidate")

    fav_rows = await db.execute(
        select(Submission.id).where(Submission.edict_id == edict.id)
    )
    sub_ids = [r[0] for r in fav_rows.all()]
    favorites = set()
    labels_by_sub: dict = {}
    biddings_by_sub: dict = {}
    if sub_ids:
        from prejanus.models import Favorite

        fav_result = await db.execute(
            select(Favorite.submission_id).where(
                Favorite.user_id == user.id, Favorite.submission_id.in_(sub_ids)
            )
        )
        favorites = {r[0] for r in fav_result.all()}
        label_rows = await db.execute(select(Label).where(Label.submission_id.in_(sub_ids)))
        for lab in label_rows.scalars().all():
            if lab.context_type == "bidding":
                biddings_by_sub.setdefault(lab.submission_id, []).append(lab)
            else:
                labels_by_sub.setdefault(lab.submission_id, []).append(lab)

    user_ids = set()
    for labs in list(labels_by_sub.values()) + list(biddings_by_sub.values()):
        user_ids.update(l.user_id for l in labs)
    for sub in subs:
        if sub.advisor_id:
            user_ids.add(sub.advisor_id)
    users = await _user_map(db, user_ids)
    slots = await _slots_map(db, edict.id, set(biddings_by_sub and {l.user_id for labs in biddings_by_sub.values() for l in labs} or set()))

    items = []
    for sub in subs:
        resp = responses.get(sub.candidate_form_id, {})
        values = resp.get("values", {})
        tree = best_mapping(cand_mappings, sub.candidate_form_version)
        flat = mapping.flatten_tree(tree)
        data = extract_candidate(flat, values)
        advisor = users.get(sub.advisor_id) if sub.advisor_id else None
        bidding_data: dict = {}
        for lab in biddings_by_sub.get(sub.id, []):
            u = users.get(lab.user_id)
            if u is None:
                continue
            bidding_data.setdefault(lab.label, []).append(
                {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "slots": str(slots.get(u.id) or 0) if slots.get(u.id) is not None else None,
                }
            )
        items.append(
            {
                "id": sub.id,
                "token": resp.get("token", ""),
                **data,
                "email": data["email"] or resp.get("email") or "",
                "advisor": (
                    {"id": advisor.id, "name": advisor.name, "email": advisor.email} if advisor else None
                ),
                "stats": sub.stats,
                "is_favorite": sub.id in favorites,
                "bidding_users": {"data": bidding_data},
                "labels": [
                    {"id": l.id, "label": l.label, "color": l.color}
                    for l in labels_by_sub.get(sub.id, [])
                ],
                "accept": await accept_info(fdb, sub),
            }
        )
    return items


async def get_recommendations(db: AsyncSession, fdb: AsyncSession, edict: Edict, sub: Submission) -> list:
    rec_form = _int(edict.recommenders_forms)
    if rec_form is None:
        return []
    rec_responses = {r["id"]: r for r in await forms_db.get_submissions_raw(fdb, rec_form)}
    rec_mappings = await get_mappings(db, edict.id, "recommender")
    out = []
    for rid in sub.recommenders_form_ids or []:
        resp = rec_responses.get(rid)
        if resp is None:
            continue
        tree = best_mapping(rec_mappings, resp["form_version"])
        flat = mapping.flatten_tree(tree)
        values = resp["values"]
        name = None
        for path, leaf in flat.items():
            if leaf is None:
                continue
            if "recommender" in path and "name" in path:
                name = values.get(leaf.get("field"))
                break
        if name is None:
            name = mapping.value_at(flat, values, "name")
        text = mapping.value_at(flat, values, "text") or mapping.value_at(flat, values, "recommendation")
        out.append(
            {
                "id": rid,
                "name": name or "",
                "email": resp.get("email") or "",
                "text": text,
                "submitted_at": resp.get("submitted_at"),
            }
        )
    return out


async def build_submission_form(fdb: AsyncSession, edict: Edict, sub: Submission) -> list:
    cand_form = _int(edict.candidate_forms)
    if cand_form is None:
        return []
    values = {}
    raw = await forms_db.get_submissions_raw(fdb, cand_form)
    entry = next((r for r in raw if r["id"] == sub.candidate_form_id), None)
    if entry:
        values = entry["values"]
    sections = await forms_db.get_sections(fdb, cand_form, sub.candidate_form_version)
    out = []
    for section in sections:
        fields = await forms_db.get_fields(fdb, cand_form, [section["id"]], sub.candidate_form_version)
        sec = forms_db.section_dict(section)
        sec["fields"] = []
        for field in fields:
            fd = forms_db.field_dict(field)
            fd["value"] = values.get(field["id"])
            sec["fields"].append(fd)
        out.append(sec)
    return out


async def submission_summary(db: AsyncSession, fdb: AsyncSession, edict: Edict, sub: Submission, user: User) -> dict:
    cand_form = _int(edict.candidate_forms)
    resp = None
    values = {}
    if cand_form:
        raw = await forms_db.get_submissions_raw(fdb, cand_form)
        entry = next((r for r in raw if r["id"] == sub.candidate_form_id), None)
        if entry:
            resp = entry
            values = entry["values"]
    cand_mappings = await get_mappings(db, edict.id, "candidate")
    tree = best_mapping(cand_mappings, sub.candidate_form_version)
    flat = mapping.flatten_tree(tree)
    data = extract_candidate(flat, values)

    from prejanus.models import Favorite, Label, PrivateNote

    fav = await db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.submission_id == sub.id)
    )
    is_favorite = fav.scalar_one_or_none() is not None
    label_rows = await db.execute(
        select(Label).where(
            Label.submission_id == sub.id, Label.context_type.is_distinct_from("bidding")
        )
    )
    labels = [
        {"id": l.id, "label": l.label, "color": l.color} for l in label_rows.scalars().all()
    ]
    note_row = await db.execute(
        select(PrivateNote).where(PrivateNote.user_id == user.id, PrivateNote.submission_id == sub.id)
    )
    note = note_row.scalar_one_or_none()
    advisor = await db.get(User, sub.advisor_id) if sub.advisor_id else None
    bidding_row = await db.execute(
        select(Label).where(
            Label.user_id == user.id,
            Label.submission_id == sub.id,
            Label.context_type == "bidding",
        )
    )
    bidding = bidding_row.scalar_one_or_none()

    summary = {
        **data,
        "email": data["email"] or (resp.get("email") if resp else "") or "",
        "stats": sub.stats,
        "advisor": (
            {"id": advisor.id, "name": advisor.name, "email": advisor.email} if advisor else None
        ),
        "is_favorite": is_favorite,
        "labels": labels,
        "private_note": note.note if note else "",
        "bidding": bidding.label if bidding else "",
        "accept": await accept_info(fdb, sub),
        "entry_semester": sub.entry_semester or data["research"]["semester"],
        "letter_sent": sub.letter_sent,
        "recommendations": await get_recommendations(db, fdb, edict, sub),
    }
    return summary
