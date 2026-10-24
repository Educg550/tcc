from urllib.parse import parse_qsl

import requests
from oauthlib.oauth1 import Client as OAuth1Client

from config import settings


class OAuthError(Exception):
    pass


def _url(path: str) -> str:
    return settings.SENHAUNICA_OAUTH_HOST.rstrip("/") + "/" + path.lstrip("/")


def _post_signed(url: str, client: OAuth1Client):
    signed_url, headers, body = client.sign(url, http_method="POST")
    resp = requests.post(signed_url, headers=headers, data=body, timeout=30)
    if resp.status_code != 200:
        raise OAuthError(f"OAuth request failed: {resp.status_code} {resp.text}")
    return resp


def get_request_token():
    client = OAuth1Client(settings.SENHAUNICA_CONSUMER_KEY, client_secret=settings.SENHAUNICA_CONSUMER_SECRET)
    resp = _post_signed(_url(settings.SENHAUNICA_REQUEST_TOKEN_RESOURCE), client)
    data = dict(parse_qsl(resp.text))
    return data.get("oauth_token"), data.get("oauth_token_secret")


def get_access_token(token: str, token_secret: str, verifier: str):
    client = OAuth1Client(
        settings.SENHAUNICA_CONSUMER_KEY,
        client_secret=settings.SENHAUNICA_CONSUMER_SECRET,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )
    resp = _post_signed(_url(settings.SENHAUNICA_ACCESS_TOKEN_RESOURCE), client)
    data = dict(parse_qsl(resp.text))
    return data.get("oauth_token"), data.get("oauth_token_secret")


def get_user_info(access_token: str, access_secret: str):
    client = OAuth1Client(
        settings.SENHAUNICA_CONSUMER_KEY,
        client_secret=settings.SENHAUNICA_CONSUMER_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    resp = _post_signed(_url("wsusuario/oauth/usuariousp"), client)
    return resp.json()


def authorize_url(request_token: str) -> str:
    base = settings.SENHAUNICA_AUTHORIZE_URL
    if base.startswith("http://") or base.startswith("https://"):
        url = base
    else:
        url = _url(base)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}oauth_token={request_token}&callback_id={settings.SENHAUNICA_CALLBACK_ID}"
