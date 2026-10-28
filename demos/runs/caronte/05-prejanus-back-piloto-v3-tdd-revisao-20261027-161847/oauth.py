from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client as OAuth1Client

from config import settings


def _url(resource):
    resource = resource or ""
    if resource.startswith(("http://", "https://")):
        return resource
    host = (settings.su_host or "").rstrip("/")
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    return host + "/" + resource.lstrip("/")


def _sign(url, token=None, secret=None, verifier=None):
    client = OAuth1Client(
        settings.consumer_key,
        client_secret=settings.consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=secret,
        verifier=verifier,
    )
    return client.sign(url, http_method="POST")


def _post(url, token=None, secret=None, verifier=None):
    uri, headers, body = _sign(url, token, secret, verifier)
    with requests.Session() as session:
        session.trust_env = False
        try:
            return session.post(uri, headers=headers, data=body or {}, timeout=30, verify=False)
        except requests.exceptions.ConnectionError:
            alt = url.replace("https://", "http://", 1)
            if alt == url:
                raise
            uri, headers, body = _sign(alt, token, secret, verifier)
            return session.post(uri, headers=headers, data=body or {}, timeout=30, verify=False)


def _parse(body):
    return {k: v[0] for k, v in parse_qs(body).items()}


def get_request_token():
    resp = _post(_url(settings.su_request))
    if resp.status_code != 200:
        raise RuntimeError(f"request token failed: {resp.status_code} {resp.text}")
    data = _parse(resp.text)
    return data["oauth_token"], data["oauth_token_secret"]


def get_access_token(token, secret, verifier):
    resp = _post(_url(settings.su_access), token, secret, verifier)
    if resp.status_code != 200:
        raise RuntimeError(f"access token failed: {resp.status_code} {resp.text}")
    data = _parse(resp.text)
    return data["oauth_token"], data["oauth_token_secret"]


def get_user_info(token, secret):
    resp = _post(_url("/wsusuario/oauth/usuariousp"), token, secret)
    if resp.status_code != 200:
        raise RuntimeError(f"user info failed: {resp.status_code} {resp.text}")
    return resp.json()


def authorize_url(token):
    url = _url(settings.su_authorize)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}oauth_token={token}&callback_id={settings.callback_id}"
