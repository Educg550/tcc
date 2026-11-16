from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from oauthlib.oauth1 import Client
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import NUSP_WHITELIST, settings
from db import FormsSessionLocal, SessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_forms_db():
    async with FormsSessionLocal() as session:
        yield session


async def get_user(db: AsyncSession, user_id: int) -> dict | None:
    result = await db.execute(
        text('select id, name, email, nusp, role from "user" where id = :id'),
        {"id": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_user_by_email(db: AsyncSession, email: str) -> dict | None:
    result = await db.execute(
        text('select id, name, email, nusp, role from "user" where email = :email'),
        {"email": email},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await get_user(db, settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID does not exist")
        return user
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in {"administrator", "secretary", "coordinator"}:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def _host() -> str:
    host = settings.senhaunica_oauth_host
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return "http://" + host.rstrip("/")


def _oauth_post(url: str, client: Client) -> dict:
    uri, headers, body = client.sign(url, "POST")
    response = requests.post(uri, headers=headers, data=body or None, timeout=30)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="OAuth request failed")
    data = parse_qs(response.text)
    return {k: v[0] for k, v in data.items() if v}


def _oauth_json(url: str, client: Client) -> dict:
    uri, headers, body = client.sign(url, "POST")
    response = requests.post(uri, headers=headers, data=body or None, timeout=30)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch user data")
    return response.json()


@router.get("/login")
async def login(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "nusp": user["nusp"],
        "role": user["role"],
    }


@router.post("/login/senhaunica")
async def login_senhaunica(
    request: Request,
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
):
    if oauth_token is None or oauth_verifier is None:
        if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
            form = await request.form()
            oauth_token = oauth_token or form.get("oauth_token")
            oauth_verifier = oauth_verifier or form.get("oauth_verifier")
        if not oauth_token:
            client = Client(settings.senhaunica_consumer_key, settings.senhaunica_consumer_secret)
            data = _oauth_post(_host() + settings.senhaunica_request_token_resource, client)
            request.session["oauth_token_secret"] = data.get("oauth_token_secret", "")
            request.session["oauth_token"] = data.get("oauth_token", "")
            query = urlencode(
                {
                    "oauth_token": data.get("oauth_token", ""),
                    "callback_id": settings.senhaunica_callback_id,
                }
            )
            authorize = settings.senhaunica_authorize_url
            if authorize.startswith("http"):
                redirect_to = authorize + "?" + query
            else:
                redirect_to = _host() + authorize + "?" + query
            return {"redirect_to": redirect_to}

    secret = request.session.get("oauth_token_secret")
    if not secret:
        raise HTTPException(status_code=401, detail="Missing request token secret")
    client = Client(
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=secret,
        verifier=oauth_verifier,
    )
    data = _oauth_post(_host() + settings.senhaunica_access_token_resource, client)
    access_token = data.get("oauth_token", "")
    access_secret = data.get("oauth_token_secret", "")
    if not access_token:
        raise HTTPException(status_code=500, detail="Access token exchange failed")

    client = Client(
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    info = _oauth_json(_host() + "/wsusuario/oauth/usuariousp", client)
    nusp = str(info.get("loginUsuario", ""))
    if nusp not in NUSP_WHITELIST:
        raise HTTPException(status_code=403, detail="NUSP not authorized")
    email = info.get("emailPrincipalUsuario", "")
    name = info.get("nomeUsuario", "")

    async with SessionLocal() as db:
        existing = await get_user_by_email(db, email)
        if existing is not None:
            user_row = existing
        else:
            result = await db.execute(
                text(
                    'insert into "user" (email, name, role, nusp, created_at) '
                    "values (:email, :name, 'teacher', :nusp, :now) returning id, name, email, nusp, role"
                ),
                {"email": email, "name": name, "nusp": nusp, "now": datetime.now(timezone.utc)},
            )
            user_row = dict(result.mappings().first())
            await db.commit()

    request.session["user_id"] = user_row["id"]
    return {
        "id": user_row["id"],
        "name": user_row["name"],
        "email": user_row["email"],
        "nusp": user_row["nusp"],
        "role": user_row["role"],
    }
