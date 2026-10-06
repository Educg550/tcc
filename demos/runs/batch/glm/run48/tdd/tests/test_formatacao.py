import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)


def test_formatacao_moeda_brasileira(client):
    r = client.post("/formatacao/valor", json={"digitos": "150000000"})
    assert r.status_code == 200
    assert r.json()["valor"] == "R$ 1.500.000,00"


def test_formatacao_moeda_valor_pequeno(client):
    r = client.post("/formatacao/valor", json={"digitos": "1500"})
    assert r.json()["valor"] == "R$ 15,00"


def test_formatacao_cpf(client):
    r = client.post("/formatacao/cpf", json={"digitos": "12345678909"})
    assert r.json()["cpf"] == "123.456.789-09"


def test_formatacao_cep(client):
    r = client.post("/formatacao/cep", json={"digitos": "05508090"})
    assert r.json()["cep"] == "05508-090"


def test_formatacao_data(client):
    r = client.post("/formatacao/data", json={"digitos": "01021980"})
    assert r.json()["data"] == "01/02/1980"
