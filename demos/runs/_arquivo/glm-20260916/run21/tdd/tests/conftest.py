import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

POST_CANDIDATOS = [
    '/api/solicitacao',
    '/solicitacao',
    '/api/solicitacoes',
    '/solicitacoes',
    '/api/solicitar',
    '/solicitar',
    '/api/enviar',
    '/enviar',
    '/api/auxilio',
    '/auxilio',
    '/api/auxilio-financeiro',
    '/submit',
    '/api/submit',
]

_MARCAS = ('solicit', 'auxili', 'ofici', 'enviar', 'abrir')

_DESCOBERTAS = {}

# chave canônica -> apelidos que a aplicação pode usar (curtos e o rótulo exato)
_APELIDOS = {
    'nome_completo': ('nome', 'NOME COMPLETO - SEM ABREVIAR'),
    'n_usp': ('numero_usp', 'nusp', 'N. USP'),
    'programa': ('PROGRAMA',),
    'nivel': ('NÍVEL',),
    'tipo_auxilio': ('tipo_de_auxilio', 'TIPO DE AUXÍLIO'),
    'email': ('e_mail', 'E-MAIL'),
    'nome_evento': ('evento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'),
    'periodo_evento': ('periodo', 'PERÍODO DO EVENTO, EXAME OU DEFESA'),
    'cidade_evento': ('CIDADE DO EVENTO, EXAME OU DEFESA',),
    'estado_evento': ('ESTADO DO EVENTO, EXAME OU DEFESA',),
    'pais_evento': ('pais', 'PAÍS DO EVENTO, EXAME OU DEFESA'),
    'link_evento': ('link', 'LINK DO EVENTO, EXAME OU DEFESA'),
    'valor_solicitado': ('valor', 'VALOR SOLICITADO (R$)'),
    'detalhamento': ('detalhamento_pedido', 'DETALHAMENTO DO PEDIDO'),
    'apresentacao_trabalho': (
        'ira_apresentar_trabalho',
        'apresentacao',
        'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    ),
    'data_nascimento': ('nascimento', 'DATA DE NASCIMENTO'),
    'logradouro': ('LOGRADOURO',),
    'numero': ('NÚMERO',),
    'complemento': ('COMPLEMENTO',),
    'bairro': ('BAIRRO',),
    'cep': ('CEP',),
    'cidade': ('CIDADE',),
    'estado': ('ESTADO',),
    'cpf': ('CPF (SEPARADOS POR PONTOS E TRAÇO)',),
    'rg_rnm': ('rg', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'),
    'nome_banco': ('banco', 'NOME DO BANCO'),
    'numero_agencia': ('agencia', 'NÚMERO DA AGÊNCIA'),
    'numero_conta': ('conta', 'NÚMERO DA CONTA'),
}

_VALORES = {
    'nome_completo': 'Maria da Silva Souza',
    'n_usp': '8765432',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria.souza@usp.br',
    'nome_evento': 'SBBD 2025',
    'periodo_evento': '6 a 9 de outubro de 2025',
    'cidade_evento': 'Rio de Janeiro',
    'estado_evento': 'RJ',
    'pais_evento': 'Brasil',
    'link_evento': 'https://sbbd.org.br/2025',
    'valor_solicitado': 'R$ 1.500,00',
    'detalhamento': 'Inscrição no evento e passagem aérea de ida e volta.',
    'apresentacao_trabalho': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero': '181',
    'complemento': 'Sala 214',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg_rnm': '12.345.678-9',
    'nome_banco': 'Banco do Brasil',
    'numero_agencia': '1234',
    'numero_conta': '98765-4',
}


@pytest.fixture(scope='session')
def client():
    return TestClient(app)


def _caminhos_com_post(client):
    resposta = client.get('/openapi.')
    if resposta.status_code != 200:
        return []
    try:
        caminhos = resposta.().get('paths', {})
    except ValueError:
        return []
    return [
        caminho
        for caminho, operacoes in caminhos.items()
        if isinstance(operacoes, dict) and 'post' in operacoes
    ]


def _descobrir(client, pista):
    caminhos = _caminhos_com_post(client)
    if pista:
        com_pista = [c for c in caminhos if pista in c.lower()]
        if com_pista:
            return com_pista[0]
    if len(caminhos) == 1:
        return caminhos[0]
    preferidos = [c for c in caminhos if any(m in c.lower() for m in _MARCAS)]
    if preferidos:
        return preferidos[0]
    if caminhos:
        return caminhos[0]
    for candidato in POST_CANDIDATOS:
        if client.post(candidato, ={}).status_code not in (404, 405):
            return candidato
    pytest.fail('Não encontrei o endpoint POST que recebe a solicitação.')


def postar(client, dados, pista=None):
    chave = pista or ''
    if chave not in _DESCOBERTAS:
        _DESCOBERTAS[chave] = _descobrir(client, pista)
    caminho = _DESCOBERTAS[chave]
    resposta = client.post(caminho, =dados)
    if resposta.status_code == 422:
        alternativa = client.post(caminho, data=dados)
        if alternativa.status_code != 422:
            return alternativa
    return resposta


def textos(resposta):
    try:
        dados = resposta.()
    except ValueError:
        return resposta.text
    partes = []

    def coletar(objeto):
        if isinstance(objeto, str):
            partes.append(objeto)
        elif isinstance(objeto, dict):
            for valor in objeto.values():
                coletar(valor)
        elif isinstance(objeto, (list, tuple)):
            for item in objeto:
                coletar(item)

    coletar(dados)
    return '\n'.join(partes)


def _expandidos(canonicos, aba):
    dados = {
        'aba': aba.upper(),
        'perfil': aba.lower(),
        'formulario': aba.upper(),
        'categoria': aba.lower(),
    }
    for chave, apelidos in _APELIDOS.items():
        if chave not in canonicos:
            continue
        valor = canonicos[chave]
        dados[chave] = valor
        for apelido in apelidos:
            dados[apelido] = valor
    return dados


def dados_alunos(**substituicoes):
    canonicos = dict(_VALORES)
    canonicos.update(substituicoes)
    return _expandidos(canonicos, 'ALUNOS')


def dados_docentes(**substituicoes):
    canonicos = {
        chave: valor
        for chave, valor in _VALORES.items()
        if chave not in ('nivel', 'tipo_auxilio')
    }
    canonicos.update(substituicoes)
    return _expandidos(canonicos, 'DOCENTES')


def dados_vazios():
    return _expandidos({chave: '' for chave in _VALORES}, 'ALUNOS')
