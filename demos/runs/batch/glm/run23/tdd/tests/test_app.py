"""Testes da API FastAPI (app.py)."""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def cliente():
    return TestClient(app)


def dados_alunos_validos():
    return {
        "tipo": "alunos",
        "nome": "Maria da Silva",
        "nusp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso X",
        "periodo": "10 a 12 de julho de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "",
        "valor": "150000",
        "detalhamento": "Inscrição",
        "apresentacao": "Pôster",
        "nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "98765-4",
    }


def dados_docentes_validos():
    dados = dados_alunos_validos()
    dados["tipo"] = "docentes"
    del dados["nivel"]
    del dados["auxilio"]
    return dados


def test_backend_responde_ok(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    assert resposta.status_code == 200


def test_solicitacao_valida_alunos_sem_erros(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    dados = resposta.json()
    assert dados.get("erros") == []


def test_solicitacao_valida_docentes_sem_erros(cliente):
    resposta = cliente.post("/api/validar", json=dados_docentes_validos())
    dados = resposta.json()
    assert dados.get("erros") == []


def test_campos_obrigatorios_vazios(cliente):
    dados = dados_alunos_validos()
    dados["nome"] = ""
    resposta = cliente.post("/api/validar", json=dados)
    assert resposta.json()["erros"] == ["Preencha todos os campos"]


def test_nusp_nao_numerico(cliente):
    dados = dados_alunos_validos()
    dados["nusp"] = "12a34"
    resposta = cliente.post("/api/validar", json=dados)
    assert "N. USP deve conter apenas números" in resposta.json()["erros"]


def test_agencia_nao_numerica(cliente):
    dados = dados_alunos_validos()
    dados["agencia"] = "12-x"
    resposta = cliente.post("/api/validar", json=dados)
    assert (
        "Número da agência deve conter apenas números" in resposta.json()["erros"]
    )


def test_valor_zero_ou_negativo(cliente):
    dados = dados_alunos_validos()
    for valor in ("0", "-1", "a"):
        dados["valor"] = valor
        resposta = cliente.post("/api/validar", json=dados)
        assert "Valor solicitado deve ser maior que 0" in resposta.json()["erros"]


def test_email_invalido(cliente):
    dados = dados_alunos_validos()
    for email in ("sem-arroba", "sem@dominio"):
        dados["email"] = email
        resposta = cliente.post("/api/validar", json=dados)
        assert "E-mail inválido" in resposta.json()["erros"]


def test_cpf_formato_errado(cliente):
    dados = dados_alunos_validos()
    dados["cpf"] = "123"
    resposta = cliente.post("/api/validar", json=dados)
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json()["erros"]


def test_cpf_digitos_verificadores_errados(cliente):
    dados = dados_alunos_validos()
    dados["cpf"] = "12345678910"
    resposta = cliente.post("/api/validar", json=dados)
    assert "CPF inválido" in resposta.json()["erros"]


def test_cep_formato_errado(cliente):
    dados = dados_alunos_validos()
    dados["cep"] = "05508"
    resposta = cliente.post("/api/validar", json=dados)
    assert "CEP deve estar no formato 00000-000" in resposta.json()["erros"]


def test_data_nascimento_formato_errado(cliente):
    dados = dados_alunos_validos()
    dados["nascimento"] = "1980"
    resposta = cliente.post("/api/validar", json=dados)
    assert (
        "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json()["erros"]
    )


def test_data_nascimento_inexistente(cliente):
    dados = dados_alunos_validos()
    dados["nascimento"] = "31021980"
    resposta = cliente.post("/api/validar", json=dados)
    assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_todos_os_erros_aparecem(cliente):
    dados = dados_alunos_validos()
    dados["nusp"] = "abc"
    dados["cpf"] = "123"
    dados["cep"] = "12"
    dados["nascimento"] = "32/13/1980"
    dados["valor"] = "0"
    dados["email"] = "sem-arroba"
    dados["agencia"] = "x"
    dados["nome"] = ""
    resposta = cliente.post("/api/validar", json=dados)
    erros = resposta.json()["erros"]
    assert "Preencha todos os campos" in erros
    assert "N. USP deve conter apenas números" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert "Data de nascimento inválida" in erros
    assert "Valor solicitado deve ser maior que 0" in erros
    assert "E-mail inválido" in erros
    assert "Número da agência deve conter apenas números" in erros
