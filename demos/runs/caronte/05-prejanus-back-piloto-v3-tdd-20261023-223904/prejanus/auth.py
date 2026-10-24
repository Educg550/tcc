from fastapi import Depends, HTTPException, Request
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus.config import settings
from prejanus.db import get_db
from prejanus.models import User

COOKIE_NAME = "prejanus_session"
SESSION_MAX_AGE = 8 * 3600
ADMIN_ROLES = {"administrator", "secretary", "coordinator"}

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="prejanus-session")


def read_session(request: Request) -> dict:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return {}
    try:
        data = _serializer.loads(raw, max_age=SESSION_MAX_AGE)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def write_session(response, data: dict) -> None:
    response.set_cookie(
        COOKIE_NAME,
        _serializer.dumps(data),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(500, "DEV_USER_ID does not reference an existing user")
        return user
    data = read_session(request)
    user_id = data.get("user_id")
    if user_id is None:
        raise HTTPException(401, "Not authenticated")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "Not authenticated")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Administrative role required")
    return user
