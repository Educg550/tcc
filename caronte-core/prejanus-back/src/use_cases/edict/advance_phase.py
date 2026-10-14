from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.edict import Edict
from src.infra.database.models.edict_phase import EdictPhase
from sqlalchemy import text
from src.use_cases.dtos import UserDTO
from src.use_cases.exceptions import InsufficientRole
from src.utils import is_admin_role

class AdvancePhaseEdictSchema(BaseModel):
    id: int


class AdvancePhaseEdictResponse(AdvancePhaseEdictSchema):
    label: str


async def advance_phase_edict_by_id(
        session: AsyncSession, 
        session_forms: AsyncSession, 
        edict_id: int, 
        edict_phase_data: AdvancePhaseEdictSchema, 
        user: UserDTO
        ) -> AdvancePhaseEdictResponse:
    
    if not is_admin_role(user.role):
        raise InsufficientRole()

    edict_to_update = await session.get(Edict, edict_id)
    edict_phase = await session.get(EdictPhase, edict_phase_data.id)

    edict_to_update.phase = edict_phase.phase

    phase_mapper = {
        "inscricoes": 'Registration',
        "homologacao": 'Approval',
        "avaliacao": 'Completed',
        "encerrado": 'Completed'
    }
    
    query = text("""
        select * from change_form_phase(
            cast(:p_id as int),
            cast(:p_phase as form_phase)
        )
    """)
    params = {
        "p_id": int(edict_to_update.candidate_forms),
        "p_phase": phase_mapper[edict_phase.phase]
    }
    await session_forms.execute(
        query,
        params
    )
    await session_forms.commit()


    await session.commit()
    await session.refresh(edict_phase)

    return AdvancePhaseEdictResponse(
        id=edict_phase.id,
        label=edict_phase.phase
    )
