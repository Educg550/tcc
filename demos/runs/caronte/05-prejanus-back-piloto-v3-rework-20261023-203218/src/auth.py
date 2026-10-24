from fastapi import Depends, HTTPException, Request
from itsdangerous import URLSafeSerializer
from sqlalchemy import text

from src.config import settings
from src.db import get_db

serializer = URLSafeSerializer(settings.SECRET_KEY, salt="prejanus-session")
COOKIE_NAME = "session"
COOKIE_MAX_AGE = 28800

ADMIN_ROLES = {"admin", "administrator", "secretary", "secretaria", "coordinator", "coordenador"}


def dumps_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def loads_session(value: str) -> int | None:
    try:
        data = serializer.loads(value)
        return data.get("user_id")
    except Exception:
        return None


async def load_user(db, user_id: int) -> dict | None:
    result = await db.execute(
        text('SELECT id, email, name, role, nusp FROM "user" WHERE id = :i'), {"i": user_id}
    )
    row = result.first()
    return dict(row._mapping) if row else None


async def get_current_user(request: Request, db=Depends(get_db)) -> dict:
    user_id = None
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        user_id = loads_session(cookie)
    if user_id is None and settings.APP_ENV == "local" and settings.DEV_USER_ID:
        user_id = settings.DEV_USER_ID
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await load_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def is_admin(user: dict) -> bool:
    return user.get("role") in ADMIN_ROLES


async def require_admin(user=Depends(get_current_user)) -> dict:
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Administrative role required")
    return user
