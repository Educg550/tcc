from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client

from prejanus.config import settings


def _url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return settings.senhaunica_oauth_host.rstrip("/") + "/" + path.lstrip("/")


def _signed_post(url: str, token=None, token_secret=None, verifier=None):
    client = Client(
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )
    uri, headers, _body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp


def get_request_token():
    resp = _signed_post(_url(settings.senhaunica_request_token_resource))
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_access_token(token: str, token_secret: str, verifier: str):
    resp = _signed_post(
        _url(settings.senhaunica_access_token_resource),
        token=token,
        token_secret=token_secret,
        verifier=verifier,
    )
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_user_resource(access_token: str, access_secret: str) -> dict:
    resp = _signed_post(
        _url("/wsusuario/oauth/usuariousp"),
        token=access_token,
        token_secret=access_secret,
    )
    data = resp.json()
    if isinstance(data, list):
        data = data[0] if data else {}
    return data


_whitelist_cache = None


def load_whitelist() -> set:
    import os
    import re

    global _whitelist_cache
    if _whitelist_cache is not None:
        return _whitelist_cache
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        "data/nusp_whitelist.txt",
        os.path.join(os.path.dirname(here), "data", "nusp_whitelist.txt"),
    ]
    text = None
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            break
        except OSError:
            continue
    out = set()
    if text:
        for part in re.split(r"[\n,]", text):
            stripped = part.strip()
            if stripped:
                out.add(stripped)
    _whitelist_cache = out
    return out
    out = set()
    for part in re.split(r"[\n,]", text):
        stripped = part.strip()
        if stripped:
            out.add(stripped)
    return out
