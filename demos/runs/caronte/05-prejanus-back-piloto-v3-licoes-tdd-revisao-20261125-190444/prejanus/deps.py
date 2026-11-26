from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus.config import settings
from prejanus.db import get_db
from prejanus.models import User

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID aponta para usuário inexistente")
        return user
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
    return user
