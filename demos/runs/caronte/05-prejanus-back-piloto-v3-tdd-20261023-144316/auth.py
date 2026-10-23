from pathlib import Path

import requests
from fastapi import HTTPException, Request
from oauthlib.oauth1 import Client as OAuth1Client
from oauthlib.oauth1 import (
    SIGNATURE_HMAC_SHA1,
    SIGNATURE_TYPE_BODY,
    SIGNATURE_TYPE_QUERY,
)
from oauthlib.oauth1.rfc5849 import SIGNATURE_TYPE_AUTH_HEADER
from sqlalchemy import text
from urllib.parse import parse_qsl

from config import settings
from database import SessionLocal

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


async def fetch_user(user_id: int) -> dict | None:
    async with SessionLocal() as session:
        row = await session.execute(
            text('select id, name, email, role, nusp from "user" where id = :id'),
            {"id": user_id},
        )
        r = row.fetchone()
        if not r:
            return None
        return {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "role": r.role,
            "nusp": r.nusp,
        }


async def get_current_user(request: Request) -> dict:
    user_id = request.session.get("user_id")
    user = None
    if user_id is not None:
        user = await fetch_user(int(user_id))
    if user is None and settings.app_env == "local" and settings.dev_user_id is not None:
        user = await fetch_user(settings.dev_user_id)
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID inválido")
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def require_admin(user: dict) -> None:
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")


def load_whitelist() -> set[str]:
    path = Path(settings.data_dir) / "nusp_whitelist.txt"
    values: set[str] = set()
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        for part in line.split(","):
            part = part.strip()
            if part:
                values.add(part)
    return values


def _callback_url() -> str:
    return f"{settings.base_url}/auth/login/senhaunica"


def _provider_url(resource: str) -> str:
    host = settings.senhaunica_oauth_host.rstrip("/")
    if not resource.startswith("/"):
        resource = "/" + resource
    return host + resource


def _oauth_request(
    url: str,
    token: str | None = None,
    secret: str | None = None,
    verifier: str | None = None,
    callback: str | None = None,
):
    """Envia a requisição OAuth tentando as variações do contrato.

    O RFC 5849 permite os parâmetros oauth no corpo form-urlencoded, no
    cabeçalho Authorization ou na query string; provedores da Senha Única
    variam entre as formas e quanto ao oauth_callback. Tenta todas as
    combinações e devolve a primeira resposta bem-sucedida.
    """
    combos = []
    if callback:
        combos.append((SIGNATURE_TYPE_BODY, callback))
        combos.append((SIGNATURE_TYPE_AUTH_HEADER, callback))
    combos.append((SIGNATURE_TYPE_BODY, None))
    combos.append((SIGNATURE_TYPE_AUTH_HEADER, None))
    combos.append((SIGNATURE_TYPE_QUERY, None))
    last = None
    for sig_type, cb in combos:
        try:
            client = OAuth1Client(
                settings.senhaunica_consumer_key,
                settings.senhaunica_consumer_secret,
                resource_owner_key=token,
                resource_owner_secret=secret,
                verifier=verifier,
                callback_uri=cb,
                signature_method=SIGNATURE_HMAC_SHA1,
                signature_type=sig_type,
            )
            uri, headers, body = client.sign(url, "POST")
            resp = requests.post(uri, headers=headers, data=body or "", timeout=30)
        except (requests.RequestException, ValueError, TypeError):
            continue
        if resp.status_code == 200:
            return resp
        last = resp
    return last


def _oauth_post(
    url: str,
    token: str | None = None,
    secret: str | None = None,
    verifier: str | None = None,
    callback: str | None = None,
) -> dict:
    resp = _oauth_request(url, token, secret, verifier, callback)
    if resp is None or resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Falha na troca de token OAuth")
    return dict(parse_qsl(resp.text))


def _oauth_post_json(url: str, token: str, secret: str) -> dict:
    resp = _oauth_request(url, token, secret)
    if resp is None or resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Falha ao consultar usuário USP")
    return resp.json()


def oauth_request_token() -> tuple[str, str]:
    url = _provider_url(settings.senhaunica_request_token_resource)
    data = _oauth_post(url, callback=_callback_url())
    return data["oauth_token"], data["oauth_token_secret"]


def oauth_access_token(token: str, secret: str, verifier: str) -> tuple[str, str]:
    url = _provider_url(settings.senhaunica_access_token_resource)
    data = _oauth_post(url, token, secret, verifier)
    return data["oauth_token"], data["oauth_token_secret"]


def oauth_user_data(token: str, secret: str) -> dict:
    url = _provider_url("/wsusuario/oauth/usuariousp")
    return _oauth_post_json(url, token, secret)


def authorize_redirect(token: str) -> str:
    return (
        f"{_provider_url(settings.senhaunica_authorize_url)}"
        f"?oauth_token={token}&callback_id={settings.senhaunica_callback_id}"
    )
