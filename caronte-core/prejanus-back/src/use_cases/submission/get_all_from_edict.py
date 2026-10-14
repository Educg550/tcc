import json
from http import HTTPStatus
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from src.infra.database.models.edict import Edict
from src.infra.database.models.edict_form_mapping import EdictFormMapping
from src.infra.database.models.favorites import Favorites
from src.infra.database.models.labels import Labels
from src.infra.database.models.submission import StatsEnum, Submission
from src.infra.database.models.user import User
from src.use_cases.exceptions import InvalidMappingError
from src.use_cases.submission.change_semester import process_semester
from src.use_cases.submission.get_by_id import (
    get_accept_info,
    get_submissions_forms_by_id,
)
from src.use_cases.submission.schemas import (
    AcceptSchema,
    BiddingEnum,
    BiddingUserSchema,
    BiddingUsersSchema,
    GraduationSchema as BaseGraduationSchema,
    LabelSchema,
    PosCompSchema,
    ResearchFieldsSchema,
    ResearchSchema,
    SubmissionApprovalSchema as BaseSubmissionSchema,
    UserSchema,
)
from src.utils import str_for_bool
from src.utils.map_candidate import build_lookup, resolve_mapping


class GraduationSchema(BaseGraduationSchema):
    pass


class SubmissionSchema(BaseSubmissionSchema):
    pass


class GetAllSubmissionsFromEdictResponse(BaseModel):
    submissions: list[SubmissionSchema]


def get_value(mapped_values, name, default_value=None):
    """Helpers agora opera sobre o dict já resolvido pelo resolve_mapping."""
    val = mapped_values.get(name)
    return val if val is not None else default_value


def get_biddings_from_edict(labels, approvals_by_user, edict_id):
    bidding = {status.value: [] for status in BiddingEnum}

    for label in labels:
        if label.context_type != "bidding":
            continue

        user = label.user
        slot_entry = next(
            (slot for slot in user.edicts_with_slots if slot.edict_id == edict_id), None
        )
        total_slots = slot_entry.slots if slot_entry else 0
        approvals = approvals_by_user.get(user.id, 0)
        slots_rest = (total_slots or 0) - (approvals or 0)

        if label.label in bidding:
            bidding[label.label].append(
                BiddingUserSchema(
                    id=user.id, name=user.name, email=user.email, slots=str(slots_rest)
                )
            )
    return bidding


async def query_get_all_submissions_from_edict(
    session: AsyncSession,
    session_forms: AsyncSession,
    edict_id: int,
    auth_user_id: int,
    user_id: str | None = None,
    stats: str | None = None,
) -> list[SubmissionSchema]:

    # busca o edict
    query_result = await session.execute(select(Edict).where(Edict.id == edict_id))
    edict: Edict = query_result.scalars().one_or_none()
    if edict is None:
        return []

    # busca submissions dos formulários externos
    base_query = text("""
        select * from get_all_submissions(
            cast(:p_form_id as int),
            cast(:p_order_by as int),
            cast(:p_order_type as int),
            cast(:p_search as text),
            cast(:p_lang as text)
        )
    """)
    base_params = {
        "p_form_id": int(edict.recommenders_forms),
        "p_order_by": 1,
        "p_order_type": 0,
        "p_search": "",
        "p_lang": "pt",
    }

    all_recommenders = await session_forms.execute(base_query, base_params)
    recommenders_forms_submissions = [
        dict(row._mapping) for row in all_recommenders.fetchall()
    ]

    recommenders_by_email = {}
    for r in recommenders_forms_submissions:
        responses = r.get("responses", [])
        r["_responses_dict"] = {k: v for d in responses for k, v in d.items()}
        email = r.get("email")
        if email and str(email).strip():
            recommenders_by_email.setdefault(str(email).strip().lower(), []).append(r)

    base_params["p_form_id"] = int(edict.candidate_forms)
    all_candidates = await session_forms.execute(base_query, base_params)
    candidate_forms_submissions = [
        dict(row._mapping) for row in all_candidates.fetchall()
    ]

    # adicionar cada informação com lookup/mapping e recomendadores
    recommender_labels = ["recommended-email-1", "recommended-email-2"]

    # busca o form mapping do tipo candidate para este edict
    mapping_result = await session.execute(
        select(EdictFormMapping)
        .where(EdictFormMapping.edict_id == edict_id)
        .where(EdictFormMapping.form_type == "candidate")
    )

    edict_form_mappings = mapping_result.scalars().all()

    mappings_by_version = {
        mapping.form_version: mapping for mapping in edict_form_mappings
    }

    result = await session.execute(
        select(Submission).where(Submission.edict_id == edict_id)
    )

    submissions_by_candidate_form = {
        s.candidate_form_id: s for s in result.scalars().all()
    }

    for candidate_form in candidate_forms_submissions:
        submission = submissions_by_candidate_form.get(candidate_form["id"])
        if submission is None:
            raise HTTPException(
                status_code=500,
                detail=f"No Submission found for candidate form {candidate_form['id']}",
            )

        if submission.candidate_form_version not in mappings_by_version:
            raise HTTPException(
                status_code=500,
                detail=f"No candidate form mapping found for form version "
                f"{submission.candidate_form_version} (submission {submission.id})",
            )

        edict_form_mapping = mappings_by_version[submission.candidate_form_version]
        # resolve o mapeamento flexível — igual ao get_submission_by_id
        raw_form = await get_submissions_forms_by_id(
            candidate_form["id"], session_forms
        )
        lookup = build_lookup(raw_form)
        try:
            candidate_form["_mapped"] = resolve_mapping(
                edict_form_mapping.mapping,
                lookup,
            )
        except InvalidMappingError as e:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        fullname = get_value(candidate_form["_mapped"], "name", "")
        candidate_form["recommenders"] = []
        for label in recommender_labels:
            email_recommender = get_value(candidate_form["_mapped"], label)
            if not email_recommender:
                continue
            for r in recommenders_by_email.get(email_recommender, []):
                r_fullname = (
                    r["_responses_dict"].get("fullname-candidate", {}).get("value", "")
                )
                if r_fullname == fullname:
                    candidate_form["recommenders"].append(r)

    # upsert submissions na base local
    insert_list = [
        {
            "edict_id": edict_id,
            "candidate_form_id": c["id"],
            "recommenders_form_ids": [r["id"] for r in c["recommenders"]],
            "entry_semester": process_semester(get_value(c["_mapped"], "semester", "")),
        }
        for c in candidate_forms_submissions
    ]

    if insert_list:
        stmt = insert(Submission).values(insert_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=["candidate_form_id", "edict_id"],
            set_={"recommenders_form_ids": stmt.excluded.recommenders_form_ids},
        )
        await session.execute(stmt)
        await session.commit()

    # carrega submissions com labels/bidding
    candidate_form_ids = [item["candidate_form_id"] for item in insert_list]
    sub_query = (
        select(Submission)
        .where(Submission.edict_id == edict_id)
        .where(Submission.candidate_form_id.in_(candidate_form_ids))
        .options(
            joinedload(Submission.labels)
            .joinedload(Labels.user)
            .joinedload(User.edicts_with_slots),
            joinedload(Submission.advisor),
        )
    )
    if stats is not None:
        sub_query = sub_query.where(Submission.stats == stats.lower())

    all_submissions_result = await session.execute(sub_query)
    all_submissions = all_submissions_result.unique().scalars().all()
    submission_ids = [row.id for row in all_submissions]

    approvals_by_user: dict[int, int] = {}
    for submission in all_submissions:
        if submission.stats == StatsEnum.APPROVED.value and submission.advisor_id:
            approvals_by_user[submission.advisor_id] = (
                approvals_by_user.get(submission.advisor_id, 0) + 1
            )

    submission_mapping = {}
    for submission in all_submissions:
        advisor_name = submission.advisor.name if submission.advisor else ""
        advisor_email = submission.advisor.email if submission.advisor else ""
        bidding = get_biddings_from_edict(
            submission.labels, approvals_by_user, edict_id
        )
        accept = await get_accept_info(submission, session_forms)

        submission_mapping[submission.candidate_form_id] = {
            "id": submission.id,
            "labels": [
                label
                for label in submission.labels
                if label.context_type == "candidate" and label.user_id == auth_user_id
            ],
            "stats": submission.stats,
            "advisor_name": advisor_name,
            "advisor_email": advisor_email,
            "bidding": bidding,
            "accept": accept,
        }

    # favoritos
    if auth_user_id is not None:
        favorites_result = await session.execute(
            select(Favorites.submission_id)
            .where(Favorites.submission_id.in_(submission_ids))
            .where(Favorites.user_id == auth_user_id)
        )
        favorite_ids = {row[0] for row in favorites_result.fetchall()}
    else:
        favorite_ids = set()

    # monta response
    response = []
    for candidate_form in candidate_forms_submissions:
        candidate_submission_id = candidate_form["id"]
        if candidate_submission_id not in submission_mapping:
            continue

        cmap = submission_mapping[candidate_submission_id]
        if user_id is not None and cmap["id"] not in favorite_ids:
            continue

        mv = candidate_form["_mapped"]

        disabilities_raw = get_value(mv, "disabilities", "[]")
        if isinstance(disabilities_raw, str):
            disabilities_raw = json.loads(disabilities_raw)

        response.append(
            SubmissionSchema(
                id=cmap["id"],
                token=str(candidate_form.get("token")),
                name=get_value(mv, "name", ""),
                phone_number=get_value(mv, "phone-number", ""),
                email=get_value(mv, "email", ""),
                lattes_curriculum=f"http://lattes.cnpq.br/{get_value(mv, 'lattes_curriculum', '')}",
                nationality=get_value(mv, "nationality", ""),
                personal_website=get_value(mv, "personal_website", ""),
                gender=get_value(mv, "gender", ""),
                birth_date=get_value(mv, "birth_date", ""),
                graduation=GraduationSchema(
                    course=get_value(mv["graduation"], "course", ""),
                    country=get_value(mv["graduation"], "country", ""),
                    institution=get_value(mv["graduation"], "institution", ""),
                    year=int(get_value(mv["graduation"], "year", 0)),
                ),
                poscomp=(
                    PosCompSchema(
                        year=int(get_value(mv["poscomp"], "year", -1)),
                        score=str(get_value(mv["poscomp"], "score", "")),
                    )
                    if get_value(mv["poscomp"], "score")
                    and get_value(mv["poscomp"], "year")
                    else None
                ),
                current_occupation=get_value(mv, "current_occupation", ""),
                research=ResearchSchema(
                    program="",
                    field=ResearchFieldsSchema(
                        primary=get_value(mv["research"]["field"], "primary", ""),
                        secondary=get_value(mv["research"]["field"], "secondary", ""),
                    ),
                    semester=get_value(mv["research"], "semester", ""),
                    dedication_level=get_value(mv["research"], "dedication_level", ""),
                    will_apply_scholarship=bool(
                        str_for_bool(
                            get_value(mv["research"], "will_apply_scholarship", "False")
                        )
                    ),
                ),
                advisor=UserSchema(
                    id=-1,
                    name=cmap["advisor_name"],
                    email=cmap["advisor_email"],
                ),
                stats=cmap["stats"],
                is_favorite=cmap["id"] in favorite_ids,
                labels=[
                    LabelSchema(label=label.label, color=label.color, id=label.id)
                    for label in cmap["labels"]
                ],
                bidding_users=BiddingUsersSchema(data=cmap["bidding"]),
                accept=cmap["accept"],
                disabilities=len(disabilities_raw) > 0,
                ethnicity_race=len(json.loads(get_value(mv, "ethnicity-race", "[]")))
                > 0,
            )
        )

    return response
