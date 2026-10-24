"""Cliente OAuth 1.0a da Senha Única e whitelist de NUSPs."""
from pathlib import Path
from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client as OAuth1Client

from .config import settings

_REQUEST_SECRETS: dict[str, str] = {}


def _client(**kwargs) -> OAuth1Client:
    return OAuth1Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        **kwargs,
    )


def _post(url: str, client: OAuth1Client):
    _, headers, _ = client.sign(url, http_method="POST")
    resp = requests.post(url, headers=headers, timeout=30, verify=False)
    if resp.status_code >= 400:
        params = _parse_auth_header(headers.get("Authorization", ""))
        if params:
            resp = requests.post(url, data=params, timeout=30, verify=False)
            if resp.status_code >= 400:
                resp = requests.post(url, params=params, timeout=30, verify=False)
    return resp


def _parse_auth_header(value: str) -> dict:
    if not value or not value.lower().startswith("oauth"):
        return {}
    params = {}
    for part in value[5:].split(","):
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            params[key.strip()] = val.strip().strip('"')
    return params


def _parse_token_response(resp) -> dict:
    resp.raise_for_status()
    data = parse_qs(resp.text)
    if "oauth_token" not in data or "oauth_token_secret" not in data:
        try:
            payload = resp.json()
        except ValueError:
            raise RuntimeError("invalid token response")
        if not isinstance(payload, dict) or "oauth_token" not in payload:
            raise RuntimeError("invalid token response")
        return {
            "oauth_token": [payload["oauth_token"]],
            "oauth_token_secret": [payload.get("oauth_token_secret", "")],
        }
    return data


def _url(resource: str) -> str:
    if resource.startswith("http://") or resource.startswith("https://"):
        return resource
    return settings.senhaunica_oauth_host.rstrip("/") + resource


def start_login() -> str:
    client = _client(callback_uri="oob")
    resp = _post(_url(settings.senhaunica_request_token_resource), client)
    data = _parse_token_response(resp)
    token = data["oauth_token"][0]
    _REQUEST_SECRETS[token] = data["oauth_token_secret"][0]
    return token


def exchange(token: str, verifier: str) -> tuple[str, str]:
    secret = _REQUEST_SECRETS.pop(token, None)
    if secret is None:
        raise RuntimeError("oauth_token desconhecido")
    client = _client(
        resource_owner_key=token,
        resource_owner_secret=secret,
        verifier=verifier,
    )
    resp = _post(_url(settings.senhaunica_access_token_resource), client)
    data = _parse_token_response(resp)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def user_info(access_token: str, access_secret: str) -> dict:
    client = _client(
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    resp = _post(_url("/wsusuario/oauth/usuariousp"), client)
    resp.raise_for_status()
    return resp.json()


def _whitelist_entries() -> set[str] | None:
    here = Path(__file__).resolve()
    candidates = [
        Path("data/nusp_whitelist.txt"),
        here.parents[1] / "data" / "nusp_whitelist.txt",
        here.parents[2] / "data" / "nusp_whitelist.txt",
    ]
    for path in candidates:
        if path.exists():
            raw = path.read_text(encoding="utf-8")
            return {x.strip() for x in raw.replace(",", "\n").split("\n") if x.strip()}
    return None


def nusp_allowed(nusp: str) -> bool:
    entries = _whitelist_entries()
    if entries is None:
        return False
    return nusp in entries
