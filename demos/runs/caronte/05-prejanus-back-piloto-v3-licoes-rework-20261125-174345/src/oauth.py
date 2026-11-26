import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import quote, parse_qs

import requests

from .config import settings

# Segredos dos request tokens emitidos por esta instância.
TOKEN_SECRETS: dict[str, str] = {}


def _url(path: str) -> str:
    host = settings.SENHAUNICA_OAUTH_HOST.rstrip("/")
    return host + "/" + path.lstrip("/")


def authorize_url() -> str:
    url = settings.SENHAUNICA_AUTHORIZE_URL
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return _url(url)


def _signature(method: str, url: str, params: dict, consumer_secret: str, token_secret: str = "") -> str:
    encoded = "&".join(
        f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted(params.items())
    )
    base = "&".join([method.upper(), quote(url, safe=""), quote(encoded, safe="")])
    key = f"{quote(consumer_secret, safe='')}&{quote(token_secret or '', safe='')}"
    digest = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _authorization(method: str, url: str, token: str | None = None,
                   token_secret: str = "", verifier: str | None = None) -> str:
    oauth = {
        "oauth_consumer_key": settings.SENHAUNICA_CONSUMER_KEY,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if token:
        oauth["oauth_token"] = token
    if verifier:
        oauth["oauth_verifier"] = verifier
    oauth["oauth_signature"] = _signature(
        method, url, oauth, settings.SENHAUNICA_CONSUMER_SECRET, token_secret
    )
    return "OAuth " + ", ".join(f'{k}="{quote(str(v), safe="")}"' for k, v in sorted(oauth.items()))


def _post(url: str, authorization: str) -> requests.Response:
    resposta = requests.post(url, headers={"Authorization": authorization}, timeout=30)
    resposta.raise_for_status()
    return resposta


def request_token() -> tuple[str, str]:
    url = _url(settings.SENHAUNICA_REQUEST_TOKEN_RESOURCE)
    resposta = _post(url, _authorization("POST", url))
    dados = parse_qs(resposta.text)
    return dados["oauth_token"][0], dados["oauth_token_secret"][0]


def access_token(token: str, token_secret: str, verifier: str) -> tuple[str, str]:
    url = _url(settings.SENHAUNICA_ACCESS_TOKEN_RESOURCE)
    resposta = _post(url, _authorization("POST", url, token=token, token_secret=token_secret, verifier=verifier))
    dados = parse_qs(resposta.text)
    return dados["oauth_token"][0], dados["oauth_token_secret"][0]


def user_info(token: str, token_secret: str) -> dict:
    url = _url("wsusuario/oauth/usuariousp")
    resposta = _post(url, _authorization("POST", url, token=token, token_secret=token_secret))
    return resposta.json()
