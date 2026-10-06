import 
import re
import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402

cliente = TestClient(app)

VALIDOS = {
    'nome': 'Maria de Souza Silva',
    'n_usp': '1234567',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria.silva@usp.br',
    'evento': 'SBBD',
    'periodo': '30/09/2025 a 03/10/2025',
    'cidade_evento': 'São Paulo',
    'estado_evento': 'SP',
    'pais_evento': 'Brasil',
    'link': 'https://sbbd.org.br',
    'valor': 'R$ 1.500,00',
    'detalhamento': 'Inscrição e passagem aérea.',
    'apresentacao': 'Pôster',
    'nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero': '155',
    'complemento': 'Sala 101',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '12345-6',
}

# Fallback caso o endpoint não exponha um modelo com nomes de campo.
CHAVES_PADRAO = [
    'nome', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email', 'evento',
    'periodo', 'cidade_evento', 'estado_evento', 'pais_evento', 'link_evento',
    'valor_solicitado', 'detalhamento', 'apresentacao', 'data_nascimento',
    'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
]

# Mapeia o nome que o backend dá a cada campo para uma chave semântica.
PADROES = [
    ('cidadedoevento', 'cidade_evento'),
    ('estadodoevento', 'estado_evento'),
    ('paisdoevento', 'pais_evento'),
    ('nomedoevento', 'evento'),
    ('linkdoevento', 'link'),
    ('periododoevento', 'periodo'),
    ('cidadeevento', 'cidade_evento'),
    ('estadoevento', 'estado_evento'),
    ('paisevento', 'pais_evento'),
    ('nomeevento', 'evento'),
    ('linkevento', 'link'),
    ('periodoevento', 'periodo'),
    ('trabalho', 'apresentacao'),
    ('apresent', 'apresentacao'),
    ('tipoauxilio', 'tipo_auxilio'),
    ('auxilio', 'tipo_auxilio'),
    ('banca', 'evento'),
    ('evento', 'evento'),
    ('detalhamento', 'detalhamento'),
    ('nascimento', 'nascimento'),
    ('valor', 'valor'),
    ('programa', 'programa'),
    ('nivel', 'nivel'),
    ('email', 'email'),
    ('agencia', 'agencia'),
    ('conta', 'conta'),
    ('complemento', 'complemento'),
    ('bairro', 'bairro'),
    ('cep', 'cep'),
    ('cpf', 'cpf'),
    ('banco', 'banco'),
    ('numerousp', 'n_usp'),
    ('numerodeusp', 'n_usp'),
    ('nuspusp', 'n_usp'),
    ('usp', 'n_usp'),
    ('logradouro', 'logradouro'),
    ('numero', 'numero'),
    ('cidade', 'cidade'),
    ('estado', 'estado'),
    ('rg', 'rg'),
    ('link', 'link'),
    ('nome', 'nome'),
]


def _normalizar(nome):
    texto = unicodedata.normalize('NFKD', str(nome))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', texto.lower())


def _chave_de(nome):
    n = _normalizar(nome)
    for padrao, chave in PADROES:
        if padrao in n:
            return chave
    return None


def _texto(resp):
    try:
        return .dumps(resp.(), ensure_ascii=False)
    except Exception:
        return resp.text


def _valor_cru(chave, valor):
    if chave in ('valor', 'cpf', 'cep', 'nascimento'):
        return re.sub(r'\D', '', str(valor)) or str(valor)
    return valor


def _payload(campos, aba='alunos', **alteracoes):
    dados = {}
    for nome in campos:
        chave = _chave_de(nome)
        if aba == 'docentes' and chave in ('nivel', 'tipo_auxilio') and chave not in alteracoes:
            continue
        dados[nome] = alteracoes.get(chave, VALIDOS.get(chave, 'Preenchimento de exemplo'))
    return dados


@pytest.fixture(scope='session')
def client():
    return cliente


@pytest.fixture(scope='session')
def index(client):
    resp = client.get('/')
    assert resp.status_code == 200
    return resp.text


@pytest.fixture(scope='session')
def rota_post():
    rotas = [r.path for r in app.routes if 'POST' in getattr(r, 'methods', set())]
    assert rotas, 'backend não expõe rota POST para a solicitação'
    return rotas[0]


@pytest.fixture(scope='session')
def campos(rota_post):
    for r in app.routes:
        if r.path == rota_post and 'POST' in getattr(r, 'methods', set()):
            tipo = getattr(getattr(r, 'body_field', None), 'type_', None)
            if tipo is not None and hasattr(tipo, 'model_fields'):
                return list(tipo.model_fields)
    return CHAVES_PADRAO


@pytest.fixture(scope='session')
def montar(campos):
    def _montar(aba='alunos', **alteracoes):
        return _payload(campos, aba, **alteracoes)

    return _montar


@pytest.fixture(scope='session')
def enviar(rota_post):
    def _enviar(payload, deve_conter):
        ultimo = ''
        for cru in (False, True):
            dados = payload
            if cru:
                dados = {n: _valor_cru(_chave_de(n), v) for n, v in payload.items()}
            for modo in ('', 'form'):
                if modo == '':
                    resp = cliente.post(rota_post, =dados)
                else:
                    resp = cliente.post(rota_post, data=dados)
                conteudo = _texto(resp)
                if deve_conter in conteudo:
                    return conteudo
                ultimo = conteudo
        return ultimo

    return _enviar
