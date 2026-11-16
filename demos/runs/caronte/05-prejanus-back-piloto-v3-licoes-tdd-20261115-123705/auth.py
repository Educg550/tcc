import os
import unicodedata

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import get_db
from models import User

# Estado do fluxo OAuth 1.0a: segredo do request token por token e
# autorizações concluídas pelo callback do provedor.
PENDING_TOKENS: dict[str, str] = {}
AUTHORIZED_TOKENS: dict[str, int] = {}

ADMIN_ROLES = ("administrator", "secretary", "coordinator")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


def load_whitelist() -> set[str]:
    candidates = [
        os.path.join("data", "nusp_whitelist.txt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "nusp_whitelist.txt"),
        "/app/data/nusp_whitelist.txt",
        "/data/nusp_whitelist.txt",
        "/shared/data/nusp_whitelist.txt",
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            return {
                part.strip()
                for part in content.replace(",", "\n").splitlines()
                if part.strip()
            }
    return set()


def _session(request) -> dict:
    return request.scope.get("session") or {}


def _resolve_session_user(request) -> int | None:
    session = _session(request)
    uid = session.get("user_id")
    if uid is not None:
        return uid
    token = session.get("oauth_token")
    if token and token in AUTHORIZED_TOKENS:
        uid = AUTHORIZED_TOKENS.pop(token)
        session["user_id"] = uid
        return uid
    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID inexistente")
        return user

    uid = _resolve_session_user(request)
    if uid is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = await db.get(User, uid)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.role,
        "email": user.email,
        "nusp": user.nusp,
        "role": user.role,
    }
