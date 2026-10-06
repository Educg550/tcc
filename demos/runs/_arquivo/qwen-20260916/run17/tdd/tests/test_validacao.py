"""Testes da validação do backend, campo a campo."""

import json

import pytest

from conftest import alunos_payload, docentes_payload


# CPFs: um válido (118.247.290-36) e um com dígitos verificadores errados
# (123.456.789-09 -> os dois últimos não conferem com os nove primeiros).
CPF_VALIDO = "118.247.290-36"
CPF_FORMATO_ERRADO = "12345678909"
CPF_DIGITOS_ERRADOS = "123.456.789-09"


@pytest.fixture(scope="module")
def input_names(client):
    """Names dos campos que o backend aceita (derivados da primeira resposta)."""
    r = client.post("/api/solicitar", json=alunos_payload(valor="R$ 0,00"))
    assert r.status_code in (200, 422)
    body = r.text
    return {m for m in __import__("re").findall(r'name="([a-z0-9_]+)"', body)}


def post_alunos(client, **over):
    return client.post("/api/solicitar", json=alunos_payload(**over))


def post_docentes(client, **over):
    return client.post("/api/solicitar", json=docentes_payload(**over))


# --------------------------------------------------------------------------- #
# Contrato de resposta em erro
# --------------------------------------------------------------------------- #


def test_resposta_json_em_erro(client):
    r = post_alunos(client, valor="R$ 0,00")
    assert r.status_code in (200, 422)
    assert "application/json" in r.headers.get("content-type", "")


def test_retorna_lista_de_erros(client):
    r = post_alunos(client, valor="R$ 0,00")
    body = r.json()
    assert isinstance(body, dict)
    assert "errors" in body
    assert isinstance(body["errors"], list)


# --------------------------------------------------------------------------- #
# Mensagens exatas de validação
# --------------------------------------------------------------------------- #


def test_campo_obrigatorio_vazio(client):
    body = post_alunos(client, nome="").json()
    assert body["errors"] == ["Preencha todos os campos"]


def test_num_usp_nao_digitos(client):
    body = post_alunos(client, num_usp="123A").json()
    assert "N. USP deve conter apenas números" in body["errors"]


def test_agencia_nao_digitos(client):
    body = post_alunos(client, agencia="12A4").json()
    assert "Número da agência deve conter apenas números" in body["errors"]


def test_valor_nao_maior_que_zero(client):
    body = post_alunos(client, valor="R$ 0,00").json()
    assert "Valor solicitado deve ser maior que 0" in body["errors"]


def test_valor_negativo(client):
    body = post_alunos(client, valor="R$ -15,00").json()
    assert "Valor solicitado deve ser maior que 0" in body["errors"]


def test_email_invalido(client):
    body = post_alunos(client, email="maria@").json()
    assert "E-mail inválido" in body["errors"]


def test_email_sem_arroba(client):
    body = post_alunos(client, email="mariaime.usp.br").json()
    assert "E-mail inválido" in body["errors"]


def test_cpf_formato_errado(client):
    body = post_alunos(client, cpf=CPF_FORMATO_ERRADO).json()
    assert "CPF deve estar no formato 000.000.000-00" in body["errors"]


def test_cep_formato_errado(client):
    body = post_alunos(client, cep="05508090").json()
    assert "CEP deve estar no formato 00000-000" in body["errors"]


def test_data_formato_errado(client):
    body = post_alunos(client, data_nascimento="01-02-1980").json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body["errors"]


def test_cpf_digitos_verificadores_errados(client):
    body = post_alunos(client, cpf=CPF_DIGITOS_ERRADOS).json()
    assert "CPF inválido" in body["errors"]


def test_data_inexistente(client):
    body = post_alunos(client, data_nascimento="29/02/2021").json()
    assert "Data de nascimento inválida" in body["errors"]


def test_data_mes_fora(client):
    body = post_alunos(client, data_nascimento="01/13/1980").json()
    assert "Data de nascimento inválida" in body["errors"]


def test_dia_fora_do_mes(client):
    body = post_alunos(client, data_nascimento="31/02/1980").json()
    assert "Data de nascimento inválida" in body["errors"]


def test_preencher_uma_vez(client):
    body = post_alunos(client, nome="", email="").json()
    assert body["errors"].count("Preencha todos os campos") == 1


def test_mensagens_sao_texto(client):
    body = post_alunos(client, num_usp="A", valor="R$ 0,00", email="x").json()
    assert all(isinstance(e, str) for e in body["errors"])


# --------------------------------------------------------------------------- #
# Validação vale igual nas duas abas
# --------------------------------------------------------------------------- #


def test_validacao_docentes(client):
    body = post_docentes(client, valor="R$ 0,00").json()
    assert "Valor solicitado deve ser maior que 0" in body["errors"]


def test_docentes_sem_erros(client):
    body = post_docentes(client).json()
    assert body.get("errors") == []
