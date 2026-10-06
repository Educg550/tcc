"""Testes do ofício gerado após envio válido."""

import pytest

from conftest import alunos_payload, docentes_payload


# CPF válido (dígitos verificadores conferem): 118.247.290-36


def post_ok(client, aba):
    payload = alunos_payload(cpf="118.247.290-36") if aba == "alunos" else docentes_payload(cpf="118.247.290-36")
    return client.post("/api/solicitar", json=payload).json()


def test_oficio_alunos_preserva_marca_dagua(client):
    o = post_ok(client, "alunos")["oficio"]
    assert "Interessada(o):" in o
    assert "A CCP-" in o
    assert "Encaminhe-se ao Serviço Financeiro para providências." in o


def test_oficio_alunos_linhas_exatas(client):
    o = post_ok(client, "alunos")["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in o
    assert "Programa: Ciência da Computação - Mestrado" in o
    assert "E-mail: maria@ime.usp.br" in o
    assert "Data de nascimento: 01/02/1980" in o
    assert "CPF: 118.247.290-36" in o


def test_valor_formatado_no_oficio(client):
    o = post_ok(client, "alunos")["oficio"]
    assert "Valor solicitado: R$ 15,00" in o


def test_link_no_oficio(client):
    o = post_ok(client, "alunos")["oficio"]
    assert "Link do evento: https://exemplo.com/evento" in o


def test_link_vazio_remove_linha(client):
    o = post_ok(client, "alunos")["oficio"]
    assert "Link do evento:" in o
    body = client.post("/api/solicitar", json=alunos_payload(cpf="118.247.290-36", link_evento="")).json()
    assert "Link do evento:" not in body["oficio"]


def test_complemento_vazio_remove_linha(client):
    body = client.post("/api/solicitar", json=alunos_payload(cpf="118.247.290-36", complemento="")).json()
    assert "Complemento:" not in body["oficio"]


def test_oficio_docentes_assunto(client):
    o = post_ok(client, "docentes")["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in o


def test_oficio_docentes_programa_sem_nivel(client):
    o = post_ok(client, "docentes")["oficio"]
    assert "Programa: Ciência da Computação" in o
    assert " - Mestrado" not in o


def test_sem_erros_nao_gera_oficio(client):
    body = client.post("/api/solicitar", json=alunos_payload(nome="")).json()
    assert body.get("oficio") in (None, "")
    assert body["errors"]
