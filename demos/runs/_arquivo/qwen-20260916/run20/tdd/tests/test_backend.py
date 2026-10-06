import re

import pytest


VALID_ALUNOS = {
    "tipo": "alunos",
    "nome": "Maria Silva Santos",
    "numusp": "1234567",
    "programa": "Matematica",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participacao em evento",
    "email": "maria@ime.usp.br",
    "evento": "Congresso",
    "periodo": "01/01/2024 a 05/01/2024",
    "cidade_evento": "Sao Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://exemplo.com",
    "valor": 150000,
    "detalhamento": "Detalhe completo",
    "apresentacao": "Poster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua A",
    "numero": "100",
    "complemento": "Apto 1",
    "bairro": "Butanta",
    "cep": "05508-090",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

VALID_DOCENTES = {
    "tipo": "docentes",
    "nome": "Joao Pereira Lima",
    "numusp": "7654321",
    "programa": "Estatistica",
    "email": "joao@ime.usp.br",
    "evento": "Seminar",
    "periodo": "01/01/2024",
    "cidade_evento": "Campinas",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://exemplo.com",
    "valor": 2500,
    "detalhamento": "Resumo do pedido",
    "apresentacao": "Nao ira apresentar trabalho",
    "data_nascimento": "15/06/1975",
    "logradouro": "Rua B",
    "numero": "200",
    "complemento": "",
    "bairro": "Centro",
    "cep": "01001-000",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "111.444.777-35",
    "rg": "5.678.901-2",
    "banco": "Caixa",
    "agencia": "0001",
    "conta": "98765-1",
}


def test_existe_rota_de_solicitacao(client):
    r = client.post("/solicitar", json=dict(VALID_ALUNOS))
    assert r.status_code == 200
    assert r.json().get("sucesso") is True


def test_oficio_alunos(client):
    r = client.post("/solicitar", json=dict(VALID_ALUNOS))
    body = r.json()
    assert body["sucesso"] is True
    doc = body["oficio"]
    assert "Maria Silva Santos - 1234567" in doc
    assert "E-mail: maria@ime.usp.br" in doc
    assert "Assunto: Solicitacao de Auxilio Financeiro" in doc
    assert "Participacao em evento" in doc
    assert "Matematica" in doc
    assert "Congresso" in doc
    assert "R$ 1.500,00" in doc
    assert "Poster" in doc
    assert "123.456.789-09" in doc


def test_oficio_docentes(client):
    r = client.post("/solicitar", json=dict(VALID_DOCENTES))
    body = r.json()
    assert body["sucesso"] is True
    doc = body["oficio"]
    assert "Joao Pereira Lima - 7654321" in doc
    assert "Verba do programa" in doc
    assert "Programa: Estatistica" in doc
    assert "Estatistica -" not in doc
    assert "R$ 25,00" in doc
    assert "Complemento" not in doc


def test_erro_campo_obrigatorio_vazio(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "nome": ""}))
    body = r.json()
    assert body["sucesso"] is False
    assert "Preencha todos os campos" in body["erros"]


def test_erro_numusp_nao_numeric(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "numusp": "12a3"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "N. USP deve conter apenas numeros" in body["erros"]


def test_erro_agencia_nao_numeric(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "agencia": "1a34"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "Numero da agencia deve conter apenas numeros" in body["erros"]


def test_erro_valor_zero(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "valor": 0}))
    body = r.json()
    assert body["sucesso"] is False
    assert "Valor solicitado deve ser maior que 0" in body["erros"]


def test_erro_valor_negativo(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "valor": -100}))
    body = r.json()
    assert body["sucesso"] is False
    assert "Valor solicitado deve ser maior que 0" in body["erros"]


def test_erro_email_sem_arroba(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "email": "x"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "E-mail invalido" in body["erros"]


def test_erro_email_sem_dominio(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "email": "x@"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "E-mail invalido" in body["erros"]


def test_erro_cpf_formato(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "cpf": "12345678909"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "CPF deve estar no formato 000.000.000-00" in body["erros"]


def test_erro_cep_formato(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "cep": "05508090"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "CEP deve estar no formato 00000-000" in body["erros"]


def test_erro_data_formato(client):
    r = client.post(
        "/solicitar", json=dict({**VALID_ALUNOS, "data_nascimento": "1980-02-01"})
    )
    body = r.json()
    assert body["sucesso"] is False
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body["erros"]


def test_erro_cpf_digitos_verificadores(client):
    r = client.post("/solicitar", json=dict({**VALID_ALUNOS, "cpf": "123.456.789-00"}))
    body = r.json()
    assert body["sucesso"] is False
    assert "CPF invalido" in body["erros"]


def test_erro_data_inexistente(client):
    r = client.post(
        "/solicitar", json=dict({**VALID_ALUNOS, "data_nascimento": "31/02/1980"})
    )
    body = r.json()
    assert body["sucesso"] is False
    assert "Data de nascimento invalida" in body["erros"]


def test_erro_mes_invalido(client):
    r = client.post(
        "/solicitar", json=dict({**VALID_ALUNOS, "data_nascimento": "13/13/1980"})
    )
    body = r.json()
    assert body["sucesso"] is False
    assert "Data de nascimento invalida" in body["erros"]


def test_erro_multiplos(client):
    r = client.post(
        "/solicitar",
        json=dict({**VALID_ALUNOS, "numusp": "1a3", "cep": "bad", "valor": 0}),
    )
    body = r.json()
    assert body["sucesso"] is False
    erros = body["erros"]
    assert "N. USP deve conter apenas numeros" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert "Valor solicitado deve ser maior que 0" in erros
    assert len(erros) == len(set(erros))


def test_nao_ha_persistencia(client):
    client.post("/solicitar", json=dict(VALID_ALUNOS))
    client.post("/solicitar", json=dict(VALID_DOCENTES))
    r = client.get("/solicitar")
    assert r.status_code not in (200, 201, 204)
