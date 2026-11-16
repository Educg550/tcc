from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text

from ..auth import current_user, set_session
from ..db import engine
from ..services import oauth

router = APIRouter(prefix='/auth', tags=['auth'])


@router.get('/login')
def login(user=Depends(current_user)):
    return user


@router.post('/login/senhaunica')
def login_senhaunica(response: Response, oauth_token: str | None = None,
                     oauth_verifier: str | None = None):
    if not oauth_token:
        token = oauth.request_token()
        return {'redirect_to': oauth.authorize_url(token)}
    access_t, access_s = oauth.access_token(oauth_token, oauth_verifier or '')
    info = oauth.user_info(access_t, access_s)
    nusp = str(info.get('loginUsuario') or '')
    if nusp not in oauth.whitelist():
        raise HTTPException(status_code=403, detail='Usuário não autorizado')
    email = info.get('emailPrincipalUsuario')
    name = info.get('nomeUsuario') or email
    with engine.begin() as conn:
        row = conn.execute(
            text('SELECT id, name, email, nusp, role FROM "user" WHERE email = :e'),
            {'e': email}).mappings().first()
        if row:
            user = dict(row)
        else:
            uid = conn.execute(
                text('INSERT INTO "user" (email, name, role, nusp, created_at) '
                     "VALUES (:e, :n, 'teacher', :nu, now()) RETURNING id"),
                {'e': email, 'n': name, 'nu': nusp}).scalar()
            user = {'id': uid, 'name': name, 'email': email, 'nusp': nusp,
                    'role': 'teacher'}
    set_session(response, user['id'])
    return user
