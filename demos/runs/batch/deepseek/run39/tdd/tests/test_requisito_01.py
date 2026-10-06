import re

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


DADOS = {
    "nome": "Fulano da Silva",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "fulano@usp.br",
    "evento": "Congresso Brasileiro de Computação",
    "periodo": "10/05/2024 a 12/05/2024",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://exemplo.com/evento",
    "valor": "150000",
    "detalhamento": "Participação no evento conforme programa.",
    "apresentacao": "Pôster",
    "data_nascimento": "01021980",
    "logradouro": "Rua do IME",
    "numero": "1010",
    "complemento": "Sala 200",
    "bairro": "Butantã",
    "cep": "05508090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "12345678909",
    "rg_rnm": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


def test_formulario_tem_abas_alunos_e_docentes():
    resposta = client.get("/")
    assert resposta.status_code == 200
    texto = resposta.text
    assert "ALUNOS" in texto
    assert "DOCENTES" in texto


def test_aba_alunos_atenta_ao_formato_do_oficio():
    dados = dict(DADOS)
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    for esperado in [
        "Interessada(o): Fulano da Silva - 12345678",
        "E-mail: fulano@usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Mestrado",
        "Evento: Congresso Brasileiro de Computação",
        "Período: 10/05/2024 a 12/05/2024",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com/evento",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Participação no evento conforme programa.",
        "Rua do IME, 1010",
        "Complemento: Sala 200",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
    ]:
        assert esperado in oficio, esperado


def test_oficio_docente_tem_assunto_verba_do_programa():
    dados = dict(DADOS)
    dados.pop("nivel", None)
    dados.pop("tipo_auxilio", None)
    resposta = client.post("/solicitacao/docentes", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciência da Computação" in oficio
    assert " - Mestrado" not in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" not in oficio


def test_campo_obrigatorio_vazio_retorna_mensagem():
    dados = dict(DADOS)
    dados["nome"] = ""
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    mensagens = resposta.json()["erros"]
    assert mensagens.count("Preencha todos os campos") == 1


def test_n_usp_apenas_digitos():
    dados = dict(DADOS)
    dados["n_usp"] = "12abc"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "N. USP deve conter apenas números" in resposta.json()["erros"]


def test_agencia_apenas_digitos():
    dados = dict(DADOS)
    dados["agencia"] = "12a4"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Número da agência deve conter apenas números" in resposta.json()["erros"]


def test_valor_precisa_ser_maior_que_zero():
    dados = dict(DADOS)
    dados["valor"] = "0"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Valor solicitado deve ser maior que 0" in resposta.json()["erros"]


def test_email_precisa_ser_valido():
    dados = dict(DADOS)
    dados["email"] = "fulano"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "E-mail inválido" in resposta.json()["erros"]


def test_cpf_formato_invalido():
    dados = dict(DADOS)
    dados["cpf"] = "123456789"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "CPF deve estar no formato 000.000.000-00" in resposta.json()["erros"]


def test_cep_formato_invalido():
    dados = dict(DADOS)
    dados["cep"] = "0550809"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "CEP deve estar no formato 00000-000" in resposta.json()["erros"]


def test_data_nascimento_formato_invalido():
    dados = dict(DADOS)
    dados["data_nascimento"] = "01-02-1980"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resposta.json()["erros"]


def test_cpf_digitos_verificadores_invalidos():
    dados = dict(DADOS)
    dados["cpf"] = "123.456.789-08"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "CPF inválido" in resposta.json()["erros"]


def test_data_nascimento_inexistente():
    dados = dict(DADOS)
    dados["data_nascimento"] = "31/02/1980"
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 400
    assert "Data de nascimento inválida" in resposta.json()["erros"]


def test_oferta_de_banca_e_apresentacao_selecionaveis():
    resposta = client.get("/")
    assert "Participação em evento" in resposta.text
    assert "Banca de exame ou defesa" in resposta.text
    assert "Outro" in resposta.text
    assert "Pôster" in resposta.text
    assert "Apresentação oral" in resposta.text
    assert "Outra" in resposta.text
    assert "Não irá apresentar trabalho" in resposta.text


def test_link_e_complemento_ausentes_saem_do_oficio():
    dados = dict(DADOS)
    dados["link_evento"] = ""
    dados["complemento"] = ""
    resposta = client.post("/solicitacao/alunos", json=dados)
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_placeholder_do_valor_é_exemplo():
    resposta = client.get("/")
    assert re.search(r'placeholder="[^"]+"', resposta.text)


def test_index_serve_assets_estaticos():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200


def test_menu_de_abas_nao_recarrega_pagina():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "app.js" in resposta.text
    assert "style.css" in resposta.text
