from urllib.parse import parse_qs, urlencode

import requests
from fastapi import Depends, HTTPException, Request
from oauthlib.oauth1 import Client as OAuth1Client
from sqlalchemy.ext.asyncio import AsyncSession

from config import load_nusp_whitelist, settings
from database import get_db
from models import User

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Administrative role required")
    return user


def _signed_post(url: str, client: OAuth1Client) -> dict:
    uri, headers, body = client.sign(url, http_method="POST")
    try:
        resp = requests.post(uri, headers=headers, data=body, timeout=30)
        resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=500, detail="OAuth request failed")
    return {k: v[0] for k, v in parse_qs(resp.text).items()}


def _signed_post_json(url: str, client: OAuth1Client) -> dict:
    uri, headers, body = client.sign(url, http_method="POST")
    try:
        resp = requests.post(uri, headers=headers, data=body, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="OAuth request failed")


def _client(resource_owner_key=None, resource_owner_secret=None, verifier=None):
    return OAuth1Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
        verifier=verifier,
    )


def senhaunica_request_token() -> dict:
    url = settings.senhaunica_oauth_host.rstrip("/") + settings.senhaunica_request_token_resource
    return _signed_post(url, _client())


def senhaunica_access_token(token: str, secret: str, verifier: str) -> dict:
    url = settings.senhaunica_oauth_host.rstrip("/") + settings.senhaunica_access_token_resource
    return _signed_post(url, _client(token, secret, verifier))


def senhaunica_user_data(access_token: str, access_secret: str) -> dict:
    url = settings.senhaunica_oauth_host.rstrip("/") + "/wsusuario/oauth/usuariousp"
    return _signed_post(url, _client(access_token, access_secret))


def authorize_redirect_url(oauth_token: str) -> str:
    base = settings.senhaunica_oauth_host.rstrip("/") + settings.senhaunica_authorize_url
    params = {"oauth_token": oauth_token}
    if settings.senhaunica_callback_id:
        params["callback_id"] = settings.senhaunica_callback_id
    return base + "?" + urlencode(params)


def check_whitelist(nusp: str) -> bool:
    return nusp in load_nusp_whitelist()
