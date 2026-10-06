import json
import re

import pytest
from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


ALUNOS_FIELDS = {
    "aba": "alunos",
    "nome": "Fulano de Tal",
    "nusp": "1234567",
    "programa": "Matematica",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participacao em evento",
    "email": "fulano@ime.usp.br",
    "evento": "Congresso X",
    "periodo": "01/02/2024 a 03/02/2024",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "pais": "Brasil",
    "link": "https://exemplo.com",
    "valor": "150000",
    "detalhamento": "Detalhes do pedido",
    "apresentacao": "Poster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua A",
    "numero": "100",
    "complemento": "",
    "bairro": "Butanta",
    "cep": "05508090",
    "cidade_endereco": "Sao Paulo",
    "estado_endereco": "SP",
    "cpf": "12345678909",
    "rg": "11.111.111-1",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789",
}


def _post(payload):
    return client.post("/solicitacao", json=payload)


def test_route_static():
    for path in ("/", "/index.html", "/style.css", "/app.js"):
        assert client.get(path).status_code == 200


@pytest.mark.parametrize("aba", ["alunos", "docentes"])
def test_post_endpoint_exists(aba):
    response = _post({"aba": aba})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")


def test_docentes_missing_optional_ok():
    payload = {k: v for k, v in ALUNOS_FIELDS.items() if k not in ("link", "complemento")}
    payload["aba"] = "docentes"
    payload["tipo_auxilio"] = None
    payload["nivel"] = None
    response = _post(payload)
    assert response.status_code == 200
    oficio = response.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_alunos_empty_required_error():
    response = _post({})
    assert response.status_code == 200
    body = response.json()
    assert "Preencha todos os campos" in body["erros"]
    assert "oficio" not in body


@pytest.mark.parametrize(
    "aba, campo, valor, esperado",
    [
        ("alunos", "nusp", "12a", "N. USP deve conter apenas numeros"),
        ("alunos", "agencia", "12b", "Numero da agencia deve conter apenas numeros"),
        ("alunos", "valor", "0", "Valor solicitado deve ser maior que 0"),
        ("alunos", "email", "sem-arroba", "E-mail invalido"),
        ("alunos", "cpf", "1.234.567-89", "CPF deve estar no formato 000.000.000-00"),
        ("alunos", "cep", "123", "CEP deve estar no formato 00000-000"),
        ("alunos", "data_nascimento", "01021980", "Data de nascimento deve estar no formato dd/mm/aaaa"),
        ("alunos", "cpf", "111.111.111-11", "CPF invalido"),
        ("alunos", "data_nascimento", "30/02/1980", "Data de nascimento invalida"),
    ],
)
def test_single_field_validation(aba, campo, valor, esperado):
    payload = dict(ALUNOS_FIELDS)
    payload["aba"] = aba
    payload[campo] = valor
    response = _post(payload)
    assert response.status_code == 200
    body = response.json()
    assert esperado in body["erros"]


def test_valid_alunos_success():
    payload = dict(ALUNOS_FIELDS)
    payload["valor"] = "150000"
    response = _post(payload)
    assert response.status_code == 200
    body = response.json()
    assert body.get("erros") in (None, [])
    oficio = body["oficio"]
    assert "Fulano de Tal - 1234567" in oficio
    assert "Assunto: Solicitacao de Auxilio Financeiro - Participacao em evento" in oficio
    assert "Programa: Matematica - Mestrado" in oficio
    assert "R$ 1.500,00" in oficio


def test_valid_docentes_success():
    payload = dict(ALUNOS_FIELDS)
    payload["aba"] = "docentes"
    payload["tipo_auxilio"] = None
    payload["nivel"] = None
    response = _post(payload)
    assert response.status_code == 200
    body = response.json()
    assert body.get("erros") in (None, [])
    oficio = body["oficio"]
    assert "Assunto: Solicitacao de Auxilio Financeiro - Verba do programa" in oficio
    assert "Programa: Matematica" in oficio
    assert "Mestrado" not in oficio


def test_oficio_markers_absent():
    response = _post(dict(ALUNOS_FIELDS))
    body = response.json()
    oficio = body["oficio"]
    assert "<<" not in oficio
    assert ">>" not in oficio


EXPECTED_ALUNOS_LINES = [
    "Interessada(o): Fulano de Tal - 1234567",
    "E-mail: fulano@ime.usp.br",
    "Assunto: Solicitacao de Auxilio Financeiro - Participacao em evento",
    "Programa: Matematica - Mestrado",
    "Dados do evento",
    "Evento: Congresso X",
    "Periodo: 01/02/2024 a 03/02/2024",
    "Local: Sao Paulo - SP - Brasil",
    "Link do evento: https://exemplo.com",
    "Apresentacao de trabalho: Poster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Detalhes do pedido",
    "Endereco da(o) interessada(o)",
    "Rua A, 100",
    "CEP: 05508-090",
    "Butanta, Sao Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 11.111.111-1",
    "Banco: Banco do Brasil",
    "Agencia: 1234",
    "Conta: 56789",
    "Encaminhe-se ao Servico Financeiro para providencias.",
]


def test_oficio_structure_and_lines():
    response = _post(dict(ALUNOS_FIELDS))
    body = response.json()
    oficio = body["oficio"]
    assert "A CCP-Matematica aprovou na data de hoje" in oficio
    assert "conforme segue" in oficio
    assert "Complemento:" not in oficio
    for line in EXPECTED_ALUNOS_LINES:
        assert line in oficio
