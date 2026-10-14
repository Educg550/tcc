from datetime import date, datetime
import pytest

from src.infra.database.models.submission import  Submission
from src.infra.database.models.comment import  Comment
from src.infra.database.models.user import RolesEnum, User
from src.use_cases.submission.exceptions import SubmissionNotFound
from src.use_cases.submission.get_by_id import  get_submission_by_id
from src.use_cases.submission.schemas import SubmissionSchema

pytestmark = pytest.mark.anyio


@pytest.fixture
async def an_user(session):
    user = User(id=1, name="Professor Carlinhos", nusp="10726929", email="carlinhos@usp.br",role=RolesEnum.TEACHER)
    
    session.add(user)
    await session.commit()
    return user


@pytest.fixture
async def another_user(session):
    user = User(id=2, name="Secretaria Katia", nusp="10121919", email="katia@usp.br",role=RolesEnum.SECRETARY)
    
    session.add(user)
    await session.commit()
    return user


@pytest.fixture
async def some_comments_on_a_submission(session, submission_a: Submission, an_user: User, another_user: User):
    comment_1 = Comment(user_id=an_user.id, comment="First comment", created_at=datetime.fromisoformat("2024-01-01T00:00:00"))
    comment_2 = Comment(user_id=another_user.id, comment="Second comment", created_at=datetime.fromisoformat("2024-01-01T01:00:00"))
    comment_3 = Comment(user_id=an_user.id, comment="Third comment", created_at=datetime.fromisoformat("2024-01-01T02:00:00"))

    
    await submission_a.awaitable_attrs.comments
    submission_a.comments = [comment_1, comment_2, comment_3]

    session.add(submission_a)
    await session.commit()

    await session.refresh(submission_a) 
    await session.refresh(comment_1)


async def test_get_by_id_throws_not_found_if_submission_is_not_(session):
    with pytest.raises(SubmissionNotFound):
        await get_submission_by_id(2, 1, session)


@pytest.mark.usefixtures("submission_a", "submission_b")
async def test_get_by_id_return_info_for_specific_submission_and_it_applicant(session):
    submission = await get_submission_by_id(1, 1, session)

    assert isinstance(submission, SubmissionSchema)

    assert submission.id == 1
    assert submission.name == "Zé"
    assert submission.nationality == "Brasileiro"
    assert submission.birth_date == date(2000, 5, 5)
    assert submission.gender == "Masculino"

    assert submission.graduation.country == "Brasil"
    assert submission.graduation.institution == "USP"

    assert submission.poscomp is not None
    assert submission.poscomp.year == 2022
    assert submission.poscomp.score == 40

    assert submission.current_occupation == "Analista de sistemas"

    assert submission.research.field.primary == "Engenharia de software"
    assert submission.research.field.secondary == "Ciência de dados"
    assert submission.research.dedication_level == "Integral"
    assert submission.research.will_apply_scholarship is True


@pytest.mark.usefixtures("submission_a", "submission_b", "some_comments_on_a_submission")
async def test_get_by_id_return_info_for_specific_submission_and_it_applicant_with_the_comments_in_the_submission_included(session):
    submission = await get_submission_by_id(1, 1, session, include_comments=True)

    assert isinstance(submission, SubmissionSchema)

    assert submission.id == 1
    assert submission.name == "Zé"
    assert submission.nationality == "Brasileiro"
    assert submission.birth_date == date(2000, 5, 5)
    assert submission.gender == "Masculino"

    assert len(submission.comments) == 3
    
    first_comment = submission.comments[0]
    assert first_comment.comment == "First comment"
    assert first_comment.user.id == 1
    assert first_comment.user.name == "Professor Carlinhos"
    assert first_comment.created_at == datetime.fromisoformat("2024-01-01T00:00:00")
    
    second_comment = submission.comments[1]
    assert second_comment.comment == "Second comment"
    assert second_comment.user.id == 2
    assert second_comment.user.name == "Secretaria Katia"
    assert second_comment.created_at == datetime.fromisoformat("2024-01-01T01:00:00")
    
    third_comment = submission.comments[2]
    assert third_comment.comment == "Third comment"
    assert third_comment.user.id == 1
    assert third_comment.user.name == "Professor Carlinhos"
    assert third_comment.created_at == datetime.fromisoformat("2024-01-01T02:00:00")
