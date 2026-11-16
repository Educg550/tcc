import json
from datetime import timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services import forms_service
from services.mapping_service import resolve_value

CANDIDATE_PATHS = {
    "name": ("personal", "name"),
    "email": ("personal", "email"),
    "phone_number": ("personal", "phone_number"),
    "nationality": ("personal", "nationality"),
    "personal_website": ("personal", "personal_website"),
    "gender": ("personal", "gender"),
    "birth_date": ("personal", "birth_date"),
    "graduation_country": ("graduation", "country"),
    "graduation_course": ("graduation", "course"),
    "graduation_institution": ("graduation", "institution"),
    "graduation_year": ("graduation", "year"),
    "poscomp_year": ("poscomp", "year"),
    "poscomp_score": ("poscomp", "score"),
    "current_occupation": ("current_occupation",),
    "research_program": ("research", "program"),
    "research_semester": ("research", "semester"),
    "research_primary": ("research", "field", "primary"),
    "research_secondary": ("research", "field", "secondary"),
    "research_scholarship": ("research", "will_apply_scholarship"),
    "research_dedication": ("research", "dedication_level"),
    "lattes_curriculum": ("lattes_curriculum",),
    "disabilities": ("disabilities",),
    "ethnicity_race": ("ethnicity_race",),
}

RECOMMENDER_PATHS = {
    "candidate_name": ("candidate", "name"),
    "candidate_email": ("candidate", "email"),
    "recommender_name": ("recommender", "name"),
    "recommender_email": ("recommender", "email"),
    "text": ("text",),
}


def parse_form_ids(raw) -> list[int]:
    if raw is None:
        return []
    if isinstance(raw, (int,)):
        return [raw]
    value = str(raw).strip()
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        try:
            return [int(value)]
        except ValueError:
            return []
    if isinstance(parsed, list):
        return [int(v) for v in parsed]
    return [int(parsed)]


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "sim", "yes", "1", "on"}


def _to_int(value):
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


async def get_edict(db: AsyncSession, edict_id: int) -> dict | None:
    result = await db.execute(text("select * from edict where id = :id"), {"id": edict_id})
    row = result.mappings().first()
    return dict(row) if row else None


async def get_submission(db: AsyncSession, submission_id: int) -> dict | None:
    result = await db.execute(
        text("select * from submission where id = :id"), {"id": submission_id}
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_mapping(db: AsyncSession, edict_id: int, form_type: str, version: int) -> dict | None:
    result = await db.execute(
        text(
            "select * from edict_form_mappings "
            "where edict_id = :eid and form_type = :ftype::form_type_enum "
            "and form_version = :v and is_active = true"
        ),
        {"eid": edict_id, "ftype": form_type, "v": version},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def ensure_submissions(db: AsyncSession, fs: AsyncSession, edict: dict) -> None:
    form_ids = parse_form_ids(edict.get("candidate_forms"))
    for form_id in form_ids:
        responses = await forms_service.get_submitted_responses(fs, form_id)
        for response in responses:
            await db.execute(
                text(
                    "insert into submission (edict_id, candidate_form_id, candidate_form_version, "
                    "recommender_form_version, created_at, updated_at) values (:eid, :fid, :cv, :rv, :now, :now) "
                    "on conflict (candidate_form_id, edict_id) do nothing"
                ),
                {
                    "eid": edict["id"],
                    "fid": response["id"],
                    "cv": response["form_version"] or 1,
                    "rv": response["form_version"] or 1,
                    "now": _now(),
                },
            )
    await db.commit()


def _now():
    from datetime import datetime

    return datetime.now(timezone.utc)


async def get_recommendations(
    db: AsyncSession, fs: AsyncSession, edict: dict, candidate_name, candidate_email
) -> list[dict]:
    recommendations = []
    for form_id in parse_form_ids(edict.get("recommenders_forms")):
        responses = await forms_service.get_submitted_responses(fs, form_id)
        if not responses:
            continue
        first = responses[0]
        mapping_row = await get_mapping(db, edict["id"], "recommender", first["form_version"] or 1)
        tree = mapping_row["mapping"] if mapping_row else None
        for response in responses:
            values = await forms_service.get_response_values(fs, response["id"])
            if tree:
                r_name = resolve_value(tree, RECOMMENDER_PATHS["candidate_name"], values)
                r_email = resolve_value(tree, RECOMMENDER_PATHS["candidate_email"], values)
            else:
                r_name = r_email = None
            match = False
            if candidate_email and r_email:
                match = r_email.strip().lower() == str(candidate_email).strip().lower()
            elif candidate_name and r_name:
                match = r_name.strip().lower() == str(candidate_name).strip().lower()
            if not match:
                continue
            entry = {
                "submitted_at": response["submitted_at"],
                "email": response.get("email"),
            }
            if tree:
                entry["name"] = resolve_value(tree, RECOMMENDER_PATHS["recommender_name"], values)
                entry["recommender_email"] = resolve_value(
                    tree, RECOMMENDER_PATHS["recommender_email"], values
                )
                entry["text"] = resolve_value(tree, RECOMMENDER_PATHS["text"], values)
            recommendations.append(entry)
    return recommendations


async def get_recommendations_for_submission(
    db: AsyncSession, fs: AsyncSession, edict: dict, submission: dict
) -> list[dict]:
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    values = await forms_service.get_response_values(fs, submission["candidate_form_id"])
    mapping_row = await get_mapping(
        db, edict["id"], "candidate", submission["candidate_form_version"]
    )
    name = email = None
    if mapping_row:
        tree = mapping_row["mapping"]
        name = resolve_value(tree, ("personal", "name"), values)
        email = resolve_value(tree, ("personal", "email"), values)
    if not email and response:
        email = response.get("email")
    return await get_recommendations(db, fs, edict, name, email)


async def get_accept_info(fs: AsyncSession, submission: dict) -> dict:
    accept_form_id = submission.get("accept_form_id")
    if not accept_form_id:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    response = await forms_service.get_response(fs, accept_form_id)
    if response is None:
        return {"sent": "not_sent", "accept": None, "comments": None, "submitted_at": None}
    if response.get("submitted_at") is None:
        return {"sent": "sent", "accept": None, "comments": None, "submitted_at": None}
    values = await forms_service.get_response_values(fs, accept_form_id)
    fields = []
    for section in await forms_service.select_sections(fs, response["form_id"], None):
        fields.extend(await forms_service.select_fields(fs, section["id"], None))
    accept_value = None
    comments = None
    for field in fields:
        name = (field.get("name") or "").lower()
        value = values.get(field["id"])
        if value is None:
            continue
        if accept_value is None and ("accept" in name or "decision" in name):
            accept_value = value
        if comments is None and ("comment" in name or "observation" in name or "observacao" in name):
            comments = value
    return {
        "sent": "replied",
        "accept": accept_value,
        "comments": comments,
        "submitted_at": response["submitted_at"],
    }


async def get_bidding_users(db: AsyncSession, edict_id: int, submission_id: int) -> dict:
    result = await db.execute(
        text(
            "select l.label, u.id, u.name, u.email, s.slots from labels l "
            'join "user" u on u.id = l.user_id '
            "left join user_edict_slots s on s.user_id = l.user_id and s.edict_id = :eid "
            "where l.submission_id = :sid and l.context_type = 'bidding'"
        ),
        {"eid": edict_id, "sid": submission_id},
    )
    data: dict[str, list] = {}
    for row in result.mappings():
        data.setdefault(row["label"] or "", []).append(
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "slots": str(row["slots"]) if row["slots"] is not None else None,
            }
        )
    return {"data": data}


async def get_user_labels(db: AsyncSession, submission_id: int, user_id: int) -> list[dict]:
    result = await db.execute(
        text(
            "select id, label, color from labels "
            "where submission_id = :sid and user_id = :uid and context_type = 'candidate'"
        ),
        {"sid": submission_id, "uid": user_id},
    )
    return [dict(r) for r in result.mappings()]


async def get_submission_labels(db: AsyncSession, submission_id: int) -> list[dict]:
    result = await db.execute(
        text("select id, label, color from labels where submission_id = :sid"),
        {"sid": submission_id},
    )
    return [dict(r) for r in result.mappings()]


async def is_favorite(db: AsyncSession, submission_id: int, user_id: int) -> bool:
    result = await db.execute(
        text("select 1 from favorites where submission_id = :sid and user_id = :uid"),
        {"sid": submission_id, "uid": user_id},
    )
    return result.first() is not None


async def get_private_note(db: AsyncSession, submission_id: int, user_id: int) -> str:
    result = await db.execute(
        text("select note from private_note where submission_id = :sid and user_id = :uid"),
        {"sid": submission_id, "uid": user_id},
    )
    row = result.first()
    return row[0] if row else ""


async def get_user_bidding(db: AsyncSession, submission_id: int, user_id: int) -> str:
    result = await db.execute(
        text(
            "select label from labels where submission_id = :sid and user_id = :uid "
            "and context_type = 'bidding'"
        ),
        {"sid": submission_id, "uid": user_id},
    )
    row = result.first()
    return row[0] if row else ""


async def get_advisor(db: AsyncSession, advisor_id) -> dict | None:
    if advisor_id is None:
        return None
    result = await db.execute(
        text('select id, name, email from "user" where id = :id'), {"id": advisor_id}
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def build_summary(
    db: AsyncSession, fs: AsyncSession, edict: dict, submission: dict, user: dict
) -> dict:
    response = await forms_service.get_response(fs, submission["candidate_form_id"])
    values = await forms_service.get_response_values(fs, submission["candidate_form_id"])
    mapping_row = await get_mapping(
        db, edict["id"], "candidate", submission["candidate_form_version"]
    )
    tree = mapping_row["mapping"] if mapping_row else None

    def mapped(key):
        if tree is None:
            return None
        return resolve_value(tree, CANDIDATE_PATHS[key], values)

    name = mapped("name")
    email = mapped("email") or (response.get("email") if response else None)

    graduation = {
        "country": mapped("graduation_country") or "",
        "course": mapped("graduation_course") or "",
        "institution": mapped("graduation_institution") or "",
        "year": _to_int(mapped("graduation_year")) or 0,
    }
    poscomp_year = _to_int(mapped("poscomp_year"))
    poscomp_score = mapped("poscomp_score")
    poscomp = (
        {"year": poscomp_year, "score": poscomp_score}
        if poscomp_year is not None or poscomp_score
        else None
    )
    research = {
        "program": mapped("research_program") or "",
        "semester": mapped("research_semester") or "",
        "field": {
            "primary": mapped("research_primary") or "",
            "secondary": mapped("research_secondary") or "",
        },
        "will_apply_scholarship": _to_bool(mapped("research_scholarship")),
        "dedication_level": mapped("research_dedication") or "",
    }
    advisor = await get_advisor(db, submission.get("advisor_id"))
    recommendations = await get_recommendations(db, fs, edict, name, email)
    accept = await get_accept_info(fs, submission)

    return {
        "id": submission["id"],
        "token": str(response["token"]) if response else "",
        "name": name or "",
        "email": email or "",
        "phone_number": mapped("phone_number") or "",
        "nationality": mapped("nationality") or "",
        "personal_website": mapped("personal_website") or "",
        "gender": mapped("gender") or "",
        "advisor": advisor,
        "birth_date": mapped("birth_date") or "",
        "graduation": graduation,
        "poscomp": poscomp,
        "current_occupation": mapped("current_occupation"),
        "research": research,
        "lattes_curriculum": mapped("lattes_curriculum") or "",
        "stats": submission["stats"],
        "is_favorite": await is_favorite(db, submission["id"], user["id"]),
        "bidding_users": await get_bidding_users(db, edict["id"], submission["id"]),
        "labels": await get_user_labels(db, submission["id"], user["id"]),
        "disabilities": _to_bool(mapped("disabilities")),
        "ethnicity_race": _to_bool(mapped("ethnicity_race")),
        "accept": accept,
        "recommendations": recommendations,
        "private_note": await get_private_note(db, submission["id"], user["id"]),
        "bidding": await get_user_bidding(db, submission["id"], user["id"]),
        "entry_semester": submission.get("entry_semester"),
        "letter_sent": submission.get("letter_sent", False),
    }


async def build_submission_form(fs: AsyncSession, form_id: int, version: int, values: dict) -> list[dict]:
    sections = await forms_service.select_sections(fs, form_id, version)
    result = []
    for section in sections:
        fields = await forms_service.select_fields(fs, section["id"], version)
        section_data = {
            "id": section["id"],
            "title": section.get("title"),
            "description": section.get("description"),
            "position": section.get("position"),
            "fields": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "label": f.get("label"),
                    "type": f["type"],
                    "prefix": f.get("prefix"),
                    "position": f.get("position"),
                    "value": values.get(f["id"]),
                }
                for f in fields
            ],
        }
        result.append(section_data)
    return result
