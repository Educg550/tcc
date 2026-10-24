import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text

import src.auth as auth
import src.oauth as oauth
from src.db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _whitelist_paths():
    return [
        Path("data/nusp_whitelist.txt"),
        Path(__file__).resolve().parents[2] / "data" / "nusp_whitelist.txt",
    ]


def load_whitelist() -> set[str]:
    for path in _whitelist_paths():
        if path.is_file():
            return {t.strip() for t in re.split(r"[\n,]", path.read_text()) if t.strip()}
    return set()


@router.get("/login")
async def login(user=Depends(auth.get_current_user)):
    return user


@router.post("/login/senhaunica")
async def login_senhaunica(
    response: Response,
    db=Depends(get_db),
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
):
    if not oauth_token or not oauth_verifier:
        token, secret = oauth.get_request_token()
        oauth.store_request_secret(token, secret)
        return {"redirect_to": oauth.authorize_url(token)}

    token_secret = oauth.pop_request_secret(oauth_token)
    access_token, access_secret = oauth.get_access_token(oauth_token, token_secret, oauth_verifier)
    info = oauth.get_user(access_token, access_secret)
    nusp = str(info.get("loginUsuario") or "")
    if nusp not in load_whitelist():
        raise HTTPException(status_code=401, detail="NUSP not authorized")
    email = info.get("emailPrincipalUsuario")
    name = info.get("nomeUsuario") or ""
    if not email:
        raise HTTPException(status_code=401, detail="Missing user email")

    result = await db.execute(
        text('SELECT id FROM "user" WHERE email = :e'), {"e": email}
    )
    row = result.first()
    if row:
        user_id = row[0]
    else:
        result = await db.execute(
            text(
                'INSERT INTO "user"(email, name, role, nusp, created_at) '
                "VALUES(:e, :n, 'teacher', :u, now()) RETURNING id"
            ),
            {"e": email, "n": name, "u": nusp},
        )
        user_id = result.scalar()
    user = await auth.load_user(db, user_id)
    response.set_cookie(
        auth.COOKIE_NAME,
        auth.dumps_session(user_id),
        max_age=auth.COOKIE_MAX_AGE,
        secure=True,
        samesite="lax",
        httponly=True,
    )
    return user
