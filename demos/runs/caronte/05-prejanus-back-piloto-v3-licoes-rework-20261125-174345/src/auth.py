from fastapi import HTTPException, Request, Response
from itsdangerous import URLSafeTimedSerializer

from .config import settings
from .db import fetch_one, prejanus_engine

COOKIE_NAME = "prejanus_session"
SESSION_MAX_AGE = 28800
ADMIN_ROLES = {"administrator", "secretary", "coordinator"}

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="prejanus-session")


def set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        _serializer.dumps({"user_id": user_id}),
        max_age=SESSION_MAX_AGE,
        secure=True,
        samesite="lax",
        httponly=True,
        path="/",
    )


def session_user_id(request: Request) -> int | None:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        data = _serializer.loads(raw, max_age=SESSION_MAX_AGE)
    except Exception:
        return None
    user_id = data.get("user_id") if isinstance(data, dict) else None
    return user_id if isinstance(user_id, int) else None


async def get_user(user_id: int) -> dict | None:
    return await fetch_one(
        prejanus_engine,
        'SELECT id, email, name, role, nusp FROM "user" WHERE id=:i',
        {"i": user_id},
    )


async def current_user(request: Request) -> dict:
    user_id = session_user_id(request)
    user = await get_user(user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def require_admin(user: dict) -> None:
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a perfis administrativos")


def public_user(user: dict) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"],
            "nusp": user["nusp"], "role": user["role"]}
