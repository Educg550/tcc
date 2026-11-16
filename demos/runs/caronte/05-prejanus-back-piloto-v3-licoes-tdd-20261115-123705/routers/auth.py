import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import oauth_senhaunica as oauth
from auth import (
    AUTHORIZED_TOKENS,
    PENDING_TOKENS,
    _resolve_session_user,
    get_user_by_email,
    load_whitelist,
    user_dict,
)
from config import settings
from db import get_db
from models import User

router = APIRouter(tags=["auth"])


def _start_oauth(request: Request):
    try:
        token, secret = oauth.get_request_token()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha no request token: {exc}")
    session = request.scope.get("session") or {}
    session["oauth_token"] = token
    session["oauth_token_secret"] = secret
    PENDING_TOKENS[token] = secret
    return RedirectResponse(oauth.authorize_url(token), status_code=302)


@router.get("/auth/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID inexistente")
        return user_dict(user)

    params = dict(request.query_params)
    if params.get("oauth_token") and params.get("oauth_verifier"):
        return await _login_senhaunica(request, db)

    uid = _resolve_session_user(request)
    if uid is not None:
        user = await db.get(User, uid)
        if user is not None:
            return user_dict(user)
    return _start_oauth(request)


@router.post("/auth/login")
async def login_post(request: Request, db: AsyncSession = Depends(get_db)):
    return await _login_senhaunica(request, db)


async def _callback_params(request: Request) -> dict:
    params = dict(request.query_params)
    if not params.get("oauth_token"):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    params.update(body)
            except Exception:
                pass
        else:
            form = await request.form()
            params.update(dict(form))
    # Tolerância a nomes sem o prefixo oauth_.
    if not params.get("oauth_token") and params.get("token"):
        params["oauth_token"] = params["token"]
    if not params.get("oauth_verifier") and params.get("verifier"):
        params["oauth_verifier"] = params["verifier"]
    return params


async def _login_senhaunica(request: Request, db: AsyncSession, params: dict | None = None):
    if params is None:
        params = await _callback_params(request)
    token = params.get("oauth_token")
    verifier = params.get("oauth_verifier")

    if not token:
        try:
            token, secret = oauth.get_request_token()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Falha no request token: {exc}")
        session = request.scope.get("session") or {}
        session["oauth_token"] = token
        session["oauth_token_secret"] = secret
        PENDING_TOKENS[token] = secret
        return {"redirect_to": oauth.authorize_url(token)}

    if not verifier:
        raise HTTPException(status_code=401, detail="oauth_verifier ausente")

    session = request.scope.get("session") or {}
    secret = None
    if session.get("oauth_token") == token:
        secret = session.get("oauth_token_secret")
    if not secret:
        secret = PENDING_TOKENS.get(token)
    if not secret:
        raise HTTPException(status_code=401, detail="Segredo de retorno ausente")

    try:
        access_token, access_secret = oauth.get_access_token(token, secret, verifier)
        user_data = oauth.get_user_data(access_token, access_secret)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha na troca de tokens: {exc}")

    nusp = str(user_data.get("loginUsuario") or "")
    if nusp not in load_whitelist():
        raise HTTPException(status_code=401, detail="Usuário fora da whitelist")

    email = (user_data.get("emailPrincipalUsuario") or "").strip()
    name = user_data.get("nomeUsuario") or ""
    user = await get_user_by_email(db, email) if email else None
    if user is None:
        user = User(
            email=email,
            name=name,
            role="teacher",
            nusp=nusp,
            created_at=dt.datetime.now(dt.timezone.utc),
        )
        db.add(user)
        await db.commit()
    elif not user.nusp:
        user.nusp = nusp
        await db.commit()

    if session.get("oauth_token") == token:
        session["user_id"] = user.id
    else:
        AUTHORIZED_TOKENS[token] = user.id
    PENDING_TOKENS.pop(token, None)
    return user_dict(user)


@router.post("/auth/login/senhaunica")
async def login_senhaunica_post(request: Request, db: AsyncSession = Depends(get_db)):
    return await _login_senhaunica(request, db)


@router.get("/auth/login/senhaunica")
async def login_senhaunica_get(request: Request, db: AsyncSession = Depends(get_db)):
    return await _login_senhaunica(request, db)


@router.api_route("/auth/login/senhaunica/callback", methods=["GET", "POST"])
@router.api_route("/auth/callback", methods=["GET", "POST"])
@router.api_route("/callback", methods=["GET", "POST"])
async def oauth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    return await _login_senhaunica(request, db)


async def try_pending_login(request: Request, db: AsyncSession) -> bool:
    """Fallback: se o callback do provedor não chegou, consulta o provedor
    sobre o request token pendente na sessão e completa o login."""
    session = request.scope.get("session") or {}
    token = session.get("oauth_token")
    if not token:
        return False
    data = oauth.check_authorization(token)
    if not data:
        return False
    verifier = data.get("oauth_verifier")
    if not verifier:
        return False
    try:
        await _login_senhaunica(
            request, db, params={"oauth_token": token, "oauth_verifier": verifier}
        )
        return True
    except HTTPException:
        return False
