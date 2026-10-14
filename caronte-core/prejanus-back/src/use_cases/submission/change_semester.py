from pydantic import BaseModel

from src.infra.database.models.submission import Submission
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.use_cases.submission.exceptions import SubmissionNotFound

class EntrySemesterSchema(BaseModel):
    semester: str


def process_semester(semester):
    # "Primeiro semestre.", "First semester."
    # "Segundo semestre.", "Second semester."
    if "primeiro" in semester.lower():
        semester = "Primeiro semestre."
    elif "segundo" in semester.lower():
        semester = "Segundo semestre."
    elif "first" in semester.lower():
        semester = "Primeiro semestre."
    elif "second" in semester.lower():
        semester = "Segundo semestre."
    return semester


async def change_semester_by_submission(
    submission_id: int, semester: str, session: AsyncSession
):
    query = select(Submission).where(Submission.id == submission_id)
    query_result = await session.execute(query)
    submission: Submission = query_result.scalars().one_or_none()

    if submission is None:
        raise SubmissionNotFound(submission_id)

    submission.entry_semester = process_semester(semester)
    await session.commit()
