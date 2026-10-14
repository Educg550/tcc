import uuid
from src.use_cases.edict.get_all_interactors import get_all_interactors
from src.use_cases.exceptions import InsufficientRole
from src.utils import is_admin_role
from sqlalchemy.ext.asyncio import AsyncSession
from src.use_cases.dtos import UserDTO
from pydantic import BaseModel
from typing import Optional
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from src.utils.download_file import PDF_STORAGE

class SectionsDocument(BaseModel):
    list_of_advisors: Optional[bool] = False
    relation: Optional[bool] = False
    approved: Optional[bool] = False
    refused: Optional[bool] = False
    underreview: Optional[bool] = False
    general_statistics: Optional[bool] = False
    show_emails: Optional[bool] = False


async def get_interactors_list(
    edict_id: int,
    section_document: SectionsDocument,
    auth_user: UserDTO,
    session: AsyncSession,
    session_forms: AsyncSession,
    background_tasks: BackgroundTasks = None,
    mode: str = "plain_text"
):
    if not is_admin_role(auth_user.role):
        raise InsufficientRole()
    
    if mode == "pdf":
        job_id = str(uuid.uuid4())
        pdf_path = PDF_STORAGE / f"{job_id}.pdf"

        if background_tasks is None:
            raise HTTPException(status_code=500)

        background_tasks.add_task(
            generate_pdf_file,
            filepath=str(pdf_path),
            edict_id=edict_id,
            section_document=section_document,
            auth_user=auth_user,
            session=session,
            session_forms=session_forms
        )

        return JSONResponse({"job_id": job_id, "status": "processing"})

    users_interacted = await get_all_interactors(
        edict_id=edict_id,
        user=auth_user,
        session=session,
        session_forms=session_forms,
        section_document=section_document,
        mode="plain_text"
    )
    return users_interacted


async def generate_pdf_file(filepath: str, edict_id: int, section_document: SectionsDocument, auth_user: UserDTO, session: AsyncSession, session_forms: AsyncSession):
    pdf_bytes = await get_all_interactors(
        edict_id=edict_id,
        user=auth_user,
        session=session,
        session_forms=session_forms,
        section_document=section_document,
        mode="pdf"
    )
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)