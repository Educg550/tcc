from src.use_cases.submission.schemas import  PosCompSchema, ResearchFieldsSchema, ResearchSchema,  SubmissionSchema, GraduationSummarySchema
import json
from src.use_cases.submission.change_semester import process_semester
from src.utils import get_value,str_for_bool


def map_master_submission(
    submission,
    dict_responses,
    candidates_forms_submissions,
    recommenders,
    documents,
    favorite_ids,
    auth_user,
    labels,
    bidding,
    private_note,
    accept,
    activity
) -> SubmissionSchema:

    return SubmissionSchema(
        id=submission.id,
        name=get_value(dict_responses, "fullname"),
        phone_number=get_value(dict_responses, "phone-number"),
        email=candidates_forms_submissions["email"],
        lattes_curriculum=f"http://lattes.cnpq.br/{get_value(dict_responses, 'lattes-cv', '')}",
        nationality=get_value(dict_responses, "nationality"),
        personal_website=get_value(dict_responses, "website"),
        gender=get_value(dict_responses, "biological-sex", ""),
        birth_date=get_value(dict_responses, "birth"),
        graduation=GraduationSummarySchema(
            year=int(get_value(dict_responses, "year-of-graduation")),
            course=get_value(dict_responses, "course-of-graduation"),
            country=get_value(dict_responses, "country-undergraduate"),
            institution=get_value(dict_responses, "institution"),
        ),
        poscomp=(
            PosCompSchema(year=int(get_value(dict_responses, "year-poscomp")), score=get_value(dict_responses, "grades-poscomp"))
            if get_value(dict_responses, "grades-poscomp") and get_value(dict_responses, "year-poscomp")
            else None
        ),
        current_occupation=get_value(dict_responses, "current-job"),
        research=ResearchSchema(
            program="",
            field=ResearchFieldsSchema(
                primary=get_value(dict_responses, "primary-area", ""),
                secondary=get_value(dict_responses, "secondary-area", ""),
            ),
            semester=process_semester(get_value(dict_responses, "semester", "")),
            dedication_level=get_value(dict_responses, "intended-level", ""),
            will_apply_scholarship=str_for_bool(get_value(dict_responses, "scholarship", False))
        ),
        entry_semester=submission.entry_semester if submission.entry_semester is not None else process_semester(get_value(dict_responses, "semester", "")),
        relevant_information=get_value(dict_responses, "relevant-information", ""),
        about_this_program=get_value(dict_responses, "about-this-program", ""),
        stats=submission.stats.lower(),
        is_favorite=auth_user.id in favorite_ids,
        recommenders=recommenders,
        documents=documents,
        comments=activity,
        private_note=private_note.note if private_note is not None else "",
        labels=[ { "label": label.label, "color": label.color, "id": label.id } for label in labels ],
        user_bidding=bidding.label if bidding is not None else "",
        disabilities=len(json.loads(get_value(dict_responses, "disabilities", "[]"))) > 0,
        ethnicity_race=len(json.loads(get_value(dict_responses, "ethnicity-race", "[]"))) > 0,
        accept=accept,
        letter_sent=submission.letter_sent
    )