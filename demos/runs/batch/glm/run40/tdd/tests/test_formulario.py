import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


CPF_VALIDO = "123.456.789-09"
CEP_VALIDO = "05508-090"
DATA_VALIDA = "01/02/1980"


def dados_alunos():
    return {
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de julho de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com",
        "valor": "1500",
        "detalhamento": "Inscrição e diárias",
        "apresentacao": "Pôster",
        "data_nascimento": DATA_VALIDA,
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": CEP_VALIDO,
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": CPF_VALIDO,
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def test_pagina_carrega():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    for rotulo in ["ALUNOS", "DOCENTES", "Enviar solicitação"]:
        assert rotulo in html


def test_formulario_valido_gera_oficio():
    r = client.post("/solicitacao", data=dados_alunos())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    texto = body["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Matemática - Mestrado" in texto
    assert "Valor solicitado: R$ 15,00" in texto


def test_docentes_nao_tem_nivel():
    r = client.post("/solicitacao", data={**dados_alunos(), "aba": "docentes"})
    assert r.status_code == 200
    texto = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática\n" in texto


def test_campo_obrigatorio_vazio():
    d = dados_alunos()
    d["nome_completo"] = ""
    r = client.post("/solicitacao", data=d)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert "Preencha todos os campos" in body["erros"]


def test_n_usp_digitos():
    d = dados_alunos()
    d["n_usp"] = "abc123"
    r = client.post("/solicitacao", data=d)
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_agencia_digitos():
    d = dados_alunos()
    d["agencia"] = "12a"
    r = client.post("/solicitacao", data=d)
    assert "Número da agência deve conter apenas números" in r.json()["erros"]


def test_valor_invalido():
    d = dados_alunos()
    d["valor"] = "0"
    r = client.post("/solicitacao", data=d)
    assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_email_invalido():
    d = dados_alunos()
    d["email"] = "sem-arroba"
    r = client.post("/solicitacao", data=d)
    assert "E-mail inválido" in r.json()["erros"]


def test_cpf_formato():
    d = dados_alunos()
    d["cpf"] = "1234567890"
    r = client.post("/solicitacao", data=d)
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]


def test_cpf_invalido():
    d = dados_alunos()
    d["cpf"] = "123.456.789-00"
    r = client.post("/solicitacao", data=d)
    assert "CPF inválido" in r.json()["erros"]


def test_cep_formato():
    d = dados_alunos()
    d["cep"] = "0550890"
    r = client.post("/solicitacao", data=d)
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_formato():
    d = dados_alunos()
    d["data_nascimento"] = "01021980"
    r = client.post("/solicitacao", data=d)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]


def test_data_inexistente():
    d = dados_alunos()
    d["data_nascimento"] = "31/02/1980"
    r = client.post("/solicitacao", data=d)
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_todos_os_erros_aparecem():
    d = dados_alunos()
    d["email"] = "x"
    d["cpf"] = "1"
    d["cep"] = "1"
    d["data_nascimento"] = "1"
    r = client.post("/solicitacao", data=d)
    erros = r.json()["erros"]
    assert "E-mail inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros
    assert "CEP deve estar no formato 00000-000" in erros
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_link_e_complemento_opcionais():
    d = dados_alunos()
    d["link"] = ""
    d["complemento"] = ""
    r = client.post("/solicitacao", data=d)
    texto = r.json()["oficio"]
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_formata_valor_grande():
    d = dados_alunos()
    d["valor"] = "150000"
    r = client.post("/solicitacao", data=d)
    assert "R$ 1.500,00" in r.json()["oficio"]
