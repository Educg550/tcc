from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.private_note import PrivateNote
from src.use_cases.auth.get_or_register_user import UserDTO
from src.utils.get_edict_phase import check_edict_phase_by_submission


class PrivateNoteSchema(BaseModel):
    note: str


class UserResponseSchema(BaseModel):
    id: int
    name: str

class PrivateNoteResponseSchema(BaseModel):
    note: str
    created_at: datetime | None = None  
    updated_at: datetime | None = None  


async def insert_or_update_notes(submission_id: int, session: AsyncSession, note_data: PrivateNoteSchema, user: UserDTO) -> PrivateNoteResponseSchema:
    await check_edict_phase_by_submission(submission_id, ["avaliacao"], "notes", session)
    
    stmt = select(PrivateNote).where(
        PrivateNote.user_id == user.id,
        PrivateNote.submission_id == submission_id,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.note = note_data.note
        existing.updated_at = datetime.now(timezone.utc)
        obj = existing
    else:
        obj = PrivateNote(
            user_id=user.id,
            submission_id=submission_id,
            note=note_data.note,
            updated_at=datetime.now(timezone.utc)
        )
        session.add(obj)

    await session.commit()
    await session.refresh(obj)

    return PrivateNoteResponseSchema(
        note = obj.note,
        created_at = obj.created_at,
        updated_at = obj.updated_at
    )

