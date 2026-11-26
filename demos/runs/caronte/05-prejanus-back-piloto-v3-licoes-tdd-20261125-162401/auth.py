from fastapi import HTTPException, Request

from config import settings
from database import SessionLocal
from models import User

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


async def get_current_user(request: Request) -> User:
    if settings.app_env == "local" and settings.dev_user_id is not None:
        async with SessionLocal() as db:
            user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID inválido")
        return user

    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    async with SessionLocal() as db:
        user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def require_admin(user: User) -> None:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
