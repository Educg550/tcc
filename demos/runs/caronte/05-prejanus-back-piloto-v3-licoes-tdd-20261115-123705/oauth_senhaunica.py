from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client as OAuth1Client

from config import settings


def _url(resource: str) -> str:
    if resource.startswith("http://") or resource.startswith("https://"):
        return resource
    host = settings.senhaunica_oauth_host.rstrip("/")
    return host + "/" + resource.lstrip("/")


def _sign(url: str, method: str = "POST", token=None, secret=None, verifier=None):
    client = OAuth1Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=secret,
        verifier=verifier,
    )
    return client.sign(url, http_method=method)


def _parse_token_response(text: str) -> dict:
    """Aceita urlencoded (contrato) e, por tolerância, JSON."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return {k: [str(v)] for k, v in data.items()}
    except ValueError:
        pass
    return parse_qs(text)


def _post_signed(url, token=None, secret=None, verifier=None):
    uri, headers, body = _sign(url, token=token, secret=secret, verifier=verifier)
    resp = requests.post(uri, headers=headers, data=body, timeout=30)
    resp.raise_for_status()
    return _parse_token_response(resp.text)


def get_request_token():
    data = _post_signed(_url(settings.senhaunica_request_token_resource))
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_access_token(token, secret, verifier):
    data = _post_signed(
        _url(settings.senhaunica_access_token_resource),
        token=token,
        secret=secret,
        verifier=verifier,
    )
    return data["oauth_token"][0], data["oauth_token_secret"][0]


def get_user_data(token, secret):
    url = _url("wsusuario/oauth/usuariousp")
    uri, headers, body = _sign(url, token=token, secret=secret)
    resp = requests.post(uri, headers=headers, data=body, timeout=30)
    resp.raise_for_status()
    return resp.json()


def authorize_url(token: str) -> str:
    url = _url(settings.senhaunica_authorize_url)
    sep = "&" if "?" in url else "?"
    return (
        f"{url}{sep}oauth_token={token}"
        f"&callback_id={settings.senhaunica_callback_id}"
    )


def check_authorization(token: str) -> dict | None:
    """Consulta o provedor sobre a autorização de um request token, sem
    autorizar um perfil. Usado como fallback quando o callback do provedor
    não chegou ao backend."""
    url = _url(settings.senhaunica_authorize_url)
    sep = "&" if "?" in url else "?"
    try:
        resp = requests.get(
            f"{url}{sep}oauth_token={token}"
            f"&callback_id={settings.senhaunica_callback_id}",
            timeout=10,
        )
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None
