from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from auth import get_user_row
from config import settings
from database import Session
import oauth

router = APIRouter(tags=["auth"])


def _load_whitelist():
    try:
        content = settings.whitelist_file.read_text()
    except OSError:
        return set()
    entries = set()
    for line in content.splitlines():
        for item in line.split(","):
            item = item.strip()
            if item:
                entries.add(item)
    return entries


def _user_payload(user_id):
    user = get_user_row(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "nusp": user["nusp"],
        "role": user["role"],
    }


@router.get("/auth/login")
def login(request: Request):
    if settings.is_local and settings.dev_user_id:
        user = get_user_row(int(settings.dev_user_id))
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID does not exist")
        return _user_payload(user["id"])
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _user_payload(user_id)


async def _parse_body(request: Request):
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        return await request.json()
    form = await request.form()
    return {k: v for k, v in form.items()}


@router.post("/auth/login/senhaunica")
async def login_senhaunica(request: Request):
    body = await _parse_body(request)
    oauth_token = body.get("oauth_token")
    if not oauth_token:
        token, secret = oauth.get_request_token()
        request.session["oauth_token"] = token
        request.session["oauth_token_secret"] = secret
        return {"redirect_to": oauth.authorize_url(token)}

    verifier = body.get("oauth_verifier")
    secret = request.session.get("oauth_token_secret")
    if not secret:
        raise HTTPException(status_code=401, detail="Missing request token secret in session")
    try:
        access_token, access_secret = oauth.get_access_token(oauth_token, secret, verifier or None)
        info = oauth.get_user_info(access_token, access_secret)
    except Exception:
        raise HTTPException(status_code=500, detail="OAuth token exchange failed")

    nusp = str(info.get("loginUsuario") or "")
    if nusp not in _load_whitelist():
        raise HTTPException(status_code=403, detail="NUSP not authorized")
    email = info.get("emailPrincipalUsuario")
    name = info.get("nomeUsuario") or email
    if not email:
        raise HTTPException(status_code=500, detail="OAuth user without email")

    with Session() as s:
        row = s.execute(
            text('select * from "user" where email = :e'), {"e": email}
        ).mappings().first()
        if row:
            user_id = row["id"]
            if not row["nusp"]:
                s.execute(
                    text('update "user" set nusp = :n where id = :i'),
                    {"n": nusp, "i": user_id},
                )
        else:
            user_id = s.execute(
                text(
                    'insert into "user" (email, name, role, nusp, created_at)'
                    " values (:e, :n, 'teacher', :u, now()) returning id"
                ),
                {"e": email, "n": name, "u": nusp},
            ).scalar_one()
        s.commit()
    request.session["user_id"] = user_id
    return _user_payload(user_id)
