import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app  # noqa: E402

# Contrato testado do backend:
# - POST na rota da aplicação com JSON cujas chaves são os rótulos exatos dos
#   campos, mais 'aba' ('ALUNOS' ou 'DOCENTES'); o valor de
#   'VALOR SOLICITADO (R$)' é a sequência de dígitos digitada (centavos).
# - Resposta JSON {'erros': [...], 'oficio': ...}: a lista de mensagens de erro
#   e, quando a solicitação é válida, o ofício redigido com os dados no lugar
#   dos marcadores.

CAMPOS_ALUNOS = {
    'aba': 'ALUNOS',
    'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva',
    'N. USP': '1234567',
    'PROGRAMA': 'Ciência da Computação',
    'NÍVEL': 'Mestrado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'maria.silva@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBES 2025',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': '22 a 26 de setembro de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'Fortaleza',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'Ceará',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbes.org.br/2025',
    'VALOR SOLICITADO (R$)': '150000',
    'DETALHAMENTO DO PEDIDO': 'Passagem aérea e inscrição no evento',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NÚMERO': '375',
    'COMPLEMENTO': 'Sala 2',
    'BAIRRO': 'Butantã',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'São Paulo',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '111.444.777-35',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '0001',
    'NÚMERO DA CONTA': '12345-6',
}

CAMPOS_DOCENTES = {
    chave: valor
    for chave, valor in CAMPOS_ALUNOS.items()
    if chave not in ('NÍVEL', 'TIPO DE AUXÍLIO')
} | {'aba': 'DOCENTES'}


def _rota_de_postagem():
    for rota in app.routes:
        if 'POST' in (getattr(rota, 'methods', None) or set()):
            return rota.path
    pytest.fail('a aplicação não tem rota POST para receber a solicitação')


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def enviar(cliente):
    def acao(campos):
        resposta = cliente.post(_rota_de_postagem(), =campos)
        assert resposta.status_code in (200, 201, 400, 422), resposta.text
        dados = resposta.()
        oficio = dados.get('oficio')
        if isinstance(oficio, list):
            oficio = '\n'.join(str(linha) for linha in oficio)
        if isinstance(oficio, str):
            oficio = oficio.replace('\r\n', '\n')
        return {'erros': dados.get('erros', []), 'oficio': oficio}

    return acao


@pytest.fixture
def campos_alunos():
    return dict(CAMPOS_ALUNOS)


@pytest.fixture
def campos_docentes():
    return dict(CAMPOS_DOCENTES)


@pytest.fixture
def arquivo_estatico(cliente):
    def buscar(*caminhos):
        for caminho in caminhos:
            resposta = cliente.get(caminho)
            if resposta.status_code == 200:
                return resposta
        pytest.fail('nenhum de ' + ', '.join(caminhos) + ' é servido')

    return buscar
