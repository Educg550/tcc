import re

import pytest
from fastapi.testclient import TestClient

from app import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def alunos_data(overrides=None):
    data = {
        "tipo": "alunos",
        "nome": "Maria da Silva",
        "nusp": "123456",
        "programa": "Matematica",
        "nivel": "Doutorado",
        "tipoAuxilio": "Participacao em evento",
        "email": "maria@ime.usp.br",
        "nomeEvento": "Congresso Internacional de Matematica",
        "periodoEvento": "10 a 14 de novembro de 2025",
        "cidadeEvento": "Sao Paulo",
        "estadoEvento": "SP",
        "paisEvento": "Brasil",
        "linkEvento": "https://exemplo.org/evento",
        "valor": "150000",
        "detalhamento": "Participacao em congresso na area de analise.",
        "apresentacao": "Poster",
        "dataNascimento": "01/02/1980",
        "logradouro": "Rua Exemplo",
        "numero": "123",
        "complemento": "Apto 42",
        "bairro": "Butanta",
        "cep": "05508-090",
        "cidade": "Sao Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "123456789",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "987654321",
    }
    if overrides:
        for key, value in overrides.items():
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
    return data


def test_valid_alunos(client):
    resp = client.post("/solicitar", json=alunos_data())
    assert resp.status_code == 200
    body = resp.json()
    assert body["errors"] == []
    oficio = body["oficio"]
    assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Participa\u00e7\u00e3o em evento" in oficio
    assert "Programa: Matematica - Doutorado" in oficio
    assert "R$ 1.500,00" in oficio
    assert "Link do evento: https://exemplo.org/evento" in oficio
    assert "Complemento: Apto 42" in oficio


def test_invalid_cpf(client):
    resp = client.post("/solicitar", json=alunos_data({"cpf": "000.000.000-00"}))
    body = resp.json()
    assert "CPF inv\u00e1lido" in body["errors"]
    assert "oficio" not in body


def test_invalid_cep_format(client):
    resp = client.post("/solicitar", json=alunos_data({"cep": "05508090"}))
    body = resp.json()
    assert "CEP deve estar no formato 00000-000" in body["errors"]


def test_invalid_data_format(client):
    resp = client.post("/solicitar", json=alunos_data({"dataNascimento": "01021980"}))
    body = resp.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body["errors"]


def test_invalid_data_calendar(client):
    resp = client.post("/solicitar", json=alunos_data({"dataNascimento": "30/02/1980"}))
    body = resp.json()
    assert "Data de nascimento inv\u00e1lida" in body["errors"]


def test_valor_zero(client):
    resp = client.post("/solicitar", json=alunos_data({"valor": "0"}))
    body = resp.json()
    assert "Valor solicitado deve ser maior que 0" in body["errors"]


def test_nusp_nao_digito(client):
    resp = client.post("/solicitar", json=alunos_data({"nusp": "12a3456"}))
    body = resp.json()
    assert "N. USP deve conter apenas n\u00fameros" in body["errors"]


def test_agencia_nao_digito(client):
    resp = client.post("/solicitar", json=alunos_data({"agencia": "123a4"}))
    body = resp.json()
    assert "N\u00famero da ag\u00eancia deve conter apenas n\u00fameros" in body["errors"]


def test_email_invalido(client):
    resp = client.post("/solicitar", json=alunos_data({"email": "sem-at-sign"}))
    body = resp.json()
    assert "E-mail inv\u00e1lido" in body["errors"]


def test_campo_obrigatorio_vazio(client):
    resp = client.post("/solicitar", json=alunos_data({"nome": "   "}))
    body = resp.json()
    assert body["errors"].count("Preencha todos os campos") == 1
    assert "oficio" not in body


def test_docentes_sem_campos_exclusivos(client):
    base = alunos_data()
    base["tipo"] = "docentes"
    base.pop("nivel")
    base.pop("tipoAuxilio")
    resp = client.post("/solicitar", json=base)
    body = resp.json()
    assert body["errors"] == []
    oficio = body["oficio"]
    assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa" in oficio
    assert "Programa: Matematica" in oficio


def test_linha_vazia_removida(client):
    resp = client.post(
        "/solicitar",
        json=alunos_data({"linkEvento": "", "complemento": ""}),
    )
    body = resp.json()
    assert body["errors"] == []
    oficio = body["oficio"]
    assert not re.search(r"^Link do evento:\s*$", oficio, re.M)
    assert not re.search(r"^Complemento:\s*$", oficio, re.M)


def test_assets_servidos(client):
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
