import base64
import hashlib
import hmac
import time
import uuid
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

from prejanus.config import settings


class OAuthError(Exception):
    pass


def _enc(value: str) -> str:
    from urllib.parse import quote

    return quote(str(value), safe="~")


def _sign(method: str, url: str, consumer_key: str, consumer_secret: str,
          token: str | None = None, token_secret: str = "", verifier: str | None = None,
          data: dict | None = None) -> tuple[str, dict, str | None]:
    oauth_params = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if token:
        oauth_params["oauth_token"] = token
    if verifier:
        oauth_params["oauth_verifier"] = verifier

    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    body_params = dict(data or {})
    all_params = {**oauth_params, **query, **body_params}

    base_url = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", "", ""))
    param_str = "&".join(f"{_enc(k)}={_enc(v)}" for k, v in sorted(all_params.items()))
    base_string = "&".join(_enc(part) for part in (method.upper(), base_url, param_str))

    key = f"{_enc(consumer_secret)}&{_enc(token_secret)}"
    digest = hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
    oauth_params["oauth_signature"] = base64.b64encode(digest).decode()

    header = "OAuth " + ", ".join(f'{_enc(k)}="{_enc(v)}"' for k, v in sorted(oauth_params.items()))
    headers = {"Authorization": header}
    body = None
    if data:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        body = urlencode(data)
    return url, headers, body


def _request(method: str, url: str, **kw) -> dict:
    url, headers, body = _sign(method, url, settings.senhaunica_consumer_key,
                               settings.senhaunica_consumer_secret, **kw)
    resp = requests.request(method, url, headers=headers, data=body, timeout=30)
    if resp.status_code != 200:
        raise OAuthError(f"oauth request failed: {resp.status_code} {resp.text}")
    return dict(parse_qsl(resp.text))


def _host_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    host = settings.senhaunica_oauth_host.rstrip("/")
    return f"{host}/{path.lstrip('/')}"


def get_request_token() -> tuple[str, str]:
    data = _request("POST", _host_url(settings.senhaunica_request_token_resource))
    return data["oauth_token"], data["oauth_token_secret"]


def authorize_url(token: str) -> str:
    base = _host_url(settings.senhaunica_authorize_url)
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}oauth_token={token}&callback_id={settings.senhaunica_callback_id}"


def get_access_token(token: str, token_secret: str, verifier: str) -> tuple[str, str]:
    data = _request("POST", _host_url(settings.senhaunica_access_token_resource),
                    token=token, token_secret=token_secret, verifier=verifier)
    return data["oauth_token"], data["oauth_token_secret"]


def get_user_info(access_token: str, access_secret: str) -> dict:
    url = _host_url("/wsusuario/oauth/usuariousp")
    url, headers, body = _sign("POST", url, settings.senhaunica_consumer_key,
                               settings.senhaunica_consumer_secret,
                               token=access_token, token_secret=access_secret)
    resp = requests.post(url, headers=headers, data=body, timeout=30)
    if resp.status_code != 200:
        raise OAuthError(f"user info failed: {resp.status_code} {resp.text}")
    return resp.json()
