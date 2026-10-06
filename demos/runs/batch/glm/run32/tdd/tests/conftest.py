"""Fixtures compartilhadas dos testes."""
import pytest
from fastapi.testclient import TestClient

from app import app


SOLICITACAO_VALIDA = {
    "aba": "alunos",
    "nome": "Maria da Silva",
    "nusp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo": "Banca de exame ou defesa",
    "email": "joao@ime.usp.br",
    "evento": "Congresso Nacional",
    "periodo": "10 a 12 de agosto",
    "cidade": "São Paulo",
    "estado_evento": "SP",
    "pais": "Brasil",
    "link": "www.congreso.br",
    "valor": "R$ 1.500,00",
    "detalhamento": "Auxílio para passagens.",
    "apresentacao": "Pôster",
    "nascimento": "01/02/1980",
    "logradouro": "Rua Sul",
    "numero": "123",
    "complemento": "Apto 45",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade_end": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "54321-X",
}

SOLICITACAO_DOCENTE_VALIDA = {
    "aba": "docentes",
    "nome": "Maria da Silva",
    "nusp": "12345678",
    "programa": "Matemática",
    "email": "joao@ime.usp.br",
    "evento": "Congresso Nacional",
    "periodo": "10 a 12 de agosto",
    "cidade": "São Paulo",
    "estado_evento": "SP",
    "pais": "Brasil",
    "link": "www.congreso.br",
    "valor": "R$ 1.500,00",
    "detalhamento": "Auxílio para passagens.",
    "apresentacao": "Pôster",
    "nascimento": "01/02/1980",
    "logradouro": "Rua Sul",
    "numero": "123",
    "complemento": "Apto 45",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade_end": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "54321-X",
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def corpo_index(client):
    return client.get("/").text


def post(client, dados):
    return client.post("/solicitacao", json=dados)
