import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def payload_alunos():
    return {
        'aba': 'ALUNOS',
        'NOME COMPLETO - SEM ABREVIAR': 'Maria de Souza',
        'N. USP': '1234567',
        'PROGRAMA': 'Ciência da Computação',
        'NÍVEL': 'Mestrado',
        'TIPO DE AUXÍLIO': 'Participação em evento',
        'E-MAIL': 'maria@usp.br',
        'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBBC 2025',
        'PERÍODO DO EVENTO, EXAME OU DEFESA': '10/06/2025 a 13/06/2025',
        'CIDADE DO EVENTO, EXAME OU DEFESA': 'Águas de Lindóia',
        'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
        'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
        'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbbc.org.br/2025',
        'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
        'DETALHAMENTO DO PEDIDO': 'Passagem aérea e inscrição',
        'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
        'DATA DE NASCIMENTO': '01/02/1980',
        'LOGRADOURO': 'Rua do Anfiteatro',
        'NÚMERO': '181',
        'COMPLEMENTO': 'Sala 222',
        'BAIRRO': 'Cidade Universitária',
        'CEP': '05508-090',
        'CIDADE': 'São Paulo',
        'ESTADO': 'SP',
        'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
        'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
        'NOME DO BANCO': 'Banco do Brasil',
        'NÚMERO DA AGÊNCIA': '0001',
        'NÚMERO DA CONTA': '12345-6',
    }


@pytest.fixture()
def payload_docentes(payload_alunos):
    payload = dict(payload_alunos)
    payload['aba'] = 'DOCENTES'
    del payload['NÍVEL']
    del payload['TIPO DE AUXÍLIO']
    return payload


@pytest.fixture()
def pagina(client):
    return client.get('/').text + client.get('/app.js').text


@pytest.fixture()
def arquivos_front(client):
    return (
        client.get('/').text
        + client.get('/style.css').text
        + client.get('/app.js').text
    )
