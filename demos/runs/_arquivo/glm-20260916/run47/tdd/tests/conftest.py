import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


@pytest.fixture(scope='session')
def client():
    from app import app

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope='session')
def html(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope='session')
def css(client):
    resposta = client.get('/style.css')
    assert resposta.status_code == 200
    return resposta.text


@pytest.fixture(scope='session')
def js(client):
    resposta = client.get('/app.js')
    assert resposta.status_code == 200
    return resposta.text


# Cada campo pode chegar ao backend com varios nomes; todas as variantes
# de um mesmo campo sao enviadas sempre com o mesmo valor.
GRUPOS = {
    'nome': ['nome_completo', 'nome', 'NOME COMPLETO - SEM ABREVIAR'],
    'n_usp': ['n_usp', 'numero_usp', 'N. USP'],
    'programa': ['programa', 'PROGRAMA'],
    'nivel': ['nivel', 'grau', 'NÍVEL'],
    'tipo_auxilio': ['tipo_auxilio', 'tipo_de_auxilio', 'TIPO DE AUXÍLIO'],
    'email': ['email', 'e_mail', 'E-MAIL'],
    'nome_evento': [
        'nome_evento',
        'evento',
        'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    ],
    'periodo': [
        'periodo_evento',
        'periodo',
        'PERÍODO DO EVENTO, EXAME OU DEFESA',
    ],
    'cidade_evento': [
        'cidade_evento',
        'cidade_do_evento',
        'CIDADE DO EVENTO, EXAME OU DEFESA',
    ],
    'estado_evento': [
        'estado_evento',
        'estado_do_evento',
        'ESTADO DO EVENTO, EXAME OU DEFESA',
    ],
    'pais_evento': [
        'pais_evento',
        'pais_do_evento',
        'PAÍS DO EVENTO, EXAME OU DEFESA',
    ],
    'link_evento': [
        'link_evento',
        'link',
        'url_evento',
        'LINK DO EVENTO, EXAME OU DEFESA',
    ],
    'valor': ['valor_solicitado', 'valor', 'VALOR SOLICITADO (R$)'],
    'detalhamento': [
        'detalhamento',
        'detalhamento_pedido',
        'DETALHAMENTO DO PEDIDO',
    ],
    'apresentacao': [
        'apresentacao',
        'apresentacao_trabalho',
        'ira_apresentar_trabalho',
        'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    ],
    'data_nascimento': [
        'data_nascimento',
        'data_de_nascimento',
        'DATA DE NASCIMENTO',
    ],
    'logradouro': ['logradouro', 'LOGRADOURO'],
    'numero': ['numero', 'NÚMERO'],
    'complemento': ['complemento', 'COMPLEMENTO'],
    'bairro': ['bairro', 'BAIRRO'],
    'cep': ['cep', 'CEP'],
    'cidade': ['cidade', 'CIDADE'],
    'estado': ['estado', 'ESTADO'],
    'cpf': ['cpf', 'CPF (SEPARADOS POR PONTOS E TRAÇO)'],
    'rg_rnm': ['rg_rnm', 'rg', 'rnm', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'],
    'banco': ['banco', 'nome_banco', 'nome_do_banco', 'NOME DO BANCO'],
    'agencia': [
        'agencia',
        'numero_agencia',
        'numero_da_agencia',
        'NÚMERO DA AGÊNCIA',
    ],
    'conta': ['conta', 'numero_conta', 'numero_da_conta', 'NÚMERO DA CONTA'],
}

CHAVES_DE_ABA = [
    'aba',
    'formulario',
    'origem',
    'categoria',
    'tipo_formulario',
    'tipo_solicitacao',
    'perfil',
    'tipo_solicitante',
    'papel',
]

VALORES = {
    'nome': 'Maria de Souza Silva',
    'n_usp': '1234567',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria@usp.br',
    'nome_evento': 'Simpósio Brasileiro de Computação',
    'periodo': '10 a 15 de março de 2025',
    'cidade_evento': 'Rio de Janeiro',
    'estado_evento': 'RJ',
    'pais_evento': 'Brasil',
    'link_evento': 'https://sbc.org.br/evento',
    'valor': 'R$ 1.500,00',
    'detalhamento': 'Passagem aérea e inscrição no evento',
    'apresentacao': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero': '181',
    'complemento': 'Sala 12',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg_rnm': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '98765-4',
}


def campos(aba='alunos', vazios=()):
    dados = {}
    for grupo, chaves in GRUPOS.items():
        valor = '' if grupo in vazios else VALORES[grupo]
        for chave in chaves:
            dados[chave] = valor
    singular = aba[:-1]
    singulares = ('perfil', 'tipo_solicitante', 'papel')
    for chave in CHAVES_DE_ABA:
        dados[chave] = singular if chave in singulares else aba
    return dados


def trocar(dados, grupo, valor):
    for chave in GRUPOS[grupo]:
        dados[chave] = valor
    return dados


@pytest.fixture(scope='session')
def post_solicitacao(client):
    from app import app

    caminhos = [
        rota.path
        for rota in app.routes
        if 'POST' in (getattr(rota, 'methods', None) or set())
    ]
    assert caminhos, 'o backend precisa de uma rota POST para receber a solicitação'

    def enviar(dados, sonda):
        primeira = None
        for caminho in caminhos:
            for resposta in (
                client.post(caminho, =dados),
                client.post(caminho, data=dados),
            ):
                if primeira is None:
                    primeira = resposta
                if sonda in resposta.text:
                    return resposta
        return primeira

    return enviar
