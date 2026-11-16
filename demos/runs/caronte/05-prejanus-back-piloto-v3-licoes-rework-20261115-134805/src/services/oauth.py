import re
from pathlib import Path
from urllib.parse import parse_qs

import requests
from oauthlib.oauth1 import Client

from ..config import settings

REQUEST_SECRETS: dict[str, str] = {}


def _url(path: str) -> str:
    if path.startswith('http://') or path.startswith('https://'):
        return path
    return settings.senhaunica_oauth_host.rstrip('/') + '/' + path.lstrip('/')


def _post(url: str, **client_kwargs) -> requests.Response:
    client = Client(settings.senhaunica_consumer_key,
                    client_secret=settings.senhaunica_consumer_secret, **client_kwargs)
    uri, headers, body = client.sign(url, http_method='POST')
    resp = requests.post(uri, headers=headers, data=body or {}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f'OAuth falhou ({resp.status_code}): {resp.text}')
    return resp


def request_token() -> str:
    resp = _post(_url(settings.senhaunica_request_token_resource))
    data = parse_qs(resp.text)
    token = data['oauth_token'][0]
    REQUEST_SECRETS[token] = data['oauth_token_secret'][0]
    return token


def authorize_url(token: str) -> str:
    base = _url(settings.senhaunica_authorize_url)
    sep = '&' if '?' in base else '?'
    return (f'{base}{sep}oauth_token={token}'
            f'&callback_id={settings.senhaunica_callback_id}')


def access_token(token: str, verifier: str) -> tuple[str, str]:
    secret = REQUEST_SECRETS.pop(token, None)
    if secret is None:
        raise RuntimeError('oauth_token desconhecido')
    resp = _post(_url(settings.senhaunica_access_token_resource),
                 resource_owner_key=token, resource_owner_secret=secret,
                 verifier=verifier)
    data = parse_qs(resp.text)
    return data['oauth_token'][0], data['oauth_token_secret'][0]


def user_info(access_token: str, access_secret: str) -> dict:
    resp = _post(_url('/wsusuario/oauth/usuariousp'),
                 resource_owner_key=access_token, resource_owner_secret=access_secret)
    return resp.json()


def whitelist() -> set[str]:
    path = Path('data/nusp_whitelist.txt')
    if not path.exists():
        path = Path(__file__).resolve().parents[2] / 'data' / 'nusp_whitelist.txt'
    if not path.exists():
        return set()
    return {t.strip() for t in re.split(r'[,\n]+', path.read_text()) if t.strip()}
