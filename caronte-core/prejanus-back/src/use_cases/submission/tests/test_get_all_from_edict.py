from datetime import date
import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.models.edict import Edict
from src.infra.database.models.favorites import Favorites
from src.infra.database.models.submission import Submission
from src.infra.database.models.user import User
from src.use_cases.submission.get_all_from_edict import GraduationSchema, PosCompSchema, ResearchFieldsSchema, ResearchSchema, SubmissionSchema, query_get_all_submissions_from_edict

pytestmark = pytest.mark.anyio


@pytest.fixture
async def a_favored_submission(session: AsyncSession, an_edict: Edict, user_a: User):
    submission = Submission(
        edict_id = an_edict.id,
        special_courses = "Machine Learning",
        current_occupation = "Desenvolvedor Web",
        primary_field = "Machine Learning",
        secondary_field = "IA",
        dedication_level = "Parcial",
        scholarship_interest = False,
        additional_info = "Mais info sobre mim",
        first_heard ="Facebook",
        advisor = "Paulo"
    )

    session.add(submission)
    await session.flush()

    favorite = Favorites(user_id=user_a.id, submission_id=submission.id, created_at=date.today())
    session.add(favorite)
    await session.commit()
    await session.refresh(submission)

    return submission

async def test_get_all_submissions_returns_empty_list_when_no_submissions_are_found(session):
    submissions = await query_get_all_submissions_from_edict(session, edict_id=2, auth_user_id=1)

    assert submissions == []


@pytest.mark.usefixtures("submission_a", "submission_b", "a_favored_submission")
async def test_get_all_submissions_from_edict_return_list_of_all_submissions(session):
    submissions = await query_get_all_submissions_from_edict(session, edict_id=1, auth_user_id=1)

    assert len(submissions) == 2

    assert submissions[0] == SubmissionSchema(
        id=1,
        name="Zé",
        nationality="Brasileiro",
        gender="Masculino",
        phone_number="(11) 99123-1234",
        birth_date=date.fromisoformat("2000-05-05"),
        graduation=GraduationSchema(
            institution="USP",
            course="BCC",
            country="Brasil",
            year=2022
        ),
        poscomp=PosCompSchema(
            year=2022,
            score=40
        ),
        current_occupation="Analista de sistemas",
        research=ResearchSchema(
            program="Cálculo 1",
            dedication_level="Integral",
            field=ResearchFieldsSchema(
                primary="Engenharia de software",
                secondary="Ciência de dados"
            ),
            semester="1",
            will_apply_scholarship=True
        ),
        lattes_curriculum="meulattes.com",
        is_favorite=False
    )
    assert submissions[1] == SubmissionSchema(
        id=3,
        name="Mário",
        phone_number="(11) 99123-1234",
        nationality="Brasileiro",
        gender="Masculino",
        birth_date=date.fromisoformat("1980-05-05"),
        graduation=GraduationSchema(
            institution="USP",
            course="BCC",
            country="Brasil",
            year=2022
        ),
        poscomp=None,
        current_occupation="Desenvolvedor Web",
        research=ResearchSchema(
            program="Machine Learning",
            dedication_level="Parcial",
            field=ResearchFieldsSchema(
                primary="Machine Learning",
                secondary="IA"
            ),
            semester="1",
            will_apply_scholarship=False
        ),
        lattes_curriculum="meulattes.com",
        is_favorite=True
    )


@pytest.mark.usefixtures("submission_a", "submission_b", "a_favored_submission")
async def test_get_all_submissions_from_edict_return_only_favored_submissions_from_an_specified_user(session, user_a: User, an_edict: Edict):
    submissions = await query_get_all_submissions_from_edict(session, an_edict.id, auth_user_id=user_a.id, user_id=user_a.id)

    assert len(submissions) == 1

    assert submissions[0] == SubmissionSchema(
        id=3,
        name="Mário",
        nationality="Brasileiro",
        phone_number="(11) 99123-1234",
        gender="Masculino",
        birth_date=date.fromisoformat("1980-05-05"),
        graduation=GraduationSchema(
            institution="USP",
            course="BCC",
            country="Brasil",
            year=2022
        ),
        poscomp=None,
        current_occupation="Desenvolvedor Web",
        research=ResearchSchema(
            program="Machine Learning",
            dedication_level="Parcial",
            field=ResearchFieldsSchema(
                primary="Machine Learning",
                secondary="IA"
            ),
            semester="1",
            will_apply_scholarship=False
        ),
        lattes_curriculum="meulattes.com",
        is_favorite=True
    )
