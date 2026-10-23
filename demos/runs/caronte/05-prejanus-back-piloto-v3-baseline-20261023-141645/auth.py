import base64
import hashlib
import hmac
import time
import uuid
from pathlib import Path
from urllib.parse import quote

import requests
from fastapi import HTTPException, Request
from sqlalchemy import text

from config import settings
from db import PrejanusSession

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


async def fetch_user(user_id: int) -> dict | None:
    async with PrejanusSession() as db:
        row = (
            await db.execute(
                text('select id, name, email, nusp, role from "user" where id = :i'),
                {"i": user_id},
            )
        ).first()
    if not row:
        return None
    return {"id": row.id, "name": row.name, "email": row.email, "nusp": row.nusp, "role": row.role}


async def current_user(request: Request) -> dict:
    if settings.app_env == "local" and settings.dev_user_id is not None:
        user = await fetch_user(settings.dev_user_id)
        if not user:
            raise HTTPException(500, "DEV_USER_ID points to a non-existent user")
        return user
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    user = await fetch_user(user_id)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user


def require_admin(user: dict) -> None:
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(403, "Administrative role required")


def load_whitelist() -> set[str]:
    path = Path("data/nusp_whitelist.txt")
    if not path.exists():
        return set()
    raw = path.read_text(encoding="utf-8")
    return {x.strip() for x in raw.replace(",", "\n").split("\n") if x.strip()}


# --- OAuth 1.0a (Senha Única) ---

def _oauth_params(token: str | None = None) -> dict:
    params = {
        "oauth_consumer_key": settings.senhaunica_consumer_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if token:
        params["oauth_token"] = token
    return params


def _sign(method: str, url: str, params: dict, token_secret: str = "") -> str:
    items = sorted(
        (quote(str(k), safe=""), quote(str(v), safe="")) for k, v in params.items()
    )
    param_str = "&".join(f"{k}={v}" for k, v in items)
    base = "&".join(
        [method.upper(), quote(url, safe=""), quote(param_str, safe="")]
    )
    key = f"{quote(settings.senhaunica_consumer_secret, safe='')}&{quote(token_secret, safe='')}"
    digest = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _oauth_post(url: str, params: dict, token_secret: str = "") -> requests.Response:
    signature = _sign("POST", url, params, token_secret)
    header = ", ".join(
        f'{k}="{quote(str(v), safe="")}"'
        for k, v in {**params, "oauth_signature": signature}.items()
    )
    resp = requests.post(url, headers={"Authorization": f"OAuth {header}"}, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(500, f"OAuth request failed: {resp.status_code}")
    return resp


def _host(resource: str) -> str:
    return settings.senhaunica_oauth_host.rstrip("/") + resource


def _parse_qs(resp: requests.Response) -> dict:
    out = {}
    for part in resp.text.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k] = v
    return out


def oauth_request_token() -> tuple[str, str]:
    resp = _oauth_post(_host(settings.senhaunica_request_token_resource), _oauth_params())
    data = _parse_qs(resp)
    return data["oauth_token"], data["oauth_token_secret"]


def oauth_access_token(token: str, secret: str, verifier: str) -> tuple[str, str]:
    params = _oauth_params(token)
    params["oauth_verifier"] = verifier
    resp = _oauth_post(_host(settings.senhaunica_access_token_resource), params, secret)
    data = _parse_qs(resp)
    return data["oauth_token"], data["oauth_token_secret"]


def oauth_user_info(token: str, secret: str) -> dict:
    resp = _oauth_post(_host("/wsusuario/oauth/usuariousp"), _oauth_params(token), secret)
    return resp.json()
