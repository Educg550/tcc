from fastapi import APIRouter, HTTPException, Request, Response
from urllib.parse import quote

from .. import oauth
from ..auth import get_user, public_user, session_user_id, set_session
from ..config import nusp_whitelist, settings
from ..db import fetch_one, prejanus_engine, run

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request, response: Response):
    user_id = session_user_id(request)
    user = await get_user(user_id) if user_id is not None else None
    if user is None and settings.is_local and settings.DEV_USER_ID:
        user = await get_user(settings.DEV_USER_ID)
        if user is not None:
            set_session(response, user["id"])
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return public_user(user)


@router.post("/login/senhaunica")
async def login_senhaunica(request: Request, response: Response,
                           oauth_token: str | None = None, oauth_verifier: str | None = None):
    if not oauth_token:
        token, secret = oauth.request_token()
        oauth.TOKEN_SECRETS[token] = secret
        redirect = f"{oauth.authorize_url()}?oauth_token={quote(token)}"
        if settings.SENHAUNICA_CALLBACK_ID:
            redirect += f"&callback_id={quote(settings.SENHAUNICA_CALLBACK_ID)}"
        return {"redirect_to": redirect}

    secret = oauth.TOKEN_SECRETS.pop(oauth_token, "")
    access, access_secret = oauth.access_token(oauth_token, secret, oauth_verifier)
    info = oauth.user_info(access, access_secret)
    nusp = str(info.get("loginUsuario") or "")
    if nusp not in nusp_whitelist():
        raise HTTPException(status_code=403, detail="NUSP não autorizado")
    user = await fetch_one(prejanus_engine, 'SELECT * FROM "user" WHERE nusp=:n', {"n": nusp})
    if user is None:
        email = info.get("emailPrincipalUsuario") or ""
        user = await fetch_one(prejanus_engine, 'SELECT * FROM "user" WHERE email=:e', {"e": email})
    if user is None:
        rows = await run(
            prejanus_engine,
            'INSERT INTO "user" (email, name, role, nusp, created_at) '
            "VALUES (:e, :n, 'teacher', :u, now()) RETURNING id, email, name, role, nusp",
            {"e": info.get("emailPrincipalUsuario") or "",
             "n": info.get("nomeUsuario") or "",
             "u": nusp},
        )
        user = rows[0]
    set_session(response, user["id"])
    return public_user(user)
