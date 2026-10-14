from fastapi import (
    HTTPException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Literal
from src.infra.database.models.edict_form_mapping import EdictFormMapping
from src.use_cases.auth.get_or_register_user import UserDTO


async def update_mapping(
    form_type: Literal["recommender", "candidate"],
    mapping_id: int,
    edict_id: int,
    new_mapping: dict,
    version: int,
    auth_user: UserDTO,
    session: AsyncSession,
):

    mapping = (
        await session.execute(
            select(EdictFormMapping).where(
                EdictFormMapping.id == mapping_id,
                EdictFormMapping.edict_id == edict_id,
                EdictFormMapping.form_type == form_type,
                EdictFormMapping.form_version == version,
            )
        )
    ).scalar_one_or_none()

    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail="Mapping not found",
        )

    mapping.mapping = new_mapping
    await session.commit()
    await session.refresh(mapping)

    return mapping
