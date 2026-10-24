from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text

import oauth
from config import settings
from db import PrejanusSession
from security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def user_dict(u):
    return {"id": u["id"], "name": u["name"], "email": u["email"], "nusp": u["nusp"], "role": u["role"]}


def load_whitelist():
    path = Path("data/nusp_whitelist.txt")
    if not path.exists():
        return set()
    tokens = set()
    for chunk in path.read_text(encoding="utf-8").replace("\n", ",").split(","):
        token = chunk.strip()
        if token:
            tokens.add(token)
    return tokens


@router.get("/login")
async def login(user=Depends(get_current_user)):
    return user_dict(user)


@router.post("/login/senhaunica")
async def login_senhaunica(request: Request):
    params = dict(request.query_params)
    try:
        body = await request.json()
        if isinstance(body, dict):
            for key in ("oauth_token", "oauth_verifier"):
                if key in body and key not in params:
                    params[key] = body[key]
    except Exception:
        pass

    token = params.get("oauth_token")
    verifier = params.get("oauth_verifier")

    if not token:
        try:
            request_token, request_secret = oauth.get_request_token()
        except oauth.OAuthError:
            raise HTTPException(status_code=500, detail="Failed to obtain request token")
        secrets = request.session.get("oauth_secrets") or {}
        secrets[request_token] = request_secret
        request.session["oauth_secrets"] = secrets
        return {"redirect_to": oauth.author_url(request_token)}

    secrets = request.session.get("oauth_secrets") or {}
    secret = secrets.get(token)
    if secret is None:
        raise HTTPException(status_code=401, detail="Missing request token secret in session")

    try:
        access_token, access_secret = oauth.get_access_token(token, secret, verifier)
        info = oauth.get_user_info(access_token, access_secret)
    except oauth.OAuthError:
        raise HTTPException(status_code=500, detail="OAuth token exchange failed")

    nusp = str(info.get("loginUsuario") or "")
    if nusp not in load_whitelist():
        raise HTTPException(status_code=403, detail="NUSP not authorized")

    email = (info.get("emailPrincipalUsuario") or "").strip()
    name = info.get("nomeUsuario") or ""
    if not email:
        raise HTTPException(status_code=500, detail="OAuth provider returned no email")

    async with PrejanusSession() as s:
        row = (await s.execute(text('select * from "user" where email = :e'), {"e": email})).mappings().first()
        if row is None:
            await s.execute(text(
                'insert into "user" (email, name, role, nusp, created_at) '
                "values (:e, :n, 'teacher', :u, now())"),
                {"e": email, "n": name, "u": nusp})
        else:
            await s.execute(text(
                'update "user" set name = :n, nusp = :u where id = :i'),
                {"n": name, "u": nusp, "i": row["id"]})
        await s.commit()
        user = (await s.execute(text('select * from "user" where email = :e'), {"e": email})).mappings().first()

    request.session["user_id"] = user["id"]
    return user_dict(user)
