import csv
import io
import json
import os
import smtplib
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl

import requests
from babel.dates import format_date
from fpdf import FPDF
from itsdangerous import Signer
from oauthlib.oauth1 import Client as ClienteOAuth
from pydantic import BaseModel
from typing import Literal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response

# ---------------------------------------------------------------- configuração

APP_ENV = os.environ.get('APP_ENV', 'production')
DEV_USER_ID = os.environ.get('DEV_USER_ID', '')
SECRET_KEY = os.environ.get('SECRET_KEY', 'caronte')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost')
ORIGENS = [o.strip() for o in os.environ.get('BACKEND_CORS_ORIGINS', '').split(',') if o.strip()]
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '1025'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'no-reply@example.com')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'false').lower() in ('1', 'true', 'yes')
OAUTH_HOST = os.environ.get('SENHAUNICA_OAUTH_HOST', '')
RECURSO_REQUEST_TOKEN = os.environ.get('SENHAUNICA_REQUEST_TOKEN_RESOURCE', '/wsusuario/oauth/request_token')
URL_AUTORIZACAO = os.environ.get('SENHAUNICA_AUTHORIZE_URL', '/wsusuario/oauth/authorize')
RECURSO_ACCESS_TOKEN = os.environ.get('SENHAUNICA_ACCESS_TOKEN_RESOURCE', '/wsusuario/oauth/access_token')
CALLBACK_ID = os.environ.get('SENHAUNICA_CALLBACK_ID', '')
CONSUMER_KEY = os.environ.get('SENHAUNICA_CONSUMER_KEY', '')
CONSUMER_SECRET = os.environ.get('SENHAUNICA_CONSUMER_SECRET', '')

BIDDINGS = ['decline', 'available', 'interested', 'agreed', 'interested_scholarship', '']
FUNCOES_ADMIN = {'admin', 'administrator', 'secretary', 'coordinator', 'coordenador', 'secretaria'}
FALSO = {'', 'false', 'no', 'não', 'nao', '0', 'none', 'null', 'n'}


def ajustar_url(u: str) -> str:
    if u.startswith('postgresql://'):
        return 'postgresql+psycopg://' + u[len('postgresql://'):]
    return u


class Banco:
    def __init__(self, url: str):
        self.engine = create_async_engine(ajustar_url(url))

    async def consulta(self, q: str, params: dict = None):
        async with self.engine.connect() as c:
            r = await c.execute(text(q), params or {})
            return [dict(m._mapping) for m in r]

    async def comando(self, q: str, params: dict = None):
        async with self.engine.begin() as c:
            r = await c.execute(text(q), params or {})
            try:
                return [dict(m._mapping) for m in r]
            except Exception:
                return []


PREJANUS = Banco(os.environ['DB_CONNECTION_STRING'])
FORMS = Banco(os.environ['DB_CONNECTION_STRING_FORMS'])

# ---------------------------------------------------------------- utilidades


def como_json(v):
    if v is None or isinstance(v, (list, dict)):
        return v
    try:
        return json.loads(v)
    except Exception:
        return v


def verdadeiro(v) -> bool:
    return v is not None and str(v).strip().lower() not in FALSO


def latin(s: str) -> str:
    return str(s).encode('latin-1', 'replace').decode('latin-1')


async def obter_edital(edict_id: int) -> dict:
    linhas = await PREJANUS.consulta('SELECT * FROM edict WHERE id=:i', {'i': edict_id})
    if not linhas:
        raise HTTPException(404, 'Edital não encontrado')
    return linhas[0]


async def resposta_candidato(response_id: int) -> dict:
    linhas = await FORMS.consulta(
        'SELECT id, form_id, token, email, form_version, submitted_at, metadata '
        'FROM form_response WHERE id=:i', {'i': response_id})
    if not linhas:
        raise HTTPException(404, 'Resposta não encontrada')
    return linhas[0]


async def valores_da_resposta(response_id: int) -> dict:
    linhas = await FORMS.consulta(
        'SELECT field_id, value FROM responses WHERE response_id=:i', {'i': response_id})
    return {l['field_id']: l['value'] for l in linhas}


async def mapeamento_versao(edict_id: int, tipo: str, versao) -> Optional[dict]:
    if versao is not None:
        linhas = await PREJANUS.consulta(
            'SELECT mapping FROM edict_form_mappings '
            'WHERE edict_id=:e AND form_type=:t AND form_version=:v LIMIT 1',
            {'e': edict_id, 't': tipo, 'v': versao})
        if linhas:
            return como_json(linhas[0]['mapping'])
    linhas = await PREJANUS.consulta(
        'SELECT mapping FROM edict_form_mappings '
        'WHERE edict_id=:e AND form_type=:t '
        'ORDER BY is_active DESC, form_version DESC LIMIT 1',
        {'e': edict_id, 't': tipo})
    return como_json(linhas[0]['mapping']) if linhas else None


def extrair(no, valores: dict):
    if no is None:
        return None
    if isinstance(no, dict):
        if 'section' in no and 'field' in no and set(no) <= {'section', 'field'}:
            return valores.get(no['field'])
        return {k: extrair(v, valores) for k, v in no.items()}
    return None


def folhas(no):
    if no is None:
        return
    if isinstance(no, dict):
        if 'section' in no and 'field' in no and set(no) <= {'section', 'field'}:
            yield no
        else:
            for v in no.values():
                yield from folhas(v)


async def validar_arvore(form_id: int, versao: int, arvore: dict):
    existe = await FORMS.consulta(
        'SELECT 1 FROM form_field f JOIN form_section s ON s.id=f.section_id '
        'WHERE s.form_id=:f AND f.version=:v LIMIT 1',
        {'f': form_id, 'v': versao})
    if not existe:
        return
    for folha in folhas(arvore):
        if folha is None:
            continue
        ok = await FORMS.consulta(
            'SELECT 1 FROM form_field f JOIN form_section s ON s.id=f.section_id '
            'WHERE f.id=:fi AND f.section_id=:si AND s.form_id=:f AND f.version=:v LIMIT 1',
            {'fi': folha['field'], 'si': folha['section'], 'f': form_id, 'v': versao})
        if not ok:
            raise HTTPException(422, 'Referência inválida de seção/campo no mapeamento')


async def submissao_e_edital(submission_id: int):
    linhas = await PREJANUS.consulta(
        'SELECT s.*, a.name AS advisor_name, a.email AS advisor_email '
        'FROM submission s LEFT JOIN "user" a ON a.id=s.advisor_id WHERE s.id=:i',
        {'i': submission_id})
    if not linhas:
        raise HTTPException(404, 'Inscrição não encontrada')
    edital = await obter_edital(linhas[0]['edict_id'])
    return linhas[0], edital


async def rotulos_do_usuario(submission_id: int, user_id: int) -> list:
    linhas = await PREJANUS.consulta(
        "SELECT id, label, color FROM labels "
        "WHERE submission_id=:s AND user_id=:u AND context_type='candidate' ORDER BY id",
        {'s': submission_id, 'u': user_id})
    return [{'id': l['id'], 'label': l['label'], 'color': l['color']} for l in linhas]


async def dados_aceite(s: dict) -> dict:
    if not s['accept_form_id']:
        return {'sent': 'not_sent', 'accept': None, 'comments': None, 'submitted_at': None}
    linhas = await FORMS.consulta(
        'SELECT submitted_at FROM form_response WHERE id=:i', {'i': s['accept_form_id']})
    if not linhas:
        return {'sent': 'not_sent', 'accept': None, 'comments': None, 'submitted_at': None}
    valores = await FORMS.consulta(
        'SELECT f.name, r.value FROM responses r JOIN form_field f ON f.id=r.field_id '
        'WHERE r.response_id=:i', {'i': s['accept_form_id']})
    d = {v['name']: v['value'] for v in valores}
    return {'sent': 'replied' if linhas[0]['submitted_at'] else 'sent',
            'accept': d.get('accept'), 'comments': d.get('comments'),
            'submitted_at': linhas[0]['submitted_at']}


async def dados_leves(s: dict, edital: dict) -> dict:
    resp = await resposta_candidato(s['candidate_form_id'])
    valores = await valores_da_resposta(resp['id'])
    mapa = await mapeamento_versao(edital['id'], 'candidate', resp['form_version'])
    d = extrair(mapa, valores) if mapa else {}
    return {'name': d.get('name') or '',
            'email': d.get('email') or resp['email'] or '',
            'stats': s['stats'], 'advisor': s.get('advisor_name')}


async def listar_recomendadores(s: dict, edital: dict) -> list:
    ids = como_json(s['recommenders_form_ids']) or []
    mapa = await mapeamento_versao(edital['id'], 'recommender', None)
    itens = []
    for rid in ids:
        linhas = await FORMS.consulta(
            'SELECT id, email, submitted_at, metadata FROM form_response WHERE id=:i', {'i': rid})
        if not linhas:
            continue
        rr = linhas[0]
        valores = await valores_da_resposta(rid)
        d = extrair(mapa, valores) if mapa else {}
        enviado = d.get('sent')
        if enviado is None:
            meta = rr['metadata'] or {}
            enviado = bool(rr['submitted_at']) or bool(meta.get('sent'))
        item = dict(d)
        item['sent'] = bool(enviado)
        itens.append(item)
    return itens


async def associar_recomendadores(edital: dict, resposta: dict) -> list:
    form_cand = int(edital['candidate_forms'])
    form_rec = int(edital['recommenders_forms'])
    candidatos = await FORMS.consulta(
        'SELECT id, email FROM form_response WHERE form_id=:f AND submitted_at IS NOT NULL',
        {'f': form_cand})
    dono: Dict[str, set] = {}
    for c in candidatos:
        valores = await FORMS.consulta(
            'SELECT value FROM responses WHERE response_id=:r', {'r': c['id']})
        chaves = {v['value'] for v in valores} | {c['email']}
        for k in chaves:
            dono.setdefault(k, set()).add(c['id'])
    ligados = []
    for rr in await FORMS.consulta(
            'SELECT id, email, metadata FROM form_response WHERE form_id=:f', {'f': form_rec}):
        meta = rr['metadata'] or {}
        referencias = {str(v) for v in meta.values()}
        if referencias & {str(resposta['id']), str(resposta['token']), str(resposta['email'])}:
            ligados.append(rr['id'])
            continue
        valores = await FORMS.consulta(
            'SELECT value FROM responses WHERE response_id=:r', {'r': rr['id']})
        chaves = {v['value'] for v in valores} | {rr['email']} | referencias
        for k in chaves:
            if k in dono and len(dono[k]) == 1 and resposta['id'] in dono[k]:
                ligados.append(rr['id'])
                break
    return sorted(ligados)


async def sincronizar(edital: dict):
    form_cand = int(edital['candidate_forms'])
    respostas = await FORMS.consulta(
        'SELECT id, token, email, form_version FROM form_response '
        'WHERE form_id=:f AND submitted_at IS NOT NULL ORDER BY id', {'f': form_cand})
    existentes = {r['candidate_form_id'] for r in await PREJANUS.consulta(
        'SELECT candidate_form_id FROM submission WHERE edict_id=:e', {'e': edital['id']})}
    mapa_rec = await PREJANUS.consulta(
        "SELECT form_version FROM edict_form_mappings "
        "WHERE edict_id=:e AND form_type='recommender' "
        "ORDER BY is_active DESC, form_version DESC LIMIT 1", {'e': edital['id']})
    rv = mapa_rec[0]['form_version'] if mapa_rec else 1
    for r in respostas:
        if r['id'] in existentes:
            continue
        recs = await associar_recomendadores(edital, r)
        await PREJANUS.comando(
            "INSERT INTO submission(edict_id, candidate_form_id, recommenders_form_ids, "
            "stats, letter_sent, recommender_form_version, candidate_form_version, "
            "created_at, updated_at) VALUES (:e,:c,:r::json,'underreview',false,:rv,:cv,now(),now())",
            {'e': edital['id'], 'c': r['id'], 'r': json.dumps(recs), 'rv': rv, 'cv': r['form_version']})
    nulos = await PREJANUS.consulta(
        'SELECT id, candidate_form_id FROM submission '
        'WHERE edict_id=:e AND recommenders_form_ids IS NULL', {'e': edital['id']})
    for s in nulos:
        r = next((x for x in respostas if x['id'] == s['candidate_form_id']), None)
        if r:
            recs = await associar_recomendadores(edital, r)
            await PREJANUS.comando(
                'UPDATE submission SET recommenders_form_ids=:r::json WHERE id=:i',
                {'r': json.dumps(recs), 'i': s['id']})


async def montar_submissao(s: dict, edital: dict, usuario: dict, slots_map: dict, favorito: bool) -> dict:
    resp = await resposta_candidato(s['candidate_form_id'])
    valores = await valores_da_resposta(resp['id'])
    mapa = await mapeamento_versao(edital['id'], 'candidate', resp['form_version'])
    d = extrair(mapa, valores) if mapa else {}
    g = d.get('graduation') or {}
    r = d.get('research') or {}
    rf = r.get('field') or {}
    p = d.get('poscomp') or {}
    poscomp = {'year': p.get('year'), 'score': p.get('score')} \
        if any(v is not None for v in p.values()) else None
    licitacoes = await PREJANUS.consulta(
        "SELECT l.user_id, l.label, u.name, u.email FROM labels l "
        "JOIN \"user\" u ON u.id=l.user_id "
        "WHERE l.submission_id=:s AND l.context_type='bidding'", {'s': s['id']})
    dados_lic = {k: [] for k in BIDDINGS}
    for l in licitacoes:
        slots = slots_map.get(l['user_id'])
        dados_lic.setdefault(l['label'], []).append(
            {'id': l['user_id'], 'name': l['name'], 'email': l['email'],
             'slots': str(slots) if slots is not None else None})
    return {
        'id': s['id'], 'token': str(resp['token']),
        'name': d.get('name') or '', 'email': d.get('email') or resp['email'] or '',
        'phone_number': d.get('phone_number') or '',
        'nationality': d.get('nationality') or '',
        'personal_website': d.get('personal_website') or '',
        'gender': d.get('gender') or '',
        'advisor': ({'id': s['advisor_id'], 'name': s['advisor_name'], 'email': s['advisor_email']}
                    if s['advisor_id'] else None),
        'birth_date': d.get('birth_date'),
        'graduation': {'country': g.get('country'), 'course': g.get('course'),
                       'institution': g.get('institution'), 'year': g.get('year')},
        'poscomp': poscomp, 'current_occupation': d.get('current_occupation'),
        'research': {'program': r.get('program'), 'semester': r.get('semester'),
                     'field': {'primary': rf.get('primary'), 'secondary': rf.get('secondary')},
                     'will_apply_scholarship': verdadeiro(r.get('will_apply_scholarship')),
                     'dedication_level': r.get('dedication_level')},
        'lattes_curriculum': d.get('lattes_curriculum') or '',
        'stats': s['stats'], 'is_favorite': favorito,
        'bidding_users': {'data': dados_lic},
        'labels': await rotulos_do_usuario(s['id'], usuario['id']),
        'disabilities': verdadeiro(d.get('disabilities')),
        'ethnicity_race': verdadeiro(d.get('ethnicity_race')),
        'accept': await dados_aceite(s),
    }


async def montar_resumo(s: dict, edital: dict, usuario: dict) -> dict:
    resp = await resposta_candidato(s['candidate_form_id'])
    valores = await valores_da_resposta(resp['id'])
    mapa = await mapeamento_versao(edital['id'], 'candidate', resp['form_version'])
    d = extrair(mapa, valores) if mapa else {}
    g = d.get('graduation') or {}
    r = d.get('research') or {}
    rf = r.get('field') or {}
    p = d.get('poscomp') or {}
    poscomp = {'year': p.get('year'), 'score': p.get('score')} \
        if any(v is not None for v in p.values()) else None
    nota = await PREJANUS.consulta(
        'SELECT note FROM private_note WHERE user_id=:u AND submission_id=:s',
        {'u': usuario['id'], 's': s['id']})
    return {
        'id': s['id'], 'token': str(resp['token']),
        'name': d.get('name') or '', 'email': d.get('email') or resp['email'] or '',
        'stats': s['stats'], 'letter_sent': s['letter_sent'],
        'private_note': nota[0]['note'] if nota else '',
        'entry_semester': s['entry_semester'] or '',
        'graduation': {'country': g.get('country'), 'course': g.get('course'),
                       'institution': g.get('institution'), 'year': g.get('year')},
        'research': {'program': r.get('program'), 'semester': r.get('semester'),
                     'field': {'primary': rf.get('primary'), 'secondary': rf.get('secondary')},
                     'will_apply_scholarship': verdadeiro(r.get('will_apply_scholarship')),
                     'dedication_level': r.get('dedication_level')},
        'poscomp': poscomp,
        'labels': await rotulos_do_usuario(s['id'], usuario['id']),
        'recommenders': await listar_recomendadores(s, edital),
        'accept': await dados_aceite(s),
        'advisor': ({'id': s['advisor_id'], 'name': s['advisor_name'], 'email': s['advisor_email']}
                    if s['advisor_id'] else None),
    }


async def formulario_da_submissao(s: dict) -> list:
    resp = await resposta_candidato(s['candidate_form_id'])
    valores = await valores_da_resposta(resp['id'])
    secoes = await FORMS.consulta(
        'SELECT * FROM form_section WHERE form_id=:f AND is_active ORDER BY position, id',
        {'f': resp['form_id']})
    resultado = []
    for sec in secoes:
        campos = await FORMS.consulta(
            'SELECT * FROM form_field WHERE section_id=:s ORDER BY position, id',
            {'s': sec['id']})
        lista = []
        for c in campos:
            item = dict(c)
            item['label'] = como_json(c['label'])
            item['description'] = como_json(c['description'])
            item['error_message'] = como_json(c['error_message'])
            item['value'] = valores.get(c['id'])
            lista.append(item)
        saida = dict(sec)
        saida['title'] = como_json(sec['title'])
        saida['description'] = como_json(sec['description'])
        saida['fields'] = lista
        resultado.append(saida)
    return resultado

# ---------------------------------------------------------------- e-mail


def enviar_email(para: str, cc: list = None, bcc: list = None, assunto: str = '', texto: str = ''):
    msg = EmailMessage()
    msg['From'] = FROM_EMAIL
    msg['To'] = para
    if cc:
        msg['Cc'] = ', '.join(cc)
    msg['Subject'] = assunto or '(sem assunto)'
    msg.set_content(texto)
    destinos = [para] + (cc or []) + (bcc or [])
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as s:
        if SMTP_USE_TLS:
            s.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.sendmail(FROM_EMAIL, destinos, msg.as_string())

# ---------------------------------------------------------------- autenticação

assinante = Signer(SECRET_KEY, salt='caronte-sessao')
TOKENS: Dict[str, str] = {}


def usuario_json(u: dict) -> dict:
    return {'id': u['id'], 'name': u['name'], 'email': u['email'],
            'nusp': u['nusp'], 'role': u['role']}


def definir_cookie(resposta: JSONResponse, user_id: int):
    resposta.set_cookie('sessao', assinante.sign(str(user_id)).decode(),
                        max_age=28800, secure=True, httponly=True, samesite='lax')


async def usuario_da_sessao(request: Request) -> Optional[dict]:
    valor = request.cookies.get('sessao')
    if not valor:
        return None
    try:
        uid = assinante.unsign(valor).decode()
    except Exception:
        return None
    linhas = await PREJANUS.consulta(
        'SELECT id, name, email, nusp, role FROM "user" WHERE id=:i', {'i': int(uid)})
    return linhas[0] if linhas else None


async def exigir_usuario(request: Request) -> dict:
    u = await usuario_da_sessao(request)
    if not u:
        raise HTTPException(401, 'Não autenticado')
    return u


def eh_admin(usuario: dict) -> bool:
    return usuario['role'] in FUNCOES_ADMIN


def nusp_permitido(nusp: str) -> bool:
    caminho = Path('data/nusp_whitelist.txt')
    if not caminho.exists():
        return True
    texto = caminho.read_text()
    permitidos = {p.strip() for linha in texto.splitlines()
                  for p in linha.split(',') if p.strip()}
    return nusp in permitidos


def post_assinado(url: str, token: str = None, segredo: str = '', verifier: str = None):
    cliente = ClienteOAuth(CONSUMER_KEY, CONSUMER_SECRET,
                           resource_token_key=token, resource_token_secret=segredo,
                           verifier=verifier)
    uri, cabecalhos, _ = cliente.sign(url, http_method='POST')
    r = requests.post(uri, headers=cabecalhos, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f'Provedor OAuth respondeu {r.status_code}: {r.text[:300]}')
    return r

# ---------------------------------------------------------------- modelos


class CorpoEdital(BaseModel):
    title: str
    description: Optional[str] = None
    year: Any
    semester: Any
    edict_type: str
    is_open: bool = True
    candidate_forms: Any
    recommenders_forms: Any
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class CorpoEdicao(BaseModel):
    title: str
    description: Optional[str] = None
    year: Any
    semester: Any
    edict_type: str
    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class CorpoData(BaseModel):
    closed_date: datetime


class CorpoFase(BaseModel):
    id: int


class CorpoEncerrar(BaseModel):
    confirmation_deadline: Any
    send_approval_letter: bool


class CorpoVagas(BaseModel):
    amount: str


class CorpoComentario(BaseModel):
    comment: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CorpoRotulo(BaseModel):
    label: str
    color: str


class CorpoNota(BaseModel):
    note: str


class CorpoReenvio(BaseModel):
    text: str


class CorpoSelecao(BaseModel):
    user_ids: Optional[List[int]] = None
    stats: Literal['approved', 'refused', 'underreview', 'waitlist']


class CorpoLicitacao(BaseModel):
    bidding: Literal['decline', 'available', 'interested', 'agreed',
                    'interested_scholarship', '']
    user_id: Optional[int] = None


class CorpoSemestre(BaseModel):
    semester: str


class Secoes(BaseModel):
    list_of_advisors: Optional[bool] = False
    relation: Optional[bool] = False
    approved: Optional[bool] = False
    refused: Optional[bool] = False
    underreview: Optional[bool] = False
    general_statistics: Optional[bool] = False
    show_emails: Optional[bool] = False

# ---------------------------------------------------------------- aplicação

app = FastAPI(title='PreJanus', version=os.environ.get('APP_VERSION', '0.1.0'))
if ORIGENS:
    app.add_middleware(CORSMiddleware, allow_origins=ORIGENS, allow_credentials=True,
                       allow_methods=['*'], allow_headers=['*'])


@app.get('/')
def raiz():
    return {'message': 'PreJanus API'}


@app.get('/auth/login')
async def login(request: Request):
    usuario = await usuario_da_sessao(request)
    if usuario:
        return usuario_json(usuario)
    if APP_ENV == 'local' and DEV_USER_ID:
        linhas = await PREJANUS.consulta(
            'SELECT id, name, email, nusp, role FROM "user" WHERE id=:i',
            {'i': int(DEV_USER_ID)})
        if linhas:
            resposta = JSONResponse(usuario_json(linhas[0]))
            definir_cookie(resposta, linhas[0]['id'])
            return resposta
    raise HTTPException(401, 'Não autenticado')


@app.post('/auth/login/senhaunica')
async def login_senhaunica(oauth_token: str = None, oauth_verifier: str = None):
    if not oauth_token:
        r = post_assinado(OAUTH_HOST + RECURSO_REQUEST_TOKEN)
        dados = dict(parse_qsl(r.text))
        TOKENS[dados['oauth_token']] = dados['oauth_token_secret']
        autorizar = URL_AUTORIZACAO if URL_AUTORIZACAO.startswith('http') \
            else OAUTH_HOST + URL_AUTORIZACAO
        return {'redirect_to': f"{autorizar}?oauth_token={dados['oauth_token']}"
                                f"&callback_id={CALLBACK_ID}"}
    segredo = TOKENS.pop(oauth_token, '')
    r = post_assinado(OAUTH_HOST + RECURSO_ACCESS_TOKEN, oauth_token, segredo, oauth_verifier)
    acesso = dict(parse_qsl(r.text))
    r2 = post_assinado(OAUTH_HOST + '/wsusuario/oauth/usuariousp',
                       acesso['oauth_token'], acesso['oauth_token_secret'])
    info = r2.json()
    nusp = str(info.get('loginUsuario', ''))
    if not nusp_permitido(nusp):
        raise HTTPException(403, 'NUSP não autorizado')
    email = info.get('emailPrincipalUsuario')
    nome = info.get('nomeUsuario', '')
    linhas = await PREJANUS.consulta(
        'SELECT id, name, email, nusp, role FROM "user" WHERE email=:e', {'e': email})
    if linhas:
        usuario = linhas[0]
    else:
        usuario = (await PREJANUS.comando(
            'INSERT INTO "user"(email, name, role, nusp, created_at) '
            "VALUES (:e,:n,'teacher',:u,now()) "
            'RETURNING id, name, email, nusp, role',
            {'e': email, 'n': nome, 'u': nusp}))[0]
    resposta = JSONResponse(usuario_json(usuario))
    definir_cookie(resposta, usuario['id'])
    return resposta

# ---------------------------------------------------------------- editais


@app.get('/edicts')
async def listar_editais(type: str = None, is_open: bool = None,
                         usuario=Depends(exigir_usuario)):
    q = 'SELECT id, title, year, semester, type AS edict_type, is_open FROM edict WHERE 1=1'
    params: dict = {}
    if type is not None:
        q += ' AND type=:t'
        params['t'] = type
    if is_open is not None:
        q += ' AND is_open=:o'
        params['o'] = is_open
    q += ' ORDER BY closed_date DESC, id DESC'
    return await PREJANUS.consulta(q, params)


@app.post('/edicts')
async def criar_edital(corpo: CorpoEdital, usuario=Depends(exigir_usuario)):
    datas = [corpo.date_application, corpo.date_verification,
             corpo.date_evaluation, corpo.date_closed]
    if not all(a < b for a, b in zip(datas, datas[1:])):
        raise HTTPException(400, 'Datas fora de ordem')
    linhas = await PREJANUS.comando(
        'INSERT INTO edict(title, description, candidate_forms, recommenders_forms, '
        'closed_date, year, semester, type, phase, is_open, created_at, updated_at, user_id) '
        "VALUES (:t,:d,:cf,:rf,:cd,:y,:s,:ty,'inscricoes',:o,now(),now(),:u) RETURNING id",
        {'t': corpo.title, 'd': corpo.description, 'cf': str(corpo.candidate_forms),
         'rf': str(corpo.recommenders_forms), 'cd': corpo.date_closed.date(),
         'y': int(corpo.year), 's': int(corpo.semester), 'ty': corpo.edict_type,
         'o': corpo.is_open, 'u': usuario['id']})
    edict_id = linhas[0]['id']
    for fase, data in (('inscricoes', corpo.date_application.date()),
                       ('homologacao', corpo.date_evaluation.date()),
                       ('avaliacao', corpo.date_verification.date()),
                       ('encerrado', corpo.date_closed.date())):
        await PREJANUS.comando(
            'INSERT INTO edict_phase(edict_id, closed_date, phase) VALUES (:e,:d,:p)',
            {'e': edict_id, 'd': data, 'p': fase})
    return {'id': edict_id, 'title': corpo.title, 'description': corpo.description,
            'year': int(corpo.year), 'semester': int(corpo.semester),
            'edict_type': corpo.edict_type, 'is_open': corpo.is_open,
            'candidate_forms': int(corpo.candidate_forms),
            'recommenders_forms': int(corpo.recommenders_forms),
            'date_application': corpo.date_application,
            'date_verification': corpo.date_verification,
            'date_evaluation': corpo.date_evaluation,
            'date_closed': corpo.date_closed,
            'closed_date': corpo.date_closed}


@app.get('/edicts/download_pdf/{job_id}')
def baixar_pdf(job_id: str):
    caminho = Path('/tmp') / f'{job_id}.pdf'
    if not caminho.exists():
        raise HTTPException(404, 'Relatório não encontrado')
    dados = caminho.read_bytes()
    caminho.unlink()
    return Response(dados, media_type='application/pdf',
                    headers={'Content-Disposition': f'inline; filename="{job_id}.pdf"'})


@app.get('/edicts/download_csv/{job_id}')
def baixar_csv(job_id: str):
    caminho = Path('/tmp') / f'{job_id}.csv'
    if not caminho.exists():
        raise HTTPException(404, 'Relatório não encontrado')
    dados = caminho.read_bytes()
    caminho.unlink()
    return Response(dados, media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'inline; filename="{job_id}.csv"'})


@app.get('/edicts/{edict_id}')
async def obter_edital_rota(edict_id: int, usuario=Depends(exigir_usuario)):
    edital = await obter_edital(edict_id)
    fases = await PREJANUS.consulta(
        'SELECT id, closed_date, phase FROM edict_phase WHERE edict_id=:e ORDER BY id',
        {'e': edict_id})
    vagas = await PREJANUS.consulta(
        'SELECT slots FROM user_edict_slots WHERE edict_id=:e AND user_id=:u',
        {'e': edict_id, 'u': usuario['id']})
    return {'id': edital['id'], 'title': edital['title'],
            'candidate_form_id': edital['candidate_forms'],
            'recommender_form_id': edital['recommenders_forms'],
            'description': edital['description'] or '',
            'closed_date': str(edital['closed_date']) if edital['closed_date'] else None,
            'created_at': edital['created_at'], 'year': edital['year'],
            'semester': edital['semester'], 'type': edital['type'],
            'is_open': edital['is_open'], 'updated_at': edital['updated_at'],
            'phase': edital['phase'],
            'phases': [{'id': f['id'],
                        'closed_date': str(f['closed_date']) if f['closed_date'] else None,
                        'phase': f['phase']} for f in fases],
            'slots': str(vagas[0]['slots']) if vagas and vagas[0]['slots'] is not None else '0'}


@app.post('/edicts/{edict_id}/edit')
async def editar_edital(edict_id: int, corpo: CorpoEdicao,
                        usuario=Depends(exigir_usuario)):
    await obter_edital(edict_id)
    datas = [corpo.date_application, corpo.date_verification,
             corpo.date_evaluation, corpo.date_closed]
    if not all(a < b for a, b in zip(datas, datas[1:])):
        raise HTTPException(400, 'Datas fora de ordem')
    await PREJANUS.comando(
        'UPDATE edict SET title=:t, description=:d, year=:y, semester=:s, type=:ty, '
        'closed_date=:cd, updated_at=now() WHERE id=:i',
        {'t': corpo.title, 'd': corpo.description, 'y': int(corpo.year),
         's': int(corpo.semester), 'ty': corpo.edict_type,
         'cd': corpo.date_closed.date(), 'i': edict_id})
    for fase, data in (('inscricoes', corpo.date_application.date()),
                       ('homologacao', corpo.date_evaluation.date()),
                       ('avaliacao', corpo.date_verification.date()),
                       ('encerrado', corpo.date_closed.date())):
        await PREJANUS.comando(
            'UPDATE edict_phase SET closed_date=:d WHERE edict_id=:e AND phase=:p',
            {'d': data, 'e': edict_id, 'p': fase})
    return {'title': corpo.title, 'description': corpo.description,
            'year': str(corpo.year), 'semester': str(corpo.semester),
            'edict_type': corpo.edict_type,
            'date_application': corpo.date_application,
            'date_verification': corpo.date_verification,
            'date_evaluation': corpo.date_evaluation,
            'date_closed': corpo.date_closed}


@app.post('/edicts/{edict_id}/edit-date')
async def editar_data(edict_id: int, corpo: CorpoData,
                      usuario=Depends(exigir_usuario)):
    await obter_edital(edict_id)
    await PREJANUS.comando(
        'UPDATE edict SET closed_date=:d, updated_at=now() WHERE id=:i',
        {'d': corpo.closed_date.date(), 'i': edict_id})
    await PREJANUS.comando(
        "UPDATE edict_phase SET closed_date=:d WHERE edict_id=:e AND phase='encerrado'",
        {'d': corpo.closed_date.date(), 'e': edict_id})
    return {'closed_date': str(corpo.closed_date.date())}


@app.post('/edicts/{edict_id}/advance-phase')
async def avancar_fase(edict_id: int, corpo: CorpoFase,
                       usuario=Depends(exigir_usuario)):
    await obter_edital(edict_id)
    linhas = await PREJANUS.consulta(
        'SELECT phase FROM edict_phase WHERE id=:i AND edict_id=:e',
        {'i': corpo.id, 'e': edict_id})
    if not linhas:
        raise HTTPException(404, 'Fase não encontrada')
    fase = linhas[0]['phase']
    await PREJANUS.comando(
        'UPDATE edict SET phase=:p, updated_at=now() WHERE id=:i',
        {'p': fase, 'i': edict_id})
    edital = await obter_edital(edict_id)
    fase_forms = {'inscricoes': 'Registration', 'homologacao': 'Approval'}.get(fase, 'Completed')
    await FORMS.comando(
        'SELECT id, phase FROM change_form_phase(:f, CAST(:p AS form_phase))',
        {'f': int(edital['candidate_forms']), 'p': fase_forms})
    return {'id': corpo.id, 'label': fase}


@app.delete('/edicts/{edict_id}/remove')
async def remover_edital(edict_id: int, usuario=Depends(exigir_usuario)):
    await obter_edital(edict_id)
    await PREJANUS.comando('DELETE FROM edict WHERE id=:i', {'i': edict_id})
    return {'message': 'Edital removido com sucesso'}


@app.patch('/edicts/{edict_id}/close')
async def encerrar_edital(edict_id: int, corpo: CorpoEncerrar,
                          usuario=Depends(exigir_usuario)):
    edital = await obter_edital(edict_id)
    if not edital['is_open']:
        raise HTTPException(409, 'Edital já encerrado')
    await PREJANUS.comando(
        'UPDATE edict SET is_open=false, updated_at=now() WHERE id=:i', {'i': edict_id})
    return {'message': 'Edital encerrado'}


@app.post('/edicts/{edict_id}/slots')
async def definir_vagas(edict_id: int, corpo: CorpoVagas,
                        usuario=Depends(exigir_usuario)):
    await obter_edital(edict_id)
    try:
        quantidade = int(corpo.amount)
    except (TypeError, ValueError):
        quantidade = 0
    quantidade = max(quantidade, 0)
    await PREJANUS.comando(
        'INSERT INTO user_edict_slots(user_id, edict_id, slots) VALUES (:u,:e,:s) '
        'ON CONFLICT (user_id, edict_id) DO UPDATE SET slots=:s',
        {'u': usuario['id'], 'e': edict_id, 's': quantidade})
    return {'amount': str(quantidade)}


@app.get('/edicts/{edict_id}/submissions')
async def listar_submissoes(edict_id: int, stats: str = None,
                            only_favorites: bool = False,
                            usuario=Depends(exigir_usuario)):
    edital = await obter_edital(edict_id)
    await sincronizar(edital)
    q = ('SELECT s.*, a.name AS advisor_name, a.email AS advisor_email '
         'FROM submission s LEFT JOIN "user" a ON a.id=s.advisor_id '
         'WHERE s.edict_id=:e')
    params: dict = {'e': edict_id}
    if stats is not None:
        q += ' AND s.stats=:st'
        params['st'] = stats
    if only_favorites:
        q += (' AND EXISTS (SELECT 1 FROM favorites f '
              'WHERE f.submission_id=s.id AND f.user_id=:u)')
        params['u'] = usuario['id']
    q += ' ORDER BY s.id'
    subs = await PREJANUS.consulta(q, params)
    slots_map = {r['user_id']: r['slots'] for r in await PREJANUS.consulta(
        'SELECT user_id, slots FROM user_edict_slots WHERE edict_id=:e', {'e': edict_id})}
    favoritos = {r['submission_id'] for r in await PREJANUS.consulta(
        'SELECT submission_id FROM favorites WHERE user_id=:u', {'u': usuario['id']})}
    resultado = []
    for s in subs:
        resultado.append(await montar_submissao(
            s, edital, usuario, slots_map, s['id'] in favoritos))
    return {'submissions': resultado}

# ---------------------------------------------------------------- mapeamentos


def mapeamento_json(m: dict) -> dict:
    return {'id': m['id'], 'edict_id': m['edict_id'], 'form_type': m['form_type'],
            'mapping': como_json(m['mapping']), 'is_active': m['is_active'],
            'form_id': m['form_id'], 'user_id': m['user_id'],
            'version': m['form_version'], 'form_version': m['form_version'],
            'created_at': m['created_at']}


async def criar_mapeamento(edict_id: int, tipo: str, versao: int, arvore: dict, usuario: dict):
    edital = await obter_edital(edict_id)
    form_id = int(edital['candidate_forms'] if tipo == 'candidate'
                  else edital['recommenders_forms'])
    await validar_arvore(form_id, versao, arvore)
    linhas = await PREJANUS.comando(
        'INSERT INTO edict_form_mappings(edict_id, form_type, mapping, is_active, '
        'created_at, form_id, user_id, form_version) '
        'VALUES (:e,:t,:m,true,now(),:f,:u,:v) RETURNING *',
        {'e': edict_id, 't': tipo, 'm': json.dumps(arvore), 'f': str(form_id),
         'u': usuario['id'], 'v': versao})
    return mapeamento_json(linhas[0])


@app.post('/edicts/{edict_id}/recommenders/mappings/versions/{version}/')
async def criar_mapeamento_recomendador(edict_id: int, version: int,
                                        arvore: Dict[str, Any],
                                        usuario=Depends(exigir_usuario)):
    return await criar_mapeamento(edict_id, 'recommender', version, arvore, usuario)


@app.post('/edicts/{edict_id}/candidates/mappings/versions/{version}/')
async def criar_mapeamento_candidato(edict_id: int, version: int,
                                     arvore: Dict[str, Any],
                                     usuario=Depends(exigir_usuario)):
    return await criar_mapeamento(edict_id, 'candidate', version, arvore, usuario)


@app.get('/edicts/{edict_id}/candidates/mappings')
async def listar_mapeamentos_candidato(edict_id: int,
                                        usuario=Depends(exigir_usuario)):
    linhas = await PREJANUS.consulta(
        "SELECT * FROM edict_form_mappings WHERE edict_id=:e AND form_type='candidate' "
        'ORDER BY id', {'e': edict_id})
    return [mapeamento_json(m) for m in linhas]


@app.get('/edicts/{edict_id}/recommenders/mappings')
async def listar_mapeamentos_recomendador(edict_id: int,
                                           usuario=Depends(exigir_usuario)):
    linhas = await PREJANUS.consulta(
        "SELECT * FROM edict_form_mappings WHERE edict_id=:e AND form_type='recommender' "
        'ORDER BY id', {'e': edict_id})
    return [mapeamento_json(m) for m in linhas]


async function_placeholder = None


async def atualizar_mapeamento(edict_id: int, tipo: str, version: int,
                               mapping_id: int, arvore: dict, usuario: dict):
    edital = await obter_edital(edict_id)
    linhas = await PREJANUS.consulta(
        'SELECT * FROM edict_form_mappings '
        'WHERE id=:i AND edict_id=:e AND form_type=:t AND form_version=:v',
        {'i': mapping_id, 'e': edict_id, 't': tipo, 'v': version})
    if not linhas:
        raise HTTPException(404, 'Mapeamento não encontrado')
    form_id = int(edital['candidate_forms'] if tipo == 'candidate'
                  else edital['recommenders_forms'])
    await validar_arvore(form_id, version, arvore)
    atual = await PREJANUS.comando(
        'UPDATE edict_form_mappings SET mapping=:m WHERE id=:i RETURNING *',
        {'m': json.dumps(arvore), 'i': mapping_id})
    return mapeamento_json(atual[0])


async def excluir_mapeamento(edict_id: int, tipo: str, version: int, mapping_id: int):
    await obter_edital(edict_id)
    linhas = await PREJANUS.consulta(
        'SELECT id FROM edict_form_mappings '
        'WHERE id=:i AND edict_id=:e AND form_type=:t AND form_version=:v',
        {'i': mapping_id, 'e': edict_id, 't': tipo, 'v': version})
    if not linhas:
        raise HTTPException(404, 'Mapeamento não encontrado')
    await PREJANUS.comando(
        'DELETE FROM edict_form_mappings WHERE id=:i', {'i': mapping_id})
    return {'message': 'Mapping deleted successfully'}


@app.put('/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}')
async def atualizar_mapeamento_recomendador(edict_id: int, mapping_id: int, version: int,
                                             payload: Dict[str, Any],
                                             usuario=Depends(exigir_usuario)):
    return await atualizar_mapeamento(edict_id, 'recommender', version, mapping_id,
                                      payload, usuario)


@app.delete('/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}')
async def excluir_mapeamento_recomendador(edict_id: int, mapping_id: int, version: int,
                                          usuario=Depends(exigir_usuario)):
    return await excluir_mapeamento(edict_id, 'recommender', version, mapping_id)


@app.put('/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}')
async def atualizar_mapeamento_candidato(edict_id: int, mapping_id: int, version: int,
                                          payload: Dict[str, Any],
                                          usuario=Depends(exigir_usuario)):
    return await atualizar_mapeamento(edict_id, 'candidate', version, mapping_id,
                                      payload, usuario)


@app.delete('/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}')
async def excluir_mapeamento_candidato(edict_id: int, mapping_id: int, version: int,
                                        usuario=Depends(exigir_usuario)):
    return await excluir_mapeamento(edict_id, 'candidate', version, mapping_id)


async function_placeholder2 = None


@app.get('/edicts/{edict_id}/candidates/forms/versions/unmapped')
async def versoes_sem_mapeamento_candidato(edict_id: int,
                                           usuario=Depends(exigir_usuario)):
    return await versoes_sem_mapeamento(edict_id, 'candidate')


@app.get('/edicts/{edict_id}/recommenders/forms/versions/unmapped')
async def versoes_sem_mapeamento_recomendador(edict_id: int,
                                               usuario=Depends(exigir_usuario)):
    return await versoes_sem_mapeamento(edict_id, 'recommender')


async def versoes_sem_mapeamento(edict_id: int, tipo: str) -> list:
    edital = await obter_edital(edict_id)
    form_id = int(edital['candidate_forms'] if tipo == 'candidate'
                  else edital['recommenders_forms'])
    versoes = {r['version'] for r in await FORMS.consulta(
        'SELECT DISTINCT version FROM form_section WHERE form_id=:f', {'f': form_id})}
    mapeadas = {r['form_version'] for r in await PREJANUS.consulta(
        'SELECT DISTINCT form_version FROM edict_form_mappings '
        'WHERE edict_id=:e AND form_type=:t', {'e': edict_id, 't': tipo})}
    return sorted(versoes - mapeadas)

# ---------------------------------------------------------------- relatórios


@app.post('/edicts/{edict_id}/interactors_list')
async def lista_interacoes(edict_id: int, mode: str = 'plain_text',
                            opcoes: Secoes = None,
                            usuario=Depends(exigir_usuario),
                            background: BackgroundTasks = None):
    await obter_edital(edict_id)
    if mode == 'pdf':
        job = uuid.uuid4().hex
        background.add_task(tarefa_pdf, job, edict_id, opcoes or Secoes())
        return {'status': 'processing', 'job_id': job}
    linhas = await PREJANUS.consulta(
        'SELECT DISTINCT u.id, u.name, u.email FROM "user" u WHERE u.id IN ('
        'SELECT c.user_id FROM comment c JOIN submission s ON s.id=c.submission_id '
        'WHERE s.edict_id=:e '
        'UNION SELECT f.user_id FROM favorites f JOIN submission s ON s.id=f.submission_id '
        'WHERE s.edict_id=:e '
        'UNION SELECT l.user_id FROM labels l JOIN submission s ON s.id=l.submission_id '
        'WHERE s.edict_id=:e '
        'UNION SELECT p.user_id FROM private_note p '
        'JOIN submission s ON s.id=p.submission_id WHERE s.edict_id=:e) ORDER BY u.id',
        {'e': edict_id})
    return linhas


@app.post('/edicts/{edict_id}/pairing-biddings')
async def pareamento_licitacoes(edict_id: int, usuario=Depends(exigir_usuario),
                                background: BackgroundTasks = None):
    await obter_edital(edict_id)
    job = uuid.uuid4().hex
    background.add_task(tarefa_csv, job, edict_id)
    return {'status': 'processing', 'job_id': job}


async def tarefa_pdf(job: str, edict_id: int, opcoes: Secoes):
    dados = await montar_pdf(edict_id, opcoes)
    (Path('/tmp') / f'{job}.pdf').write_bytes(dados)


async def tarefa_csv(job: str, edict_id: int):
    texto = await montar_csv(edict_id)
    (Path('/tmp') / f'{job}.csv').write_text(texto, encoding='utf-8')


async def montar_pdf(edict_id: int, opcoes: Secoes) -> bytes:
    edital = await obter_edital(edict_id)
    subs = await PREJANUS.consulta(
        'SELECT s.*, a.name AS advisor_name, a.email AS advisor_email '
        'FROM submission s LEFT JOIN "user" a ON a.id=s.advisor_id '
        'WHERE s.edict_id=:e ORDER BY s.id', {'e': edict_id})
    leves = [await dados_leves(s, edital) for s in subs]

    def rotulo(l):
        if opcoes.show_emails and l['email']:
            return f"{l['name']} ({l['email']})"
        return l['name']

    secoes = []
    if opcoes.list_of_advisors:
        orientadores = sorted({l['advisor'] for l in leves if l['advisor']})
        secoes.append(('Lista de Orientadores', orientadores or ['Nenhum orientador definido']))
    if opcoes.relation:
        secoes.append(('Relação de candidatos', [rotulo(l) for l in leves]))
    if opcoes.approved:
        secoes.append(('Aprovados', [rotulo(l) for l in leves if l['stats'] == 'approved']))
    if opcoes.refused:
        secoes.append(('Recusados', [rotulo(l) for l in leves if l['stats'] == 'refused']))
    if opcoes.underreview:
        secoes.append(('Em avaliação', [rotulo(l) for l in leves if l['stats'] == 'underreview']))
    if opcoes.general_statistics:
        rascunhos = await FORMS.consulta(
            'SELECT count(*) AS n FROM form_response '
            'WHERE form_id=:f AND submitted_at IS NULL',
            {'f': int(edital['candidate_forms'])})
        secoes.append(('Estatísticas Gerais', [
            f"{len(leves)} submissões finalizadas",
            f"{rascunhos[0]['n']} submissões em preenchimento"]))
    secoes.append(('Observações Finais',
                   ['Relatório gerado automaticamente pelo sistema PreJanus.']))

    p = FPDF()
    p.add_page()
    p.set_font('Helvetica', 'B', 16)
    p.multi_cell(0, 8, latin(edital['title']))
    p.ln(4)
    for titulo, itens in secoes:
        p.set_font('Helvetica', 'B', 13)
        p.multi_cell(0, 7, latin(titulo))
        p.set_font('Helvetica', '', 12)
        for it in itens:
            p.multi_cell(0, 6, '  ' + latin(it))
        p.ln(2)
    return bytes(p.output())


async def montar_csv(edict_id: int) -> str:
    edital = await obter_edital(edict_id)
    professores = await PREJANUS.consulta(
        'SELECT u.id, u.email, s.slots FROM user_edict_slots s '
        'JOIN "user" u ON u.id=s.user_id WHERE s.edict_id=:e ORDER BY u.email',
        {'e': edict_id})
    subs = await PREJANUS.consulta(
        'SELECT s.*, a.name AS advisor_name, a.email AS advisor_email '
        'FROM submission s LEFT JOIN "user" a ON a.id=s.advisor_id '
        'WHERE s.edict_id=:e ORDER BY s.id', {'e': edict_id})
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(['#'] + [pr['email'] for pr in professores])
    escritor.writerow(['slots'] + [str(pr['slots']) for pr in professores])
    for s in subs:
        licitacoes = {r['user_id']: r['label'] for r in await PREJANUS.consulta(
            "SELECT user_id, label FROM labels "
            "WHERE submission_id=:s AND context_type='bidding'", {'s': s['id']})}
        leve = await dados_leves(s, edital)
        escritor.writerow([leve['email']] +
                          [licitacoes.get(pr['id'], '') for pr in professores])
    return buffer.getvalue()

# ---------------------------------------------------------------- inscrições


@app.get('/submissions/{submission_id}')
async def detalhe_submissao(submission_id: int, include_comments: bool = False,
                            usuario=Depends(exigir_usuario)):
    s, edital = await submissao_e_edital(submission_id)
    resumo = await montar_resumo(s, edital, usuario)
    formulario = await formulario_da_submissao(s)
    return {'summary': resumo, 'submission_form': formulario}


@app.get('/submissions/{submission_id}/files/{label}/{filename}')
async def arquivo_da_submissao(submission_id: int, label: str, filename: str,
                               usuario=Depends(exigir_usuario)):
    s, _ = await submissao_e_edital(submission_id)
    if '/' in filename or '..' in filename or '\\' in filename:
        raise HTTPException(404, 'Arquivo não encontrado')
    linhas = await FORMS.consulta(
        'SELECT 1 FROM responses r JOIN form_field f ON f.id=r.field_id '
        'WHERE r.response_id=:rid AND f.name=:n AND r.value=:v LIMIT 1',
        {'rid': s['candidate_form_id'], 'n': label, 'v': filename})
    if not linhas:
        raise HTTPException(404, 'Arquivo não encontrado')
    caminho = Path('/shared/uploads') / filename
    if not caminho.exists():
        raise HTTPException(404, 'Arquivo não encontrado')
    return FileResponse(caminho, filename=filename)


@app.get('/submissions/{submission_id}/comments')
async def listar_comentarios(submission_id: int, usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    linhas = await PREJANUS.consulta(
        'SELECT c.*, u.name AS user_name FROM comment c '
        'JOIN "user" u ON u.id=c.user_id WHERE c.submission_id=:s ORDER BY c.id',
        {'s': submission_id})
    return [{'id': c['id'], 'user': {'id': c['user_id'], 'name': c['user_name']},
             'submission_id': c['submission_id'], 'comment': c['comment'],
             'created_at': c['created_at'], 'updated_at': c['updated_at']} for c in linhas]


@app.post('/submissions/{submission_id}/comments')
async def criar_comentario(submission_id: int, corpo: CorpoComentario,
                           usuario=Depends(exigir_usuario)):
    _, edital = await submissao_e_edital(submission_id)
    if edital['phase'] != 'avaliacao':
        raise HTTPException(400, 'Fora da fase de avaliação')
    criado = corpo.created_at or datetime.now(timezone.utc)
    if criado.tzinfo is None:
        criado = criado.replace(tzinfo=timezone.utc)
    linhas = await PREJANUS.comando(
        'INSERT INTO comment(user_id, submission_id, comment, created_at, updated_at) '
        'VALUES (:u,:s,:c,:ca,now()) RETURNING id, created_at, updated_at',
        {'u': usuario['id'], 's': submission_id, 'c': corpo.comment, 'ca': criado})
    c = linhas[0]
    return {'id': c['id'], 'user': {'id': usuario['id'], 'name': usuario['name']},
            'submission_id': submission_id, 'comment': corpo.comment,
            'created_at': c['created_at'], 'updated_at': c['updated_at']}


@app.delete('/submissions/comments/{comment_id}')
async def remover_comentario(comment_id: int, usuario=Depends(exigir_usuario)):
    linhas = await PREJANUS.consulta(
        'SELECT user_id FROM comment WHERE id=:i', {'i': comment_id})
    if not linhas:
        raise HTTPException(404, 'Comentário não encontrado')
    if linhas[0]['user_id'] != usuario['id']:
        raise HTTPException(403, 'Comentário de outro usuário')
    await PREJANUS.comando('DELETE FROM comment WHERE id=:i', {'i': comment_id})
    return Response(status_code=204)


@app.get('/submissions/{submission_id}/labels')
async def catalogo_rotulos(submission_id: int, usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    linhas = await PREJANUS.consulta(
        'SELECT MIN(id) AS id, label, color FROM labels WHERE user_id=:u '
        'GROUP BY label, color ORDER BY label', {'u': usuario['id']})
    return {'labels': [{'id': l['id'], 'label': l['label'], 'color': l['color']}
                      for l in linhas]}


@app.post('/submissions/{submission_id}/labels')
async def criar_rotulo(submission_id: int, corpo: CorpoRotulo,
                       usuario=Depends(exigir_usuario)):
    _, edital = await submissao_e_edital(submission_id)
    if edital['phase'] != 'avaliacao':
        raise HTTPException(400, 'Fora da fase de avaliação')
    await PREJANUS.comando(
        'UPDATE labels SET color=:c WHERE user_id=:u AND label=:l',
        {'c': corpo.color, 'u': usuario['id'], 'l': corpo.label})
    existente = await PREJANUS.consulta(
        "SELECT id FROM labels WHERE user_id=:u AND submission_id=:s "
        "AND label=:l AND context_type='candidate'",
        {'u': usuario['id'], 's': submission_id, 'l': corpo.label})
    if existente:
        rotulo_id = existente[0]['id']
    else:
        rotulo_id = (await PREJANUS.comando(
            "INSERT INTO labels(user_id, submission_id, label, color, context_type) "
            "VALUES (:u,:s,:l,:c,'candidate') RETURNING id",
            {'u': usuario['id'], 's': submission_id, 'l': corpo.label,
             'c': corpo.color}))[0]['id']
    return {'id': rotulo_id, 'user': {'id': usuario['id'], 'name': usuario['name']},
            'submission_id': submission_id, 'label': corpo.label, 'color': corpo.color}


@app.delete('/submissions/label/{label_id}')
async def remover_rotulo(label_id: int, usuario=Depends(exigir_usuario)):
    linhas = await PREJANUS.consulta(
        'SELECT user_id FROM labels WHERE id=:i', {'i': label_id})
    if not linhas:
        raise HTTPException(404, 'Etiqueta não encontrada')
    if linhas[0]['user_id'] != usuario['id']:
        raise HTTPException(403, 'Etiqueta de outro usuário')
    await PREJANUS.comando('DELETE FROM labels WHERE id=:i', {'i': label_id})
    return Response(status_code=204)


@app.post('/submissions/{submission_id}/private_notes')
async def criar_nota(submission_id: int, corpo: CorpoNota,
                     usuario=Depends(exigir_usuario)):
    _, edital = await submissao_e_edital(submission_id)
    if edital['phase'] != 'avaliacao':
        raise HTTPException(400, 'Fora da fase de avaliação')
    await PREJANUS.comando(
        'INSERT INTO private_note(user_id, submission_id, note, created_at, updated_at) '
        'VALUES (:u,:s,:n,now(),now()) '
        'ON CONFLICT (user_id, submission_id) DO UPDATE SET note=:n, updated_at=now()',
        {'u': usuario['id'], 's': submission_id, 'n': corpo.note})
    return {'note': corpo.note}


@app.post('/submissions/{submission_id}/favorites')
async def criar_favorito(submission_id: int, usuario=Depends(exigir_usuario)):
    _, edital = await submissao_e_edital(submission_id)
    if edital['phase'] != 'avaliacao':
        raise HTTPException(400, 'Fora da fase de avaliação')
    await PREJANUS.comando(
        'INSERT INTO favorites(user_id, submission_id, created_at) '
        'VALUES (:u,:s,now()) ON CONFLICT DO NOTHING',
        {'u': usuario['id'], 's': submission_id})
    return JSONResponse(status_code=201, content='Favorito registrado')


@app.delete('/submissions/{submission_id}/favorites')
async def remover_favorito(submission_id: int, usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    await PREJANUS.comando(
        'DELETE FROM favorites WHERE user_id=:u AND submission_id=:s',
        {'u': usuario['id'], 's': submission_id})
    return 'Favorito removido'


@app.post('/submissions/{submission_id}/view')
async def registrar_visualizacao(submission_id: int,
                                 usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    hoje = await PREJANUS.consulta(
        'SELECT id FROM submission_view WHERE user_id=:u AND submission_id=:s '
        'AND created_at::date = now()::date',
        {'u': usuario['id'], 's': submission_id})
    if hoje:
        await PREJANUS.comando(
            'UPDATE submission_view SET updated_at=now() WHERE id=:i',
            {'i': hoje[0]['id']})
    else:
        await PREJANUS.comando(
            'INSERT INTO submission_view(user_id, submission_id, created_at, updated_at) '
            'VALUES (:u,:s,now(),now())', {'u': usuario['id'], 's': submission_id})
    return {'message': 'Visualização registrada'}


@app.get('/submissions/{submission_id}/view')
async def listar_visualizacoes(submission_id: int, usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    linhas = await PREJANUS.consulta(
        'SELECT v.*, u.name AS user_name FROM submission_view v '
        'JOIN "user" u ON u.id=v.user_id WHERE v.submission_id=:s ORDER BY v.id',
        {'s': submission_id})
    return [{'id': v['id'], 'user': {'id': v['user_id'], 'name': v['user_name']},
             'created_at': v['created_at'], 'updated_at': v['updated_at']} for v in linhas]


@app.post('/submissions/{submission_id}/select')
async def selecionar(submission_id: int, corpo: CorpoSelecao,
                     usuario=Depends(exigir_usuario)):
    s, edital = await submissao_e_edital(submission_id)
    if not edital['is_open']:
        raise HTTPException(409, 'Edital encerrado')
    orientador = s['advisor_id']
    if corpo.stats == 'approved' and corpo.user_ids:
        orientador = corpo.user_ids[0]
    await PREJANUS.comando(
        'UPDATE submission SET stats=:st, advisor_id=:a, updated_at=now() WHERE id=:i',
        {'st': corpo.stats, 'a': orientador, 'i': submission_id})
    return 'Situação atualizada'


@app.post('/submissions/{submission_id}/entry-semester')
async def semestre_ingresso(submission_id: int, corpo: CorpoSemestre,
                            usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    texto = corpo.semestre.strip().lower()
    if 'prim' in texto or 'first' in texto:
        normalizado = 'Primeiro semestre.'
    elif 'seg' in texto or 'second' in texto:
        normalizado = 'Segundo semestre.'
    else:
        normalizado = corpo.semestre
    await PREJANUS.comando(
        'UPDATE submission SET entry_semester=:e, updated_at=now() WHERE id=:i',
        {'e': normalizado, 'i': submission_id})
    return 'Semestre de ingresso atualizado'


@app.post('/submissions/{submission_id}/bidding')
async def licitar(submission_id: int, corpo: CorpoLicitacao,
                  usuario=Depends(exigir_usuario)):
    await submissao_e_edital(submission_id)
    alvo = corpo.user_id if (corpo.user_id and eh_admin(usuario)) else usuario['id']
    await PREJANUS.comando(
        "DELETE FROM labels WHERE user_id=:u AND submission_id=:s "
        "AND context_type='bidding'", {'u': alvo, 's': submission_id})
    if corpo.bidding != '':
        await PREJANUS.comando(
            "INSERT INTO labels(user_id, submission_id, label, color, context_type) "
            "VALUES (:u,:s,:b,'#000000','bidding')",
            {'u': alvo, 's': submission_id, 'b': corpo.bidding})
    return 'Interesse registrado'


@app.post('/submissions/{submission_id}/reesend_submission')
async def reenviar_submissao(submission_id: int, corpo: CorpoReenvio,
                             usuario=Depends(exigir_usuario)):
    s, edital = await submissao_e_edital(submission_id)
    if edital['phase'] != 'homologacao':
        raise HTTPException(400, 'Fora da fase de homologação')
    resp = await resposta_candidato(s['candidate_form_id'])
    await FORMS.comando(
        'UPDATE form_response SET current_section=0 WHERE id=:i', {'i': resp['id']})
    texto = (f"{corpo.text}\n\n"
             f"Acesse o formulário para atualizar sua inscrição:\n"
             f"{BASE_URL}/form/{resp['token']}\n")
    enviar_email(para=resp['email'], bcc=[usuario['email']],
                 assunto='Correção de inscrição', texto=texto)
    return {'message': 'Solicitação de correção enviada', 'email_sent': resp['email']}


@app.post('/submissions/{submission_id}/send-accept')
async def enviar_aceite(submission_id: int, usuario=Depends(exigir_usuario)):
    s, edital = await submissao_e_edital(submission_id)
    if s['stats'] != 'approved':
        raise HTTPException(400, 'Inscrição não aprovada')
    if s['accept_form_id']:
        raise HTTPException(400, 'Formulário de aceite já enviado')
    if not edital['accept_forms']:
        raise HTTPException(404, 'Edital sem formulário de aceite configurado')
    form_id = int(edital['accept_forms'])
    expiracao = edital['closed_date']
    compartilhado = (await FORMS.comando(
        'INSERT INTO form_shared(form_id, token, unique_answers, is_public, '
        'expiration_at, created_at) VALUES (:f,:t,true,false,:exp,now()) RETURNING id',
        {'f': form_id, 't': str(uuid.uuid4()), 'exp': expiracao}))[0]
    token = str(uuid.uuid4())
    resposta = (await FORMS.comando(
        'INSERT INTO form_response(form_id, shared_id, email, token, current_section, '
        'submitted_at, metadata, form_version) '
        "VALUES (:f,:sh,:e,:t,0,NULL,'{}',1) RETURNING id",
        {'f': form_id, 'sh': compartilhado['id'], 'e': s_email(s, edital),
         't': token}))[0]
    await PREJANUS.comando(
        'UPDATE submission SET accept_form_id=:a, updated_at=now() WHERE id=:i',
        {'a': resposta['id'], 'i': submission_id})
    nome = (await dados_leves(s, edital))['name']
    pt = format_date(expiracao, format='long', locale='pt_BR')
    en = format_date(expiracao, format='long', locale='en_US')
    texto = (f"Prezado(a) {nome},\n\n"
             "Parabéns! Sua inscrição foi aprovada no programa.\n"
             "Para confirmar o aceite da vaga, preencha o formulário no link abaixo:\n"
             f"{BASE_URL}/form/{token}\n\n"
             f"O prazo de confirmação vai até {pt} ({en}).\n")
    cc = [s['advisor_email']] if s['advisor_id'] and s['advisor_email'] else None
    enviar_email(para=s_email(s, edital), cc=cc, assunto='Confirmação de aceite da vaga',
                 texto=texto)
    return {'message': 'Formulário de aceite enviado', 'email_sent': s_email(s, edital)}


@app.post('/submissions/{submission_id}/send-letter')
async def enviar_carta(submission_id: int, usuario=Depends(exigir_usuario)):
    s, edital = await submissao_e_edital(submission_id)
    if s['stats'] != 'approved':
        raise HTTPException(400, 'Inscrição não aprovada')
    if s['letter_sent']:
        raise HTTPException(400, 'Carta já enviada')
    nome = (await dados_leves(s, edital))['name']
    email = s_email(s, edital)
    texto = (f"Prezado(a) {nome},\n\n"
             "Sua inscrição foi aprovada. Segue a carta de aprovação.\n")
    enviar_email(para=email, assunto='Carta de aprovação', texto=texto)
    await PREJANUS.comando(
        'UPDATE submission SET letter_sent=true, updated_at=now() WHERE id=:i',
        {'i': submission_id})
    return {'message': 'Carta de aprovação enviada', 'email_sent': email}


async def s_email(s: dict, edital: dict) -> str:
    resp = await resposta_candidato(s['candidate_form_id'])
    return resp['email'] or ''

# ---------------------------------------------------------------- formulários


@app.get('/forms')
async def listar_formularios(year: str = None, notice: str = None,
                              usuario=Depends(exigir_usuario)):
    q = ("SELECT id, title->>'pt' AS title, description->>'pt' AS description, "
         'created_at, tags, phase::text AS phase, version FROM form '
         'WHERE (:y IS NULL OR tags->>\'Ano\' = :y) '
         'AND (:n IS NULL OR tags->>\'Edital\' = :n) ORDER BY id')
    linhas = await FORMS.consulta(q, {'y': year, 'n': notice})
    for l in linhas:
        l['tags'] = como_json(l['tags'])
    return linhas


async def secoes_do_formulario(form_id: int, versao: int = None) -> list:
    if versao is None:
        secoes = await FORMS.consulta(
            'SELECT * FROM form_section WHERE form_id=:f AND is_active '
            'ORDER BY position, id', {'f': form_id})
    else:
        secoes = await FORMS.consulta(
            'SELECT * FROM form_section WHERE form_id=:f AND version=:v '
            'ORDER BY position, id', {'f': form_id, 'v': versao})
        if not secoes:
            secoes = await FORMS.consulta(
                'SELECT * FROM form_section WHERE form_id=:f ORDER BY position, id',
                {'f': form_id})
    resultado = []
    for sec in secoes:
        campos = await FORMS.consulta(
            'SELECT * FROM form_field WHERE section_id=:s ORDER BY position, id',
            {'s': sec['id']})
        saida = dict(sec)
        saida['title'] = como_json(sec['title'])
        saida['description'] = como_json(sec['description'])
        saida['fields'] = [campo_json(c) for c in campos]
        resultado.append(saida)
    return resultado


def campo_json(c: dict) -> dict:
    saida = dict(c)
    saida['label'] = como_json(c['label'])
    saida['description'] = como_json(c['description'])
    saida['error_message'] = como_json(c['error_message'])
    return saida


@app.get('/forms/{form_id}')
async def formulario_completo(form_id: int, version: int = None,
                              usuario=Depends(exigir_usuario)):
    return await secoes_do_formulario(form_id, version)


@app.get('/forms/{form_id}/sections')
async def secoes(form_id: int, version: int = None,
                 usuario=Depends(exigir_usuario)):
    return await secoes_do_formulario(form_id, version)


@app.get('/forms/{form_id}/sessions/{section_id}/fields')
async def campos_da_secao(form_id: int, section_id: int,
                          usuario=Depends(exigir_usuario)):
    linhas = await FORMS.consulta(
        'SELECT * FROM form_field WHERE section_id=:s ORDER BY position, id',
        {'s': section_id})
    return [campo_json(c) for c in linhas]
