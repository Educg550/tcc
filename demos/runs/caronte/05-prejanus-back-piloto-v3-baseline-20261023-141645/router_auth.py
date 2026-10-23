from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy import text

import auth
from auth import current_user
from config import settings
from db import PrejanusSession

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
async def login(user=Depends(current_user)):
    return user


@router.post("/auth/login/senhaunica")
async def login_senhaunica(request: Request, payload: dict | None = Body(default=None)):
    payload = payload or {}
    oauth_token = payload.get("oauth_token")
    if not oauth_token:
        token, secret = auth.oauth_request_token()
        request.session["oauth_token"] = token
        request.session["oauth_token_secret"] = secret
        host = settings.senhaunica_oauth_host.rstrip("/")
        redirect_to = (
            f"{host}{settings.senhaunica_authorize_url}"
            f"?oauth_token={token}&callback_id={settings.senhaunica_callback_id}"
        )
        return {"redirect_to": redirect_to}

    verifier = payload.get("oauth_verifier")
    stored_secret = request.session.get("oauth_token_secret")
    if not stored_secret or request.session.get("oauth_token") != oauth_token:
        raise HTTPException(401, "Missing request token secret for this session")

    access_token, access_secret = auth.oauth_access_token(oauth_token, stored_secret, verifier)
    info = auth.oauth_user_info(access_token, access_secret)
    nusp = str(info.get("loginUsuario", "")).strip()
    if nusp not in auth.load_whitelist():
        raise HTTPException(403, "NUSP not authorized")
    email = info.get("emailPrincipalUsuario")
    name = info.get("nomeUsuario")

    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text('select id from "user" where email = :e'), {"e": email}
            )
        ).first()
        if row:
            user_id = row.id
        else:
            result = await db.execute(
                text(
                    'insert into "user" (email, name, role, nusp, created_at) '
                    "values (:e, :n, 'teacher', :u, now()) returning id"
                ),
                {"e": email, "n": name, "u": nusp},
            )
            user_id = result.scalar()
            await db.commit()
    request.session["user_id"] = user_id
    return await auth.fetch_user(user_id)
