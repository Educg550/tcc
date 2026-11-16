from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deps import get_current_user, get_db
from models import User
from services import oauth

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "nusp": user.nusp,
        "role": user.role,
    }


@router.get("/login")
async def login(user: User = Depends(get_current_user)):
    return _user_dict(user)


class SenhaunicaBody(BaseModel):
    oauth_token: str | None = None
    oauth_verifier: str | None = None


@router.post("/login/senhaunica")
async def login_senhaunica(
    request: Request,
    body: SenhaunicaBody,
    db: AsyncSession = Depends(get_db),
):
    if not body.oauth_token:
        try:
            token, secret = oauth.get_request_token()
        except oauth.OAuthError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        secrets = request.session.get("oauth_secrets") or {}
        secrets[token] = secret
        request.session["oauth_secrets"] = secrets
        return {"redirect_to": oauth.authorize_url(token)}

    secrets = request.session.get("oauth_secrets") or {}
    secret = secrets.get(body.oauth_token)
    if secret is None:
        raise HTTPException(status_code=401, detail="Sessão OAuth inválida")

    try:
        access_token, access_secret = oauth.get_access_token(
            body.oauth_token, secret, body.oauth_verifier or ""
        )
        info = oauth.get_user_info(access_token, access_secret)
    except oauth.OAuthError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    nusp = str(info.get("loginUsuario") or "")
    whitelist = oauth.load_whitelist()
    if not nusp or nusp not in whitelist:
        raise HTTPException(status_code=403, detail="NUSP não autorizado")

    email = info.get("emailPrincipalUsuario") or ""
    name = info.get("nomeUsuario") or ""
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalars().first()
    if user is None:
        user = User(email=email, name=name, nusp=nusp, role="teacher")
        db.add(user)
        await db.flush()
    if user.nusp is None:
        user.nusp = nusp
    await db.commit()
    request.session["user_id"] = user.id
    return _user_dict(user)
