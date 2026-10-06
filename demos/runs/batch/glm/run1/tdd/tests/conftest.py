import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)


def _solicitacao_valida():
    return {
        "perfil": "alunos",
        "nome": "Maria da Silva Souza",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Brasileiro de Matemática",
        "periodo": "10 a 14 de julho de 2025",
        "cidade_evento": "Porto Alegre",
        "estado_evento": "RS",
        "pais_evento": "Brasil",
        "link": "https://cbm.exemplo.br",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição no evento e passagens aéreas.",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Apto 21",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


@pytest.fixture()
def form_alunos():
    return _solicitacao_valida()


@pytest.fixture()
def form_docentes():
    form = _solicitacao_valida()
    form["perfil"] = "docentes"
    del form["nivel"]
    del form["tipo_auxilio"]
    return form
