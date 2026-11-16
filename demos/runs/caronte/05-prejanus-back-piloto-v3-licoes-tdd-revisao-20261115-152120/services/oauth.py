"""Cliente OAuth 1.0a da Senha Única (HMAC-SHA1)."""

import json
from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client

from config import settings


class OAuthError(Exception):
    pass


def _client(token=None, token_secret=None, verifier=None) -> Client:
    return Client(
        client_key=settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )


def _post(url: str, client: Client) -> dict:
    uri, headers, body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=headers, data=body if body else None,
                         timeout=60)
    if resp.status_code != 200:
        raise OAuthError(
            f"Falha na troca de token: {resp.status_code} {resp.text[:200]}"
        )
    return resp


def _url(path: str) -> str:
    return settings.senhaunica_oauth_host.rstrip("/") + "/" + path.lstrip("/")


def get_request_token() -> tuple[str, str]:
    resp = _post(_url(settings.senhaunica_request_token_resource), _client())
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_access_token(token: str, secret: str, verifier: str) -> tuple[str, str]:
    resp = _post(
        _url(settings.senhaunica_access_token_resource),
        _client(token, secret, verifier),
    )
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_user_info(token: str, secret: str) -> dict:
    resp = _post(
        _url("wsusuario/oauth/usuariousp"), _client(token, secret)
    )
    try:
        return resp.json()
    except json.JSONDecodeError:
        raise OAuthError("Resposta inválida do servidor de usuários")


def authorize_url(token: str) -> str:
    return (
        f"{_url(settings.senhaunica_authorize_url)}?oauth_token={token}"
        f"&callback_id={settings.senhaunica_callback_id}"
    )


def load_whitelist() -> set[str]:
    from pathlib import Path

    candidates = [
        Path("data/nusp_whitelist.txt"),
        Path(__file__).resolve().parent.parent / "data" / "nusp_whitelist.txt",
    ]
    content = None
    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
            break
        except OSError:
            continue
    if content is None:
        return set()
    return {
        part.strip()
        for part in content.replace(",", "\n").split("\n")
        if part.strip()
    }
