from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client

from config import settings


class OAuthError(Exception):
    pass


def _url(resource: str) -> str:
    if resource.startswith("http://") or resource.startswith("https://"):
        return resource
    return settings.senhaunica_oauth_host.rstrip("/") + "/" + resource.lstrip("/")


def _signed_post(url: str, token=None, token_secret=None, verifier=None):
    client = Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )
    uri, headers, body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise OAuthError(f"Falha OAuth: {resp.status_code} {resp.text}")
    return resp


def get_request_token() -> tuple[str, str]:
    resp = _signed_post(_url(settings.senhaunica_request_token_resource))
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_access_token(token: str, secret: str, verifier: str) -> tuple[str, str]:
    resp = _signed_post(
        _url(settings.senhaunica_access_token_resource),
        token=token,
        token_secret=secret,
        verifier=verifier,
    )
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_user_info(token: str, secret: str) -> dict:
    resp = _signed_post(
        _url("/wsusuario/oauth/usuariousp"), token=token, token_secret=secret
    )
    return resp.json()


def authorize_redirect(token: str) -> str:
    base = _url(settings.senhaunica_authorize_url)
    sep = "&" if "?" in base else "?"
    url = f"{base}{sep}oauth_token={token}"
    if settings.senhaunica_callback_id:
        url += f"&callback_id={settings.senhaunica_callback_id}"
    return url


def load_whitelist() -> set[str]:
    try:
        with open("data/nusp_whitelist.txt", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return set()
    return {p.strip() for p in content.replace(",", "\n").split() if p.strip()}
