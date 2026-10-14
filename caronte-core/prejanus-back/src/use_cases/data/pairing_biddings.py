import uuid
import csv
from src.infra.database.models.edict import Edict
from src.infra.database.models.labels import Labels
from src.infra.database.models.submission import Submission
from src.infra.database.models.user import User
from src.infra.database.models.user_edict_slots import UserEdictSlots
from src.use_cases.exceptions import InsufficientRole
from sqlalchemy.orm import selectinload, with_loader_criteria
from src.use_cases.forms.get_forms_by_id import get_forms_by_id
from src.utils import is_admin_role
from sqlalchemy.ext.asyncio import AsyncSession
from src.use_cases.dtos import UserDTO
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select

from pathlib import Path

PDF_STORAGE = Path("/tmp")


async def get_pairing_biddings(
    edict_id: int,
    auth_user: UserDTO,
    session: AsyncSession,
    session_forms: AsyncSession,
    background_tasks: BackgroundTasks = None,
):
    if not is_admin_role(auth_user.role):
        raise InsufficientRole()
    
    job_id = str(uuid.uuid4())
    csv_path = PDF_STORAGE / f"{job_id}.csv"

    if background_tasks is None:
        raise HTTPException(status_code=500)

    background_tasks.add_task(
        generate_file,
        filepath=str(csv_path),
        edict_id=edict_id,
        auth_user=auth_user,
        session=session,
        session_forms=session_forms
    )

    return JSONResponse({"job_id": job_id, "status": "processing"})


async def generate_file(
        filepath: str, 
        edict_id: int, 
        auth_user: UserDTO, 
        session: AsyncSession,
        session_forms: AsyncSession
    ):

    csv_filename = filepath

    edict_query = (
        select(Edict)
        .where(Edict.id == edict_id)
        .options(
            selectinload(Edict.submissions).
            joinedload(Submission.labels).
            joinedload(Labels.user).
            joinedload(User.edicts_with_slots),
            with_loader_criteria(
                UserEdictSlots,
                lambda cls: cls.edict_id == edict_id,
                include_aliases=True
            ),
            with_loader_criteria(
                Labels,
                Labels.context_type == "bidding",
                include_aliases=True
            )
        )
    )
    edict_result = await session.execute(edict_query)
    edict: Edict | None = edict_result.scalar_one_or_none()

    await session.close()

    candidate_forms_submissions = await get_forms_by_id(session_forms, edict.candidate_forms)
    await session_forms.close()
    recommenders_by_id = {}
    for r in candidate_forms_submissions:
        id_submission = r.get("id", None)
        if id_submission is None:
            continue
        recommenders_by_id[id_submission] = r.get("email", "")

    data = []
    fieldnames = [ "#" ]
    known_users = set()

    for submission in edict.submissions:
        for label in submission.labels:
            user_email = label.user.email
            if user_email not in known_users:
                known_users.add(user_email)
                fieldnames.append(user_email)

    slots_row = {"#": "slots"}
    for user_email in fieldnames[1:]:
        user = None
        for submission in edict.submissions:
            for label in submission.labels:
                if label.user.email == user_email:
                    user = label.user
                    break
            if user:
                break
        slot = user.edicts_with_slots[0].slots if user.edicts_with_slots else 0
        slots_row[user_email] = slot
    data.append(slots_row)

    for submission in edict.submissions:
        candidate_email = recommenders_by_id.get(submission.candidate_form_id, None)
        if candidate_email is None:
            continue
        row = { "#": candidate_email }
        for label in submission.labels:
            user_email = label.user.email
            row[user_email] = label.label or ""
        data.append(row)

    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)