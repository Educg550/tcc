import os
from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client as OAuth1Client

from config import settings


def _host():
    return settings.senhaunica_oauth_host.rstrip("/")


def _sign_post(url, client):
    uri, headers, body = client.sign(url, http_method="POST")
    resp = requests.post(uri, headers=headers, data=body, timeout=30)
    resp.raise_for_status()
    return resp


def fetch_request_token():
    client = OAuth1Client(
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
        callback_uri="oob",
    )
    resp = _sign_post(_host() + settings.senhaunica_request_token_resource, client)
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def fetch_access_token(oauth_token, token_secret, verifier):
    client = OAuth1Client(
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
        resource_owner_key=oauth_token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )
    resp = _sign_post(_host() + settings.senhaunica_access_token_resource, client)
    data = parse_qs(resp.text)
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def fetch_user_data(access_token, access_secret):
    client = OAuth1Client(
        settings.senhaunica_consumer_key,
        settings.senhaunica_consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    resp = _sign_post(_host() + "/wsusuario/oauth/usuariousp", client)
    return resp.json()


def authorize_url(oauth_token):
    return (
        f"{_host()}{settings.senhaunica_authorize_url}"
        f"?oauth_token={oauth_token}&callback_id={settings.senhaunica_callback_id}"
    )


def load_whitelist():
    path = os.path.join("data", "nusp_whitelist.txt")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return {t.strip() for t in content.replace(",", "\n").split() if t.strip()}
