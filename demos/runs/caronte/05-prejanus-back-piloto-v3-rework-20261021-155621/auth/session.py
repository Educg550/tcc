"""Sessão assinada e usuário corrente."""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from itsdangerous import URLSafeSerializer
from sqlalchemy import text

from config import settings
from database import get_db

serializer = URLSafeSerializer(settings.secret_key, salt="prejanus-session")
COOKIE_NAME = "prejanus_session"
COOKIE_MAX_AGE = 28800

ADMIN_ROLES = {"admin", "administrator", "secretary", "secretariat", "coordinator", "coordination"}


@dataclass
class CurrentUser:
    id: int
    name: str
    email: str
    nusp: str | None
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role in ADMIN_ROLES

    def as_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "email": self.email, "nusp": self.nusp, "role": self.role}


def set_session_cookie(response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        serializer.dumps({"user_id": user_id}),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )


def read_session_cookie(request: Request) -> int | None:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        data = serializer.loads(raw)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data.get("user_id")


async def get_current_user(request: Request, db=Depends(get_db)) -> CurrentUser:
    user_id = None
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user_id = settings.dev_user_id
    if user_id is None:
        user_id = read_session_cookie(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    row = (
        await db.execute(
            text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :i'),
            {"i": user_id},
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return CurrentUser(*row)


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Papel administrativo exigido")
    return user
