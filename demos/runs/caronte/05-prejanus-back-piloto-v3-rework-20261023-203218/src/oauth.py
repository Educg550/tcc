import base64
import hashlib
import hmac
import time
import uuid
from urllib.parse import parse_qsl, quote, urlencode

import httpx

from src.config import settings

_request_secrets: dict[str, str] = {}


def _url(resource: str) -> str:
    if resource.startswith("http://") or resource.startswith("https://"):
        return resource
    return settings.SENHAUNICA_OAUTH_HOST.rstrip("/") + "/" + resource.lstrip("/")


def _oauth_params(extra: dict | None = None) -> dict:
    params = {
        "oauth_consumer_key": settings.SENHAUNICA_CONSUMER_KEY,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_version": "1.0",
    }
    if extra:
        params.update(extra)
    return params


def _signature(method: str, url: str, params: dict, token_secret: str = "") -> str:
    items = sorted(
        (quote(str(k), safe=""), quote(str(v), safe="")) for k, v in params.items()
    )
    param_string = "&".join(f"{k}={v}" for k, v in items)
    base = "&".join(
        [method.upper(), quote(url, safe=""), quote(param_string, safe="")]
    )
    key = f"{quote(settings.SENHAUNICA_CONSUMER_SECRET, safe='')}&{quote(token_secret, safe='')}"
    digest = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _attempt(url: str, params: dict, token_secret: str, mode: str) -> httpx.Response:
    params = dict(params)
    params["oauth_signature"] = _signature("POST", url, params, token_secret)
    if mode == "body":
        return httpx.post(
            url,
            content=urlencode(params),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
    if mode == "query":
        return httpx.post(url, params=params, timeout=30)
    header = "OAuth " + ", ".join(
        f'{quote(str(k), safe="")}="{quote(str(v), safe="")}"'
        for k, v in sorted(params.items())
    )
    return httpx.post(url, headers={"Authorization": header}, timeout=30)


def _parse(response: httpx.Response) -> dict:
    data = dict(parse_qsl(response.text))
    if data:
        return data
    try:
        return response.json()
    except Exception:
        return {}


def _signed_request(url: str, params: dict, token_secret: str, required: tuple) -> dict:
    attempts = [("body", params), ("header", params), ("query", params)]
    with_callback = dict(params, oauth_callback="oob")
    attempts += [("body", with_callback), ("header", with_callback)]
    last = None
    for mode, attempt_params in attempts:
        response = _attempt(url, attempt_params, token_secret, mode)
        last = response
        if response.status_code < 400:
            data = _parse(response)
            if all(key in data for key in required):
                return data
    if last is not None:
        last.raise_for_status()
    raise RuntimeError(f"OAuth request failed: {url}")


def store_request_secret(token: str, secret: str) -> None:
    _request_secrets[token] = secret


def pop_request_secret(token: str) -> str:
    return _request_secrets.pop(token, "")


def authorize_url(token: str) -> str:
    url = settings.SENHAUNICA_AUTHORIZE_URL
    if not url.startswith("http://") and not url.startswith("https://"):
        url = settings.SENHAUNICA_OAUTH_HOST.rstrip("/") + "/" + url.lstrip("/")
    return f"{url}?oauth_token={token}&callback_id={settings.SENHAUNICA_CALLBACK_ID}"


def get_request_token() -> tuple[str, str]:
    data = _signed_request(
        _url(settings.SENHAUNICA_REQUEST_TOKEN_RESOURCE),
        _oauth_params(),
        "",
        ("oauth_token", "oauth_token_secret"),
    )
    return data["oauth_token"], data["oauth_token_secret"]


def get_access_token(token: str, token_secret: str, verifier: str) -> tuple[str, str]:
    params = _oauth_params({"oauth_token": token, "oauth_verifier": verifier})
    data = _signed_request(
        _url(settings.SENHAUNICA_ACCESS_TOKEN_RESOURCE),
        params,
        token_secret,
        ("oauth_token", "oauth_token_secret"),
    )
    return data["oauth_token"], data["oauth_token_secret"]


def get_user(access_token: str, access_secret: str) -> dict:
    params = _oauth_params({"oauth_token": access_token})
    data = _signed_request(
        _url("/wsusuario/oauth/usuariousp"), params, access_secret, ("loginUsuario",)
    )
    if isinstance(data, list):
        data = data[0] if data else {}
    return data
