import pathlib
import re
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

ROTULOS = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'NÍVEL',
    'TIPO DE AUXÍLIO',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAÍS DO EVENTO, EXAME OU DEFESA',
    'LINK DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]


class NomesDeCampos(dict):
    def __missing__(self, rotulo):
        return rotulo


def caminho_estatico(html, sufixo):
    for m in re.finditer(r'(?:href|src)="([^"]+)"', html):
        caminho = m.group(1).split('?')[0].split('#')[0]
        if caminho.endswith(sufixo) and not caminho.startswith(('http://', 'https://')):
            return caminho if caminho.startswith('/') else '/' + caminho
    return '/' + sufixo


def _limpar(texto):
    return re.sub(r'\s+', ' ', texto).strip()


def _chave(texto):
    return _limpar(texto.replace('*', ' ')).casefold()


def _mapear_rotulos(html):
    nome_por_id = {}
    for tag in re.findall(r'<(?:input|select|textarea)\b[^>]*>', html, re.I):
        idm = re.search(r'\bid="([^"]+)"', tag, re.I)
        nmm = re.search(r'\bname="([^"]+)"', tag, re.I)
        if idm:
            nome_por_id[idm.group(1)] = nmm.group(1) if nmm else idm.group(1)
    pares = {}
    for m in re.finditer(r'<label\b([^>]*)>(.*?)</label>', html, re.I | re.S):
        attrs, interno = m.groups()
        texto = _limpar(re.sub(r'<[^>]+>', ' ', interno))
        rotulo = _chave(texto)
        form = re.search(r'\bfor="([^"]+)"', attrs, re.I)
        if form and form.group(1) in nome_por_id:
            pares[rotulo] = nome_por_id[form.group(1)]
            continue
        nmm = re.search(r'\bname="([^"]+)"', interno, re.I)
        if nmm:
            pares.setdefault(rotulo, nmm.group(1))
    return pares


def _rotas_de_envio(client):
    candidatas = []
    pagina = client.get('/').text
    js = client.get(caminho_estatico(pagina, 'app.js')).text
    for m in re.finditer(r'fetch\(\s*"([^"]+)"', js):
        caminho = m.group(1).split('?')[0]
        candidatas.append(caminho if caminho.startswith('/') else '/' + caminho)
    for rota in app.routes:
        if 'POST' in (getattr(rota, 'methods', None) or set()):
            candidatas.append(rota.path)
    return candidatas


def enviar(client, payload):
    for caminho in _rotas_de_envio(client):
        resposta = client.post(caminho, =payload)
        if resposta.status_code == 422:
            por_form = client.post(caminho, data=payload)
            if por_form.status_code != 422:
                return por_form
            continue
        return resposta
    pytest.fail('Nenhuma rota de backend recebe a solicitação')


def payload_de_aluno(nomes):
    return {
        nomes['NOME COMPLETO - SEM ABREVIAR']: 'Maria da Silva',
        nomes['N. USP']: '1234567',
        nomes['PROGRAMA']: 'Ciência da Computação',
        nomes['NÍVEL']: 'Mestrado',
        nomes['TIPO DE AUXÍLIO']: 'Participação em evento',
        nomes['E-MAIL']: 'maria@usp.br',
        nomes['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']: 'Congresso Brasileiro de Computação',
        nomes['PERÍODO DO EVENTO, EXAME OU DEFESA']: '1 a 5 de julho de 2025',
        nomes['CIDADE DO EVENTO, EXAME OU DEFESA']: 'São Paulo',
        nomes['ESTADO DO EVENTO, EXAME OU DEFESA']: 'SP',
        nomes['PAÍS DO EVENTO, EXAME OU DEFESA']: 'Brasil',
        nomes['LINK DO EVENTO, EXAME OU DEFESA']: 'https://evento.usp.br',
        nomes['VALOR SOLICITADO (R$)']: 'R$ 1.500,00',
        nomes['DETALHAMENTO DO PEDIDO']: 'Passagem aérea e inscrição no evento.',
        nomes['DATA DE NASCIMENTO']: '01/02/1980',
        nomes['LOGRADOURO']: 'Rua do Anfiteatro',
        nomes['NÚMERO']: '123',
        nomes['COMPLEMENTO']: 'Sala 5',
        nomes['BAIRRO']: 'Butantã',
        nomes['CEP']: '05508-090',
        nomes['CIDADE']: 'São Paulo',
        nomes['ESTADO']: 'SP',
        nomes['CPF (SEPARADOS POR PONTOS E TRAÇO)']: '123.456.789-09',
        nomes['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']: '12.345.678-9',
        nomes['NOME DO BANCO']: 'Banco do Brasil',
        nomes['NÚMERO DA AGÊNCIA']: '1234',
        nomes['NÚMERO DA CONTA']: '98765-4',
    }


@pytest.fixture(scope='session')
def client():
    return TestClient(app)


@pytest.fixture(scope='session')
def index_html(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope='session')
def app_js(client, index_html):
    resposta = client.get(caminho_estatico(index_html, 'app.js'))
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope='session')
def nomes(index_html):
    return NomesDeCampos(_mapear_rotulos(index_html))
