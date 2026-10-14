from functools import lru_cache
import os
from typing import Annotated
from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import UserNotAuthenticatedInSenhaunica
from src.infra.database.models.user import User
from src.infra.database.session import get_session
from src.settings import get_settings
from src.use_cases.dtos import UserDTO

FILE_PATH = "data/nusp_whitelist.txt"
os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

async def get_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> UserDTO:
    _settings = get_settings()

    # Local dev bypass: skip OAuth session check when APP_ENV=local and DEV_USER_ID is set.
    # The user row must already exist in the database.
    if _settings.APP_ENV == "local" and _settings.DEV_USER_ID is not None:
        user = await session.get(User, _settings.DEV_USER_ID)
        if not user:
            raise HTTPException(
                status_code=500,
                detail=f"DEV_USER_ID={_settings.DEV_USER_ID} not found in database"
            )
        return UserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            nusp=user.nusp,
            role=user.role,
        )

    user_id = request.session.get("user_id")

    if not user_id:
        raise UserNotAuthenticatedInSenhaunica

    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return UserDTO(
        id=user.id,
        email=user.email,
        name=user.name,
        nusp=user.nusp,
        role=user.role,
    )

@lru_cache
def load_whitelist():
    items = []
    with open(FILE_PATH, "r") as f:
        for row in f:
            row = row.strip()
            if row:
                items.extend(map(str, row.split(",")))
    return set(items)
