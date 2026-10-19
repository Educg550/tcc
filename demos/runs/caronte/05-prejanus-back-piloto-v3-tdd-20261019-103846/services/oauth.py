from urllib.parse import parse_qs, urlencode

import requests
from oauthlib.oauth1 import Client

from config import settings


class OAuthError(Exception):
    pass


def _client(token=None, secret=None, verifier=None):
    return Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=secret,
        verifier=verifier,
    )


def _post(url, client):
    uri, headers, body = client.sign(url, "POST")
    resp = requests.post(uri, headers=headers, data=body, timeout=30)
    if resp.status_code != 200:
        raise OAuthError(f"falha OAuth: {resp.status_code}")
    return resp


def get_request_token():
    url = settings.senhaunica_oauth_host + settings.senhaunica_request_token_resource
    resp = _post(url, _client())
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_access_token(token, secret, verifier):
    url = settings.senhaunica_oauth_host + settings.senhaunica_access_token_resource
    resp = _post(url, _client(token, secret, verifier))
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_user_data(token, secret):
    url = settings.senhaunica_oauth_host + "/wsusuario/oauth/usuariousp"
    resp = _post(url, _client(token, secret))
    return resp.json()


def authorize_url(token):
    query = urlencode(
        {"oauth_token": token, "callback_id": settings.senhaunica_callback_id}
    )
    return f"{settings.senhaunica_oauth_host}{settings.senhaunica_authorize_url}?{query}"


def load_whitelist(path="data/nusp_whitelist.txt"):
    try:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return None  # sem arquivo, sem restrição
    values = set()
    for chunk in content.replace("\n", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            values.add(chunk)
    return values
