import pytest
from datetime import date
from fastapi import HTTPException
from src.use_cases.edict.send_approved_emails import send_emails_to_approved_submissions

pytestmark = pytest.mark.anyio

class FakeBackgroundTasks:
    def add_task(self, task, args):
        pass

async def test_send_emails_to_approved_submissions_success(session, an_edict, submission_a):
    submission_a.advisor = "Prof. Orientador"
    submission_a.advisor_email = "orientador@example.com"
    await session.commit()

    confirmation_deadline = date.fromisoformat("2024-12-31")
    background_tasks = FakeBackgroundTasks()

    result = await send_emails_to_approved_submissions(
        session=session,
        edict_id=an_edict.id,
        confirmation_deadline=confirmation_deadline,
        background_tasks=background_tasks
    )

    assert result.message == "Emails sent successfully."
    assert len(result.email_list) == 1
    assert result.email_list[0] == "ze@email.com"
    assert result.confirmation_deadline == "2024-12-31"

async def test_send_emails_to_approved_submissions_no_approved_submissions(session, an_edict):
    confirmation_deadline = date.fromisoformat("2024-12-31")
    background_tasks = FakeBackgroundTasks()

    with pytest.raises(HTTPException) as exc_info:
        await send_emails_to_approved_submissions(
            session=session,
            edict_id=an_edict.id,
            confirmation_deadline=confirmation_deadline,
            background_tasks=background_tasks
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No approved submissions found for this edict."

@pytest.mark.usefixtures("an_edict")
async def test_send_emails_to_approved_submissions_edict_not_found(session):
    confirmation_deadline = date.fromisoformat("2024-12-31")
    background_tasks = FakeBackgroundTasks()

    with pytest.raises(HTTPException) as exc_info:
        await send_emails_to_approved_submissions(
            session=session,
            edict_id=999,  # Non-existent edict_id
            confirmation_deadline=confirmation_deadline,
            background_tasks=background_tasks
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Edict not found."
