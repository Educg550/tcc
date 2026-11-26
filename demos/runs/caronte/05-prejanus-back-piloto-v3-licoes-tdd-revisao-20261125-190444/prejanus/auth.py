from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import oauth
from prejanus.config import settings
from prejanus.db import get_db
from prejanus.deps import get_current_user
from prejanus.models import User

router = APIRouter(tags=["auth"])


def _user_dict(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "nusp": user.nusp, "role": user.role}


@router.get("/auth/login")
async def login(user: User = Depends(get_current_user)):
    return _user_dict(user)


@router.post("/auth/login/senhaunica")
async def login_senhaunica(
    request: Request,
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if oauth_token is None:
        token, secret = oauth.get_request_token()
        request.session["oauth_token"] = token
        request.session["oauth_token_secret"] = secret
        authorize = oauth._url(settings.senhaunica_authorize_url)
        redirect_to = (
            f"{authorize}?oauth_token={token}&callback_id={settings.senhaunica_callback_id}"
        )
        return {"redirect_to": redirect_to}

    secret = request.session.get("oauth_token_secret")
    if not secret:
        raise HTTPException(status_code=401, detail="Sessão sem segredo de retorno")
    try:
        access_token, access_secret = oauth.get_access_token(oauth_token, secret, oauth_verifier or "")
        data = oauth.get_user_resource(access_token, access_secret)
    except HTTPException:
        raise
    except Exception as exc:  # falha nas trocas de token
        raise HTTPException(status_code=500, detail=f"Falha na autenticação: {exc}") from exc

    nusp = str(
        data.get("loginUsuario") or data.get("nusp") or data.get("idUsuario") or ""
    ).strip()
    whitelist = oauth.load_whitelist()
    if nusp not in whitelist:
        raise HTTPException(status_code=403, detail="Usuário fora da whitelist")

    email = str(
        data.get("emailPrincipalUsuario")
        or data.get("emailUsuario")
        or data.get("email")
        or ""
    ).strip()
    name = str(data.get("nomeUsuario") or data.get("name") or "").strip()
    if not email:
        raise HTTPException(status_code=500, detail="Provedor não retornou e-mail")

    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None:
        user = User(email=email, name=name or email, role="teacher", nusp=nusp)
        db.add(user)
        await db.flush()
    elif not user.nusp:
        user.nusp = nusp
    await db.commit()
    request.session["user_id"] = user.id
    return _user_dict(user)
