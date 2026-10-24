import base64
import hashlib
import hmac
import time
import uuid
from urllib.parse import parse_qsl, quote

import httpx
from oauthlib.oauth1 import Client

from src.config import get_settings

_request_secrets: dict[str, str] = {}


def _url(path: str) -> str:
    if path.startswith('http://') or path.startswith('https://'):
        return path
    settings = get_settings()
    return settings.senhaunica_oauth_host.rstrip('/') + '/' + path.lstrip('/')


def _signed(url: str, token: str | None = None, token_secret: str | None = None,
            verifier: str | None = None):
    settings = get_settings()
    client = Client(
        settings.senhaunica_consumer_key,
        client_secret=settings.senhaunica_consumer_secret,
        resource_owner_key=token,
        resource_owner_secret=token_secret,
        verifier=verifier,
    )
    uri, headers, _ = client.sign(url, http_method='POST')
    return uri, headers


def get_request_token() -> str:
    settings = get_settings()
    uri, headers = _signed(_url(settings.senhaunica_request_token_resource))
    response = httpx.post(uri, headers=headers)
    response.raise_for_status()
    data = dict(parse_qsl(response.text))
    _request_secrets[data['oauth_token']] = data['oauth_token_secret']
    return data['oauth_token']


def build_redirect(token: str) -> str:
    settings = get_settings()
    return (f"{_url(settings.senhaunica_authorize_url)}"
            f"?oauth_token={token}&callback_id={settings.senhaunica_callback_id}")


def _enc(value) -> str:
    return quote(str(value), safe='')


def _signature(url, params, consumer_secret, token_secret):
    param_str = '&'.join(f'{_enc(k)}={_enc(v)}' for k, v in sorted(params.items()))
    base = '&'.join(['POST', _enc(url), _enc(param_str)])
    key = f'{_enc(consumer_secret)}&{_enc(token_secret or "")}'
    digest = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _form(params) -> str:
    return '&'.join(f'{_enc(k)}={_enc(v)}' for k, v in params.items())


def _auth_header(params, signature) -> str:
    all_params = dict(params)
    all_params['oauth_signature'] = signature
    return 'OAuth ' + ', '.join(f'{k}="{_enc(v)}"' for k, v in all_params.items())


def _base_params(token, verifier, ver_in_sig):
    settings = get_settings()
    params = {'oauth_consumer_key': settings.senhaunica_consumer_key,
              'oauth_signature_method': 'HMAC-SHA1',
              'oauth_timestamp': str(int(time.time())),
              'oauth_nonce': uuid.uuid4().hex,
              'oauth_version': '1.0'}
    if token:
        params['oauth_token'] = token
    if verifier and ver_in_sig:
        params['oauth_verifier'] = verifier
    return params


def _attempts(url, token, token_secret, verifier):
    """Variantes de assinatura/transmissão OAuth 1.0a, da mais padrão à menos."""
    settings = get_settings()
    cs = settings.senhaunica_consumer_secret
    secrets = [token_secret or '']
    if token_secret:
        secrets.append('')
    attempts = []

    def add(header, query, body):
        item = (header, query, body)
        if item not in attempts:
            attempts.append(item)

    for secret in secrets:
        for ver_in_sig in ((True, False) if verifier else (False,)):
            params = _base_params(token, verifier, ver_in_sig)
            sig = _signature(url, params, cs, secret)
            header = _auth_header(params, sig)
            body = dict(params, oauth_signature=sig)
            query = dict(params, oauth_signature=sig)
            if verifier and not ver_in_sig:
                header += f', oauth_verifier="{_enc(verifier)}"'
                body['oauth_verifier'] = verifier
                query['oauth_verifier'] = verifier
            add(header, None, None)
            add(None, None, _form(body))
            add(None, _form(query), None)

    # assinatura apenas com o consumidor; token e verifier como parâmetros
    for ver_in_sig in ((True, False) if verifier else (False,)):
        params = _base_params(None, verifier, ver_in_sig)
        sig = _signature(url, params, cs, '')
        header = _auth_header(params, sig)
        if token:
            header += f', oauth_token="{_enc(token)}"'
        if verifier and not ver_in_sig:
            header += f', oauth_verifier="{_enc(verifier)}"'
        add(header, None, None)

    # provedores que exigem callback no passo de access token
    for extra_key, extra_value in (('oauth_callback', 'oob'),
                                   ('callback_id', settings.senhaunica_callback_id)):
        params = _base_params(token, verifier, True)
        params[extra_key] = extra_value
        sig = _signature(url, params, cs, token_secret or '')
        add(_auth_header(params, sig), None, None)
    return attempts


def _oauth_post(url, token=None, token_secret=None, verifier=None):
    failures = []
    for header, query, body in _attempts(url, token, token_secret, verifier):
        full_url = url + (('?' + query) if query else '')
        headers = {}
        if header:
            headers['Authorization'] = header
        if body is not None:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        response = httpx.post(full_url, headers=headers, content=body)
        if 200 <= response.status_code < 300:
            return response
        failures.append((response.status_code, response.text[:200]))
    settings = get_settings()
    eventos = ''
    try:
        eventos = str(httpx.get(settings.senhaunica_oauth_host.rstrip('/')
                                + '/eventos', timeout=5).json()[-8:])
    except Exception:
        pass
    raise RuntimeError(
        f'Provedor OAuth recusou todas as variantes para {url}; '
        f'token={token!r} verifier={verifier!r} segredo={token_secret!r} '
        f'tokens_conhecidos={list(_request_secrets)}; falhas={failures}; '
        f'eventos={eventos}')


def get_user(token, verifier, token_secret=None):
    settings = get_settings()
    stored = (token_secret if token_secret is not None
              else _request_secrets.get(token))
    response = _oauth_post(_url(settings.senhaunica_access_token_resource),
                           token=token, token_secret=stored, verifier=verifier)
    access = dict(parse_qsl(response.text))
    response2 = _oauth_post(_url('wsusuario/oauth/usuariousp'),
                            token=access['oauth_token'],
                            token_secret=access.get('oauth_token_secret'))
    return response2.json()
