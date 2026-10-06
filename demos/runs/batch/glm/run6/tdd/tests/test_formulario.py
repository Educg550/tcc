"""Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re

from fastapi.testclient import TestClient

from app import app


DADOS_ALUNOS = {
    "nome_completo": "Maria da Silva",
    "n_usp": "1234567",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "Congresso de Matemática",
    "periodo": "10 a 12 de julho",
    "cidade": "São Paulo",
    "estado": "SP",
    "pais": "Brasil",
    "link": "https://exemplo.com",
    "valor": "150000",
    "detalhamento": "Passagem e hospedagem",
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
    "conta": "56789-0",
}


def client():
    return TestClient(app)


def test_pagina_carrega_com_abas():
    resposta = client().get("/")
    assert resposta.status_code == 200


def test_arquivos_estaticos_existem():
    for caminho in ("/style.css", "/app.js", "/assets/usp-logo.png"):
        resposta = client().get(caminho)
        assert resposta.status_code == 200


def test_titulo_e_cabecalho_na_pagina():
    resposta = client().get("/")
    assert "Universidade de São Paulo" in resposta.text


def test_formulario_alunos_deve_validar_campos_obrigatorios():
    resposta = client().post("/api/validar", json={"aba": "alunos", "dados": {}})
    dados = resposta.json()
    assert dados["valido"] is False
    assert "Preencha todos os campos" in dados["erros"]
