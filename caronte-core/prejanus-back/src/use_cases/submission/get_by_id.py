from datetime import datetime, timezone
from fastapi import HTTPException
import json
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infra.database.models.favorites import Favorites
from src.infra.database.models.labels import Labels
from src.infra.database.models.submission import StatsEnum, Submission
from src.infra.database.models.comment import Comment
from src.infra.database.models.submission_view import SubmissionView
from src.infra.database.models.edict_form_mapping import EdictFormMapping
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.change_semester import process_semester
from src.use_cases.submission.get_biddings_by_user import get_biddings_by_user
from src.use_cases.submission.private_notes.get_private_note import get_private_note
from src.use_cases.submission.exceptions import SubmissionNotFound
from src.use_cases.submission.schemas import (
    AcceptSchema,
    PosCompSchema,
    ResearchFieldsSchema,
    ResearchSchema,
    SentStatus,
    UserSchema,
    SubmissionSchema,
    CommentSchema,
    RecommenderSchema,
    GraduationSummarySchema,
)
from src.utils import str_for_bool, get_value
from src.utils.map_candidate import build_lookup, resolve_mapping


async def get_accept_info(submission, session_forms):
    accept = AcceptSchema(
        sent=SentStatus.NOT_SENT, accept="", comments="", submitted_at=None
    )
    if submission.accept_form_id is not None:
        accept.sent = SentStatus.SENT

        accept_forms_submissions = await get_submissions_forms_by_id(
            submission.accept_form_id, session_forms
        )

        if accept_forms_submissions:
            accept.sent = SentStatus.REPLIED

            accept_responses_dict = {
                field["name"]: field["value"]
                for section in accept_forms_submissions
                for field in section["fields"]
            }

            # workaround
            submitted_at = (
                await session_forms.execute(
                    text("SELECT submitted_at FROM form_response WHERE id = :id"),
                    {"id": int(submission.accept_form_id)},
                )
            ).scalar()

            accept.comments = get_value(accept_responses_dict, "comments")
            accept.accept = get_value(accept_responses_dict, "accept")
            accept.submitted_at = submitted_at
    return accept


async def get_submissions_forms_by_id(candidate_form_id, session_forms):
    # Busca os metadados da resposta para saber qual é o formulário original
    response_record = (
        await session_forms.execute(
            text("SELECT form_id,submitted_at FROM form_response WHERE id = :id"),
            {"id": int(candidate_form_id)},
        )
    ).one_or_none()

    if not response_record:
        return None

    real_form_id = response_record.form_id

    result = await session_forms.execute(
        text("""
            SELECT 
                s.id AS section_id, 
                s.title AS section_title,
                f.id AS field_id, 
                f.label,
                f.name,
                f.type,
                f.prefix,
                r.value
            FROM form_section s
            JOIN form_field f ON s.id = f.section_id
            LEFT JOIN responses r ON f.id = r.field_id AND r.response_id = :res_id
            WHERE s.form_id = :f_id
            ORDER BY s.position, f.id
        """),
        {"res_id": int(candidate_form_id), "f_id": int(real_form_id)},
    )

    rows = result.fetchall()
    if not rows:
        return []

    # Agrupar por hierarquia
    sections = {}
    for row in rows:
        r = row._mapping
        s_id = r["section_id"]

        if s_id not in sections:
            sections[s_id] = {"id": s_id, "title": r["section_title"], "fields": []}

        sections[s_id]["fields"].append(r)

    return list(sections.values())


async def load_activity(
    submission_id,
    session: AsyncSession,
    session_forms: AsyncSession,
    include_comments: bool,
):

    query = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(
            selectinload(Submission.advisor),
            selectinload(Submission.comments).selectinload(Comment.user),
        )
    )

    result = await session.execute(query)

    submission = result.scalar_one_or_none()

    if submission is None:
        raise SubmissionNotFound(submission_id)

    accept_info = await get_accept_info(submission, session_forms)

    candidates_forms_submission = await get_submissions_forms_by_id(
        submission.candidate_form_id, session_forms
    )

    edict_form_mappings = (
        (
            await session.execute(
                select(EdictFormMapping)
                .where(EdictFormMapping.edict_id == submission.edict_id)
                .where(EdictFormMapping.form_type == "candidate")
            )
        )
        .scalars()
        .all()
    )

    mapped_candidate_values = {}
    if edict_form_mappings and candidates_forms_submission:
        edict_form_mapping = edict_form_mappings[0]
        try:
            lookup = build_lookup(candidates_forms_submission)
            mapped_candidate_values = resolve_mapping(edict_form_mapping.mapping, lookup) or {}
        except Exception:
            mapped_candidate_values = {}

    forms_recommenders = await get_recommenders(submission, session, session_forms, mapped_candidate_values)

    activity = []

    activity += (
        []
        if not include_comments
        else [
            CommentSchema(
                user=UserSchema(
                    id=comment.user.id, name=comment.user.name, email=comment.user.email
                ),
                id=comment.id,
                comment=comment.comment,
                created_at=comment.created_at,
                type="comment",
            )
            for comment in submission.comments
        ]
    )

    activity += (
        []
        if not include_comments
        or submission.advisor is None
        or submission.stats != StatsEnum.APPROVED.value
        else [
            CommentSchema(
                id=0,
                user=UserSchema(
                    id=submission.advisor.id,
                    name=submission.advisor.name,
                    email=submission.advisor.email,
                ),
                created_at=submission.updated_at,
                comment="",
                type="advisor",
            )
        ]
    )

    submitted_at = (await session_forms.execute(
        text("SELECT submitted_at FROM form_response WHERE id = :id"),
        {"id": int(submission.candidate_form_id)}
    )).scalar()

    cand_fullname = (
        get_value(mapped_candidate_values, "fullname", "")
        or get_value(mapped_candidate_values, "name", "")
    )
    cand_email = get_value(mapped_candidate_values, "email", "")
    if not cand_email:
        cand_email = (await session_forms.execute(
            text("SELECT email FROM form_response WHERE id = :id"),
            {"id": int(submission.candidate_form_id)}
        )).scalar() or ""

    if not cand_fullname and candidates_forms_submission:
        cand_dict = {
            field['name']: field['value']
            for section in candidates_forms_submission
            for field in section.get('fields', [])
            if 'name' in field and 'value' in field
        }
        cand_fullname = cand_dict.get("fullname", "") or cand_dict.get("name", "")

    activity += [
        CommentSchema(
            id=0,
            user=UserSchema(
                id=0,
                name=cand_fullname,
                email=cand_email,
            ),
            created_at=submitted_at,
            comment=f'{cand_fullname} preencheu o formulário',
            type="custom",
        )
    ]

    for forms_recommender in forms_recommenders:
        if forms_recommender.sent == True:
            activity += [
                CommentSchema(
                    id=0,
                    user=UserSchema(
                        id=0,
                        name=forms_recommender.fullname,
                        email=forms_recommender.email,
                    ),
                    created_at=forms_recommender.submitted_at,
                    comment=f"{forms_recommender.fullname} recomendou o candidato",
                    type="custom",
                )
            ]

    if accept_info.sent == SentStatus.REPLIED:
        activity += [
            CommentSchema(
                id=0,
                user=UserSchema(
                    id=0,
                    name=cand_fullname,
                    email=cand_email,
                ),
                created_at=accept_info.submitted_at,
                comment=f"{accept_info.accept} {accept_info.comments}",
                type="external_comment",
            )
        ]

    return sorted(
        activity,
        key=lambda x: (
            x.created_at.replace(tzinfo=timezone.utc)
            if x.created_at.tzinfo is None
            else x.created_at
        ),
    )


async def get_recommenders(submission, session, session_forms, mapped_candidate_values):
    recommenders = []

    edict_form_mappings = (await session.execute(
        select(EdictFormMapping)
        .where(EdictFormMapping.edict_id == submission.edict_id)
        .where(EdictFormMapping.form_type == "recommender")
    )).scalars().all()

    rec_mapping = edict_form_mappings[0] if edict_form_mappings else None

    for recommenders_form_id in (submission.recommenders_form_ids or []):
        recommenders_forms_submissions = await get_submissions_forms_by_id(recommenders_form_id, session_forms)

        mapped_recommenders_values = {}
        if rec_mapping and recommenders_forms_submissions:
            try:
                lookup = build_lookup(recommenders_forms_submissions)
                mapped_recommenders_values = resolve_mapping(rec_mapping.mapping, lookup) or {}
            except Exception:
                mapped_recommenders_values = {}

        recommenders_dict_responses = {
            field['name']: field['value']
            for section in (recommenders_forms_submissions or [])
            for field in section.get('fields', [])
            if 'name' in field and 'value' in field
        }

        rec_res_row = (await session_forms.execute(
            text("SELECT email, submitted_at FROM form_response WHERE id = :id"),
            {"id": int(recommenders_form_id)}
        )).one_or_none()

        rec_email = (
            (rec_res_row.email if rec_res_row and rec_res_row.email else "")
            or get_value(mapped_recommenders_values, "email", "")
            or get_value(recommenders_dict_responses, "email", "")
        )

        rec_submitted_at = (
            (rec_res_row.submitted_at if rec_res_row and rec_res_row.submitted_at else None)
            or get_value(recommenders_dict_responses, "submitted_at", None)
            or get_value(recommenders_dict_responses, "created_at", None)
            or datetime.now()
        )

        cand_name = (
            get_value(mapped_recommenders_values, "fullname_candidate", "")
            or get_value(mapped_recommenders_values, "name_candidate", "")
            or get_value(recommenders_dict_responses, "fullname-candidate", "")
            or get_value(recommenders_dict_responses, "fullname_candidate", "")
            or get_value(recommenders_dict_responses, "name_candidate", "")
            or ""
        )

        rec_fullname = (
            get_value(mapped_recommenders_values, "fullname", "")
            or get_value(mapped_recommenders_values, "name", "")
            or get_value(recommenders_dict_responses, "fullname", "")
            or get_value(recommenders_dict_responses, "name", "")
            or ""
        )

        affiliation = (
            get_value(mapped_recommenders_values, "affiliation", "")
            or get_value(recommenders_dict_responses, "affiliation", "")
            or ""
        )

        kt = (
            get_value(mapped_recommenders_values, "known_time", None)
            or get_value(recommenders_dict_responses, "known-time", None)
            or get_value(recommenders_dict_responses, "known_time", "")
        )
        if isinstance(kt, list):
            known_time = ", ".join(str(x) for x in kt if str(x).strip())
        elif kt is not None:
            known_time = str(kt)
        else:
            known_time = ""

        rel = (
            get_value(mapped_recommenders_values, "relationship", None)
            or get_value(recommenders_dict_responses, "relationship", None)
        )
        if isinstance(rel, str):
            try:
                rel = json.loads(rel)
            except Exception:
                rel = [rel] if rel else []
        if isinstance(rel, list):
            relationship = [str(x) for x in rel if str(x).strip()]
        else:
            relationship = []

        rating = (
            get_value(mapped_recommenders_values, "rating", "")
            or get_value(recommenders_dict_responses, "rating", "")
            or ""
        )

        recommenders.append(RecommenderSchema(
            fullname_candidate=cand_name,
            fullname=rec_fullname,
            affiliation=affiliation,
            known_time=known_time,
            relationship=relationship,
            rating=rating,
            email=rec_email,
            sent=True,
            submitted_at=rec_submitted_at
        ))

    # Recommenders nominated in candidate form
    cand_fullname = (
        get_value(mapped_candidate_values, "fullname", "")
        or get_value(mapped_candidate_values, "name", "")
    )
    recs_data = get_value(mapped_candidate_values, "recommenders", {})
    forms_recommenders = []
    if isinstance(recs_data, dict):
        for rec_key in ["recommender1", "recommender2"]:
            rec_entry = recs_data.get(rec_key, {})
            if isinstance(rec_entry, dict):
                r_name = rec_entry.get("fullname", "") or rec_entry.get("name", "")
                r_email = rec_entry.get("email", "")
                if r_name or r_email:
                    forms_recommenders.append(
                        RecommenderSchema(
                            fullname_candidate=cand_fullname,
                            fullname=r_name,
                            email=r_email,
                            sent=False
                        )
                    )

    # Fallback to raw candidate form responses if forms_recommenders is empty
    if not forms_recommenders and submission.candidate_form_id:
        try:
            cand_raw = await get_submissions_forms_by_id(submission.candidate_form_id, session_forms)
            if cand_raw:
                cand_dict = {
                    field['name']: field['value']
                    for section in cand_raw
                    for field in section.get('fields', [])
                    if 'name' in field and 'value' in field
                }
                if not cand_fullname:
                    cand_fullname = cand_dict.get("fullname", "") or cand_dict.get("name", "")
                for idx in ["1", "2"]:
                    r_name = cand_dict.get(f"recommended-name-{idx}", "") or cand_dict.get(f"recommended_name_{idx}", "")
                    r_email = cand_dict.get(f"recommended-email-{idx}", "") or cand_dict.get(f"recommended_email_{idx}", "")
                    if r_name or r_email:
                        forms_recommenders.append(
                            RecommenderSchema(
                                fullname_candidate=cand_fullname,
                                fullname=r_name,
                                email=r_email,
                                sent=False
                            )
                        )
        except Exception:
            pass

    existing_emails = {
        r.email.strip().lower()
        for r in recommenders
        if r.email and r.email.strip()
    }
    existing_names = {
        r.fullname.strip().lower()
        for r in recommenders
        if r.fullname and r.fullname.strip()
    }

    for form_recommender in forms_recommenders:
        f_email = (form_recommender.email or "").strip().lower()
        f_name = (form_recommender.fullname or "").strip().lower()

        is_existing = False
        if f_email and f_email in existing_emails:
            is_existing = True
        elif f_name and f_name in existing_names:
            is_existing = True

        if not is_existing:
            recommenders.append(form_recommender)

    return recommenders


async def get_submission_by_id(
    submission_id: int,
    auth_user: UserDTO,
    session: AsyncSession,
    session_forms: AsyncSession,
    include_comments: bool = False,
):
    query = (
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.advisor))
    )

    if include_comments:
        query = query.options(
            selectinload(Submission.comments).joinedload(Comment.user)
        )

    query_result = await session.execute(query)
    submission = query_result.scalars().one_or_none()

    if submission is None:
        raise SubmissionNotFound(submission_id)

    favorites_query = (
        select(Favorites)
        .where(Favorites.submission_id == submission_id)
        .options(selectinload(Favorites.user))
    )
    favorites_result = await session.execute(favorites_query)
    favorites = favorites_result.scalars().all()
    favorite_ids = {favorite.user_id for favorite in favorites}

    labels_query = (
        select(Labels)
        .where(Labels.submission_id == submission_id)
        .where(Labels.user_id == auth_user.id)
        .where(Labels.context_type == "candidate")
        .options(selectinload(Labels.user))
    )
    labels_result = await session.execute(labels_query)
    labels = labels_result.scalars().all()

    bidding = await get_biddings_by_user(submission_id, auth_user.id, session)

    private_note = await get_private_note(session, auth_user.id, submission_id)

    edict_form_mappings = (
        (
            await session.execute(
                select(EdictFormMapping)
                .where(EdictFormMapping.edict_id == submission.edict_id)
                .where(
                    EdictFormMapping.form_type == "candidate",
                    EdictFormMapping.form_version == submission.candidate_form_version,
                )
            )
        )
        .scalars()
        .all()
    )

    form_response = (await session_forms.execute(
        text("SELECT form_id,email FROM form_response WHERE id = :id"),
        {"id": int(submission.candidate_form_id)}
    )).one_or_none()
    candidates_forms_submission = await get_submissions_forms_by_id(
        submission.candidate_form_id, session_forms
    )

    mapped_candidate_values = {}
    if edict_form_mappings and candidates_forms_submission:
        edict_form_mapping = edict_form_mappings[0]
        try:
            lookup = build_lookup(candidates_forms_submission)
            mapped_candidate_values = resolve_mapping(edict_form_mapping.mapping, lookup) or {}
        except Exception:
            mapped_candidate_values = {}

    # If some basic fields are missing and we have raw forms, fallback to raw candidate fields
    if candidates_forms_submission:
        raw_cand_dict = {
            field['name']: field['value']
            for section in candidates_forms_submission
            for field in section.get('fields', [])
            if 'name' in field and 'value' in field
        }
        for k in ["name", "fullname", "phone-number", "nationality", "website", "biological-sex", "birth", "current-job", "primary-area", "secondary-area", "semester", "intended-level", "scholarship", "relevant-information", "about-this-program", "disabilities", "ethnicity-race"]:
            if k not in mapped_candidate_values and k in raw_cand_dict:
                mapped_candidate_values[k] = raw_cand_dict[k]
        if "name" not in mapped_candidate_values and "fullname" in raw_cand_dict:
            mapped_candidate_values["name"] = raw_cand_dict["fullname"]

    cand_email = (form_response.email if form_response and form_response.email else "") or get_value(mapped_candidate_values, "email", "")

    disabilities = get_value(mapped_candidate_values, "disabilities", "[]")
    if isinstance(disabilities, str):
        try:
            disabilities = json.loads(disabilities)
        except Exception:
            disabilities = [disabilities] if disabilities else []

    eth = get_value(mapped_candidate_values, "ethnicity-race", "[]")
    if isinstance(eth, str):
        try:
            eth = json.loads(eth)
        except Exception:
            eth = [eth] if eth else []
    ethnicity_race = len(eth) > 0 if isinstance(eth, list) else bool(eth)

    # pegar dados do forms (candidatos e orientadores)
    # --
    recommenders = await get_recommenders(
        submission, session, session_forms, mapped_candidate_values
    )
    accept = await get_accept_info(submission, session_forms)

    # TODO retornar SubmissionSchema

    res = {}

    res["submission_form"] = candidates_forms_submission

    res["summary"] = SubmissionSchema(
        id=submission.id,
        name=get_value(mapped_candidate_values, "name", ""),
        phone_number=get_value(mapped_candidate_values, "phone-number", ""),
        email=cand_email,
        lattes_curriculum=f"http://lattes.cnpq.br/{get_value(mapped_candidate_values, 'lattes_curriculum', '')}",
        nationality=get_value(mapped_candidate_values, "nationality", ""),
        personal_website=get_value(mapped_candidate_values, "website", ""),
        gender=get_value(mapped_candidate_values, "biological-sex", ""),
        birth_date=get_value(mapped_candidate_values, "birth", ""),
        graduation=GraduationSummarySchema(
            year=int(get_value(mapped_candidate_values, "year-of-graduation", 0)),
            course=get_value(
                mapped_candidate_values,
                "course-of-graduation",
                default_value="Campo não encontrado",
            ),
            country=get_value(
                mapped_candidate_values, "country-undergraduate", default_value=""
            ),
            institution=get_value(
                mapped_candidate_values, "institution", default_value=""
            ),
        ),
        poscomp=(
            PosCompSchema(
                year=int(get_value(mapped_candidate_values, "year-poscomp", 0)),
                score=get_value(mapped_candidate_values, "grades-poscomp"),
            )
            if get_value(mapped_candidate_values, "grades-poscomp")
            and get_value(mapped_candidate_values, "year-poscomp")
            else None
        ),
        current_occupation=get_value(
            mapped_candidate_values, "current-job", default_value=""
        ),
        research=ResearchSchema(
            program="",
            field=ResearchFieldsSchema(
                primary=get_value(mapped_candidate_values, "primary-area", ""),
                secondary=get_value(mapped_candidate_values, "secondary-area", ""),
            ),
            semester=process_semester(
                get_value(mapped_candidate_values, "semester", "")
            ),
            dedication_level=get_value(mapped_candidate_values, "intended-level", ""),
            will_apply_scholarship=str_for_bool(
                get_value(mapped_candidate_values, "scholarship", False)
            ),
        ),
        entry_semester=(
            submission.entry_semester
            if submission.entry_semester is not None
            else process_semester(get_value(mapped_candidate_values, "semester", ""))
        ),
        relevant_information=get_value(
            mapped_candidate_values, "relevant-information", ""
        ),
        about_this_program=get_value(mapped_candidate_values, "about-this-program", ""),
        stats=submission.stats.lower(),
        is_favorite=auth_user.id in favorite_ids,
        recommenders=recommenders,
        # TODO modificar depois
        documents=[],
        # TODO modificar depois
        comments=[],
        private_note=private_note.note if private_note is not None else "",
        labels=[
            {"label": label.label, "color": label.color, "id": label.id}
            for label in labels
        ],
        user_bidding=bidding.label if bidding is not None else "",
        disabilities=len(disabilities) > 0,
        ethnicity_race=ethnicity_race,
        accept=accept,
        letter_sent=submission.letter_sent,
    )

    return res


async def get_views_by_submission_id(
    submission_id: int,
    auth_user: UserDTO,
    session: AsyncSession,
) -> SubmissionSchema:

    query = (
        select(SubmissionView)
        .where(SubmissionView.submission_id == submission_id)
        .options(selectinload(SubmissionView.user))
    )

    result = await session.execute(query)
    submission_views = result.scalars().all()
    response = [
        {
            **submission_view.__dict__,
            "user": UserSchema(
                id=submission_view.user.id,
                name=submission_view.user.name,
                email=submission_view.user.email,
            ),
        }
        for submission_view in submission_views
    ]
    return response
