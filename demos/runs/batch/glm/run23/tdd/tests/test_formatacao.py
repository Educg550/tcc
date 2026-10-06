"""Testes da formatação automática dos campos e do endpoint de formatação."""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def cliente():
    return TestClient(app)


@pytest.mark.parametrize(
    "digitado,esperado",
    [
        ("1500", "R$ 15,00"),
        ("150000", "R$ 1.500,00"),
        ("150000000", "R$ 1.500.000,00"),
        ("5", "R$ 0,05"),
    ],
)
def test_formatacao_valor(cliente, digitado, esperado):
    resposta = cliente.post("/api/formata", json={"campo": "valor", "valor": digitado})
    assert resposta.json()["formatado"] == esperado


@pytest.mark.parametrize(
    "digitado,esperado",
    [
        ("12345678909", "123.456.789-09"),
        ("123", "123"),
        ("123456", "123.456"),
        ("123456789", "123.456.789"),
    ],
)
def test_formatacao_cpf(cliente, digitado, esperado):
    resposta = cliente.post("/api/formata", json={"campo": "cpf", "valor": digitado})
    assert resposta.json()["formatado"] == esperado


@pytest.mark.parametrize(
    "digitado,esperado",
    [("05508090", "05508-090"), ("055", "055")],
)
def test_formatacao_cep(cliente, digitado, esperado):
    resposta = cliente.post("/api/formata", json={"campo": "cep", "valor": digitado})
    assert resposta.json()["formatado"] == esperado


@pytest.mark.parametrize(
    "digitado,esperado",
    [
        ("01021980", "01/02/1980"),
        ("01", "01"),
        ("0102", "01/02"),
    ],
)
def test_formatacao_nascimento(cliente, digitado, esperado):
    resposta = cliente.post("/api/formata", json={"campo": "nascimento", "valor": digitado})
    assert resposta.json()["formatado"] == esperado


def test_app_js_contem_formatacao_de_campos():
    from pathlib import Path

    js = (Path(__file__).resolve().parent.parent / "app.js").read_text(encoding="utf-8")
    # o frontend deve chamar o backend para formatar os campos
    assert "/api/formata" in js
    assert "/api/validar" in js
