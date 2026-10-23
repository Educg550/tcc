"""Cliente OAuth 1.0a (HMAC-SHA1) do provedor local da Senha Única."""
from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client as OAuth1Client

from config import settings

# Segredos de request token em memória, entre as duas chamadas do fluxo.
REQUEST_SECRETS: dict[str, str] = {}


def _abs_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return settings.senhaunica_oauth_host.rstrip("/") + "/" + url.lstrip("/")


def _post_signed(url: str, token: str | None = None, token_secret: str | None = None,
                 verifier: str | None = None) -> requests.Response:
    client = OAuth1Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )
    uri, headers, body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=headers, data=body or {}, timeout=30)
    resp.raise_for_status()
    return resp


def get_request_token() -> tuple[str, str]:
    resp = _post_signed(_abs_url(settings.senhaunica_request_token_resource))
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_access_token(token: str, token_secret: str, verifier: str) -> tuple[str, str]:
    resp = _post_signed(
        _abs_url(settings.senhaunica_access_token_resource), token, token_secret, verifier
    )
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_user_info(access_token: str, access_token_secret: str) -> dict:
    resp = _post_signed(_abs_url("wsusuario/oauth/usuariousp"), access_token, access_token_secret)
    return resp.json()


def authorize_redirect_url(token: str) -> str:
    base = _abs_url(settings.senhaunica_authorize_url)
    return f"{base}?oauth_token={token}&callback_id={settings.senhaunica_callback_id}"
