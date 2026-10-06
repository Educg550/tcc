import re

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def base_aluno(**over):
    dados = {
        "nome": "Fulano de Tal",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "fulano@usp.br",
        "evento": "Congresso de Teste",
        "periodo": "10 a 12 de janeiro",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "http://evento.test",
        "valor": "R$ 15,00",
        "detalhamento": "Viagem para apresentar trabalho.",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Av. Teste",
        "numero": "100",
        "complemento": "",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade_sol": "São Paulo",
        "estado_sol": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(over)
    return dados


def base_docente(**over):
    dados = base_aluno()
    for k in ("nivel", "tipo_auxilio"):
        dados.pop(k, None)
    dados.update(over)
    return dados


def test_frontend_index_servido(client):
    r = client.get("/")
    assert r.status_code == 200
    corpo = r.text
    assert "ALUNOS" in corpo
    assert "DOCENTES" in corpo
    assert "Universidade de São Paulo" in corpo


def test_assets_estaticos(client):
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200


def test_submit_valido_retorna_oficio_aluno(client):
    r = client.post("/solicitacao", json=base_aluno())
    assert r.status_code == 200
    oficio = r.json().get("oficio", r.text)
    assert "Fulano de Tal" in oficio
    assert "12345678" in oficio
    assert "fulano@usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "R$ 15,00" in oficio
    assert "Interessada(o):" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_submit_valido_oficio_docente_sem_nivel_tipo(client):
    r = client.post("/solicitacao", json={**base_docente(), "aba": "docentes"})
    assert r.status_code == 200
    oficio = r.json().get("oficio", r.text)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert "Mestrado" not in oficio
    assert "Participação em evento" not in oficio


def test_link_vazio_nao_aparece(client):
    r = client.post("/solicitacao", json=base_aluno(link=""))
    oficio = r.json().get("oficio", r.text)
    assert "Link do evento:" not in oficio


def test_complemento_vazio_nao_aparece(client):
    r = client.post("/solicitacao", json=base_aluno(complemento=""))
    oficio = r.json().get("oficio", r.text)
    assert "Complemento:" not in oficio


def test_erro_campo_obrigatorio(client):
    r = client.post("/solicitacao", json=base_aluno(nome=""))
    assert r.status_code >= 400
    corpo = r.json()
    assert "Preencha todos os campos" in corpo.get("erros", [])


def test_erro_n_usp_nao_numerico(client):
    r = client.post("/solicitacao", json=base_aluno(n_usp="12a45"))
    corpo = r.json()
    assert "N. USP deve conter apenas números" in corpo.get("erros", [])


def test_erro_agencia_nao_numerica(client):
    r = client.post("/solicitacao", json=base_aluno(agencia="12a4"))
    corpo = r.json()
    assert "Número da agência deve conter apenas números" in corpo.get("erros", [])


def test_erro_valor_zero(client):
    r = client.post("/solicitacao", json=base_aluno(valor="R$ 0,00"))
    corpo = r.json()
    assert "Valor solicitado deve ser maior que 0" in corpo.get("erros", [])


def test_erro_email(client):
    r = client.post("/solicitacao", json=base_aluno(email="fulano"))
    corpo = r.json()
    assert "E-mail inválido" in corpo.get("erros", [])


def test_erro_cpf_formato(client):
    r = client.post("/solicitacao", json=base_aluno(cpf="12345678909"))
    corpo = r.json()
    assert "CPF deve estar no formato 000.000.000-00" in corpo.get("erros", [])


def test_erro_cpf_invalido(client):
    r = client.post("/solicitacao", json=base_aluno(cpf="111.111.111-11"))
    corpo = r.json()
    assert "CPF inválido" in corpo.get("erros", [])


def test_erro_cep_formato(client):
    r = client.post("/solicitacao", json=base_aluno(cep="05508090"))
    corpo = r.json()
    assert "CEP deve estar no formato 00000-000" in corpo.get("erros", [])


def test_erro_data_formato(client):
    r = client.post("/solicitacao", json=base_aluno(data_nascimento="01021980"))
    corpo = r.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in corpo.get("erros", [])


def test_erro_data_invalida(client):
    r = client.post("/solicitacao", json=base_aluno(data_nascimento="31/02/1980"))
    corpo = r.json()
    assert "Data de nascimento inválida" in corpo.get("erros", [])


def test_multiplos_erros_retornados(client):
    r = client.post("/solicitacao", json=base_aluno(nome="", n_usp="12a45", agencia="x"))
    corpo = r.json()
    erros = corpo.get("erros", [])
    assert "Preencha todos os campos" in erros
    assert "N. USP deve conter apenas números" in erros
    assert "Número da agência deve conter apenas números" in erros


def test_index_js_formata_valor(cliente_js):
    assert re.search(r"R\$\s*1\.500,00", cliente_js("150000"))
