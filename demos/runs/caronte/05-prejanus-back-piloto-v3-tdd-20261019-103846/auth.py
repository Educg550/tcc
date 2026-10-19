from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}

_USER_COLS = 'id, name, email, nusp, role'


async def _fetch_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        text(f'select {_USER_COLS} from "user" where id = :uid'), {"uid": user_id}
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
):
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await _fetch_user(db, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID inválido")
        return user

    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = await _fetch_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


async def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    return user
