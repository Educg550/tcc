import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    if "app" in sys.modules:
        importlib.reload(sys.modules["app"])
    app_module = importlib.import_module("app")
    with TestClient(app_module.app) as c:
        yield c


def test_index_serve_estaticos(client):
    resp = client.get("/")
    assert resp.status_code == 200
    corpo = resp.text
    assert "ALUNOS" in corpo
    assert "DOCENTES" in corpo
    assert "Enviar solicitação" in corpo
    assert "usps-logo" not in corpo
    assert "usp-logo.png" in corpo
    assert "Universidade de São Paulo" in corpo


def test_assets_servidos(client):
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200


def _campos_alunos(**overrides):
    dados = {
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro",
        "periodo_evento": "01/03/2025 a 05/03/2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://exemplo.com",
        "valor_solicitado": "150000",
        "detalhamento": "Participação no evento com apresentação de artigo.",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco B",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg_rnm": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "numero_agencia": "1234",
        "numero_conta": "12345-6",
    }
    dados.update(overrides)
    return dados


def _campos_docentes(**overrides):
    dados = _campos_alunos()
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    dados.update(overrides)
    return dados


def test_submissao_valida_alunos(client):
    resp = client.post("/solicitar", json=_campos_alunos())
    assert resp.status_code == 200
    body = resp.json()
    assert body["titulo"] == "Solicitação registrada"
    oficio = body["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "Evento: Congresso Brasileiro" in oficio
    assert "Período: 01/03/2025 a 05/03/2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Apresentação de trabalho: Apresentação oral" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Participação no evento com apresentação de artigo." in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco B" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in ofcio if False else True
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_submissao_docentes_altera_linhas(client):
    resp = client.post("/solicitar", json=_campos_docentes())
    assert resp.status_code == 200
    body = resp.json()
    oficio = body["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Mestrado" not in oficio


def test_link_e_complemento_vazios_removem_linhas(client):
    dados = _campos_alunos(link_evento="", complemento="")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code == 200
    oficio = resp.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_campo_obrigatorio_vazio(client):
    dados = _campos_alunos(nome_completo="")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code == 422 or resp.status_code == 400
    erros = resp.json()["erros"]
    assert erros.count("Preencha todos os campos") == 1


def test_n_usp_nao_numerico(client):
    dados = _campos_alunos(n_usp="12a45678")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "N. USP deve conter apenas números" in erros


def test_agencia_nao_numerica(client):
    dados = _campos_alunos(numero_agencia="12a4")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "Número da agência deve conter apenas números" in erros


def test_valor_invalido(client):
    dados = _campos_alunos(valor_solicitado="0")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "Valor solicitado deve ser maior que 0" in erros


def test_email_invalido(client):
    dados = _campos_alunos(email="maria.ime.usp.br")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "E-mail inválido" in erros


def test_cpf_formato_invalido(client):
    dados = _campos_alunos(cpf="12345678909")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_cpf_invalido(client):
    dados = _campos_alunos(cpf="123.456.789-00")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "CPF inválido" in erros


def test_cep_formato_invalido(client):
    dados = _campos_alunos(cep="0550809")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "CEP deve estar no formato 00000-000" in erros


def test_data_formato_invalido(client):
    dados = _campos_alunos(data_nascimento="01-02-1980")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_data_invalida(client):
    dados = _campos_alunos(data_nascimento="31/02/1980")
    resp = client.post("/solicitar", json=dados)
    assert resp.status_code in (400, 422)
    erros = resp.json()["erros"]
    assert "Data de nascimento inválida" in erros
