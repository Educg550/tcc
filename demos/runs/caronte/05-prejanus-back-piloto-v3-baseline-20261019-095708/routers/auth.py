from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    authorize_redirect_url,
    check_whitelist,
    get_current_user,
    senhaunica_access_token,
    senhaunica_request_token,
    senhaunica_user_data,
)
from config import settings
from database import get_db
from models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "nusp": user.nusp,
        "role": user.role,
    }


@router.get("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID does not match an existing user")
        request.session["user_id"] = user.id
        return _user_payload(user)
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _user_payload(user)


@router.post("/login/senhaunica")
async def login_senhaunica(
    request: Request,
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if not oauth_token:
        tokens = senhaunica_request_token()
        request.session["oauth_token"] = tokens.get("oauth_token")
        request.session["oauth_token_secret"] = tokens.get("oauth_token_secret")
        return {"redirect_to": authorize_redirect_url(tokens.get("oauth_token", ""))}

    secret = request.session.get("oauth_token_secret")
    if not secret or request.session.get("oauth_token") != oauth_token:
        raise HTTPException(status_code=401, detail="Missing request token secret")
    if not oauth_verifier:
        raise HTTPException(status_code=401, detail="Missing oauth_verifier")

    access = senhaunica_access_token(oauth_token, secret, oauth_verifier)
    data = senhaunica_user_data(access.get("oauth_token", ""), access.get("oauth_token_secret", ""))

    nusp = str(data.get("loginUsuario", "")).strip()
    name = str(data.get("nomeUsuario", "")).strip()
    email = str(data.get("emailPrincipalUsuario", "")).strip()
    if not check_whitelist(nusp):
        raise HTTPException(status_code=403, detail="NUSP not authorized")

    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalars().first()
    if user is None:
        user = User(email=email, name=name, nusp=nusp, role="teacher")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    request.session["user_id"] = user.id
    request.session.pop("oauth_token", None)
    request.session.pop("oauth_token_secret", None)
    return _user_payload(user)
