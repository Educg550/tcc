"""Testes do ofício gerado a partir de uma solicitação válida."""

import pytest
from fastapi.testclient import TestClient

from app import app
from tests.test_app import dados_alunos_validos, dados_docentes_validos


@pytest.fixture()
def cliente():
    return TestClient(app)


def linhas_do_oficio(texto):
    return [linha.strip() for linha in texto.splitlines()]


def test_oficio_alunos_cabecalho(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    dados = resposta.json()
    texto = dados.get("oficio", "")
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert (
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    )
    assert "Programa: Matemática - Mestrado" in texto


def test_oficio_alunos_bloco_evento(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    texto = resposta.json()["oficio"]
    assert "Evento: Congresso X" in texto
    assert "Período: 10 a 12 de julho de 2025" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Inscrição" in texto


def test_oficio_alunos_bloco_endereco(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    texto = resposta.json()["oficio"]
    assert "Rua do Matão, 1010" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto


def test_oficio_alunos_bloco_pagamento(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    texto = resposta.json()["oficio"]
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 98765-4" in texto


def test_oficio_sem_link_e_complemento_vazios(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    texto = resposta.json()["oficio"]
    linhas = linhas_do_oficio(texto)
    assert not any("Link do evento:" in linha for linha in linhas if linha == "Link do evento: " or linha.endswith("Link do evento:") and "http" not in linha)
    # Linha do complemento também deve sair quando vazio
    assert "Complemento: " not in texto


def test_oficio_docentes(cliente):
    resposta = cliente.post("/api/validar", json=dados_docentes_validos())
    texto = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática" in texto
    assert "Programa: Matemática -" not in texto


def test_oficio_docentes_nao_tem_tipo_nivel(cliente):
    resposta = cliente.post("/api/validar", json=dados_docentes_validos())
    texto = resposta.json()["oficio"]
    assert "Mestrado" not in texto
    assert "Doutorado" not in texto
    assert "Participação em evento" not in texto


def test_oficio_mantem_quebras_de_linha(cliente):
    resposta = cliente.post("/api/validar", json=dados_alunos_validos())
    texto = resposta.json()["oficio"]
    assert "\n" in texto
    assert "Interessada(o):" in texto
    assert "Dados do evento" in texto
    assert "Endereço da(o) interessada(o)" in texto
    assert "Dados para pagamento" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
