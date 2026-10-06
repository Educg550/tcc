import 
import sys
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

CAMPOS_BASE = {
    'ABA': 'ALUNOS',
    'NOME COMPLETO - SEM ABREVIAR': 'Maria de Souza Silva',
    'N. USP': '1234567',
    'PROGRAMA': 'Ciência da Computação',
    'NÍVEL': 'Doutorado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'maria.ss@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'Simpósio Brasileiro de Computação',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': '10 a 15 de agosto de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'São Paulo',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://eventos.usp.br/simposio',
    'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Inscrição no evento e passagem aérea',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1990',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NÚMERO': '181',
    'COMPLEMENTO': 'Bloco A',
    'BAIRRO': 'Butantã',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '111.444.777-35',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '1234',
    'NÚMERO DA CONTA': '98765-4',
}


@pytest.fixture(scope='session')
def client():
    import app

    with TestClient(app.app) as test_client:
        yield test_client


@pytest.fixture(scope='session')
def caminho_submissao(client):
    rotas_post = [
        rota.path
        for rota in client.app.routes
        if isinstance(rota, APIRoute) and 'POST' in rota.methods
    ]
    assert rotas_post, 'o backend precisa expor uma rota POST para receber a solicitação'
    return rotas_post[0]


@pytest.fixture
def submeter(client, caminho_submissao):
    def _submeter(dados):
        resposta = client.post(caminho_submissao, =dados)
        try:
            return .dumps(resposta.(), ensure_ascii=False)
        except ValueError:
            return resposta.text

    return _submeter


@pytest.fixture
def dados_alunos():
    def _dados(**substituicoes):
        dados = dict(CAMPOS_BASE)
        dados.update(substituicoes)
        return dados

    return _dados


@pytest.fixture
def dados_docentes():
    def _dados(**substituicoes):
        dados = {
            campo: valor
            for campo, valor in CAMPOS_BASE.items()
            if campo not in ('NÍVEL', 'TIPO DE AUXÍLIO')
        }
        dados['ABA'] = 'DOCENTES'
        dados.update(substituicoes)
        return dados

    return _dados
