from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from config import settings
from database import get_db
from services import oauth

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
async def login(user=Depends(get_current_user)):
    return user


@router.post("/auth/login/senhaunica")
async def login_senhaunica(
    request: Request,
    payload: dict | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    payload = payload or {}
    oauth_token = payload.get("oauth_token")
    oauth_verifier = payload.get("oauth_verifier")

    if not oauth_token:
        token, secret = oauth.get_request_token()
        request.session["oauth_token"] = token
        request.session["oauth_token_secret"] = secret
        return {"redirect_to": oauth.authorize_url(token)}

    stored_token = request.session.get("oauth_token")
    stored_secret = request.session.get("oauth_token_secret")
    if not stored_secret or stored_token != oauth_token:
        raise HTTPException(status_code=401, detail="Sessão OAuth inválida")

    try:
        access_token, access_secret = oauth.get_access_token(
            oauth_token, stored_secret, oauth_verifier
        )
        info = oauth.get_user_data(access_token, access_secret)
    except oauth.OAuthError:
        raise HTTPException(status_code=500, detail="Falha na troca de tokens")
    except Exception:
        raise HTTPException(status_code=500, detail="Falha na troca de tokens")

    nusp = str(info.get("loginUsuario") or "")
    whitelist = oauth.load_whitelist()
    if whitelist is not None and nusp not in whitelist:
        raise HTTPException(status_code=401, detail="NUSP não autorizado")

    email = (info.get("emailPrincipalUsuario") or "").strip()
    name = info.get("nomeUsuario") or ""
    if not email:
        raise HTTPException(status_code=500, detail="Usuário sem e-mail")

    row = await db.execute(
        text('select id, name, email, nusp, role from "user" where email = :email'),
        {"email": email},
    )
    row = row.first()
    if row:
        user = dict(row._mapping)
    else:
        inserted = await db.execute(
            text(
                'insert into "user" (email, name, role, nusp, created_at) '
                "values (:email, :name, 'teacher', :nusp, now()) "
                "returning id, name, email, nusp, role"
            ),
            {"email": email, "name": name, "nusp": nusp},
        )
        user = dict(inserted.first()._mapping)
        await db.commit()

    request.session["user_id"] = user["id"]
    request.session.pop("oauth_token", None)
    request.session.pop("oauth_token_secret", None)
    return user
