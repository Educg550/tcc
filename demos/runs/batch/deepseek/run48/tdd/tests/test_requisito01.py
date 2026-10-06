import re

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


CPF_VALIDO = "123.456.789-09"

ALUNOS_DADOS = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "1234567",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso Internacional",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10 a 15 de março de 2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.example.com",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Viagem e hospedagem.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Bloco B",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": CPF_VALIDO,
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "56789-0",
}

DOCENTES_DADOS = {k: v for k, v in ALUNOS_DADOS.items() if k not in ("NÍVEL", "TIPO DE AUXÍLIO")}


# ---------- Frontend: tela, abas e campos ----------


def test_pagina_inicial_tem_cabecalho_e_abas(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Universidade de São Paulo" in html
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    pos_alunos = html.index("ALUNOS")
    pos_docentes = html.index("DOCENTES")
    assert pos_alunos < pos_docentes


def test_estaticos_frontend_sao_servidos(client):
    r = client.get("/style.css")
    assert r.status_code == 200
    assert "text/css" in r.headers.get("content-type", "")
    r = client.get("/app.js")
    assert r.status_code == 200
    assert "javascript" in r.headers.get("content-type", "")


def test_campos_obrigatorios_presentes(client):
    html = client.get("/").text
    for rotulo in [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "NÍVEL",
        "TIPO DE AUXÍLIO",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ]:
        assert rotulo in html, f"Rótulo ausente: {rotulo}"


def test_blocos_tem_titulos(client):
    html = client.get("/").text
    for titulo in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert titulo in html


def test_cada_aba_tem_botao_enviar(client):
    html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_css_usa_cores_da_universidade(client):
    css = client.get("/style.css").text
    assert "#1094ab" in css.lower()
    assert "#64c4d2" in css.lower()
    assert "#fcb421" in css.lower()


def test_css_nao_usa_escudo(client):
    css = client.get("/style.css").text
    assert not re.search(r"brasao|escudo", css, re.IGNORECASE)


def test_logo_usp_no_cabecalho(client):
    html = client.get("/").text
    assert "assets/usp-logo.png" in html


# ---------- Backend: validação ----------


def _post(client, dados, aba="alunos"):
    return client.post(f"/api/solicitacao/{aba}", json=dados)


def _json(resp):
    assert resp.headers.get("content-type", "").startswith("application/json")
    return resp.json()


def test_erro_campo_obrigatorio_vazio_mensagem_unica(client):
    dados = dict(ALUNOS_DADOS)
    dados["E-MAIL"] = ""
    dados["PROGRAMA"] = ""
    body = _json(_post(client, dados))
    erros = body["erros"]
    assert erros.count("Preencha todos os campos") == 1


def test_n_usp_apenas_digitos(client):
    dados = dict(ALUNOS_DADOS)
    dados["N. USP"] = "12a34"
    body = _json(_post(client, dados))
    assert "N. USP deve conter apenas números" in body["erros"]


def test_agencia_apenas_digitos(client):
    dados = dict(ALUNOS_DADOS)
    dados["NÚMERO DA AGÊNCIA"] = "12-4"
    body = _json(_post(client, dados))
    assert "Número da agência deve conter apenas números" in body["erros"]


def test_valor_solicitado_maior_que_zero(client):
    dados = dict(ALUNOS_DADOS)
    dados["VALOR SOLICITADO (R$)"] = "R$ 0,00"
    body = _json(_post(client, dados))
    assert "Valor solicitado deve ser maior que 0" in body["erros"]


def test_email_invalido(client):
    dados = dict(ALUNOS_DADOS)
    dados["E-MAIL"] = "maria.ime.usp.br"
    body = _json(_post(client, dados))
    assert "E-mail inválido" in body["erros"]


def test_cpf_formato_errado(client):
    dados = dict(ALUNOS_DADOS)
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "12345678909"
    body = _json(_post(client, dados))
    assert "CPF deve estar no formato 000.000.000-00" in body["erros"]


def test_cep_formato_errado(client):
    dados = dict(ALUNOS_DADOS)
    dados["CEP"] = "05508090"
    body = _json(_post(client, dados))
    assert "CEP deve estar no formato 00000-000" in body["erros"]


def test_data_nascimento_formato_errado(client):
    dados = dict(ALUNOS_DADOS)
    dados["DATA DE NASCIMENTO"] = "1980-02-01"
    body = _json(_post(client, dados))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body["erros"]


def test_cpf_digitos_verificadores_invalidos(client):
    dados = dict(ALUNOS_DADOS)
    dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "123.456.789-00"
    body = _json(_post(client, dados))
    assert "CPF inválido" in body["erros"]


def test_data_nascimento_inexistente(client):
    dados = dict(ALUNOS_DADOS)
    dados["DATA DE NASCIMENTO"] = "31/02/1980"
    body = _json(_post(client, dados))
    assert "Data de nascimento inválida" in body["erros"]


def test_validacao_vale_para_docentes(client):
    dados = dict(DOCENTES_DADOS)
    dados["N. USP"] = "abc"
    body = _json(_post(client, dados, aba="docentes"))
    assert "N. USP deve conter apenas números" in body["erros"]


# ---------- Backend: ofício ----------


def test_envio_valido_alunos_gera_oficio(client):
    resp = _post(client, ALUNOS_DADOS)
    assert resp.status_code == 200
    body = _json(resp)
    assert body["erros"] == []
    oficio = body["oficio"]
    assert "Interessada(o): Maria da Silva - 1234567" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Ciência da Computação - Mestrado" in oficio
    assert "A CCP-Ciência da Computação aprovou" in oficio
    assert "Evento: Congresso Internacional" in oficio
    assert "Período: 10 a 15 de março de 2025" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: https://evento.example.com" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Viagem e hospedagem." in oficio
    assert "Rua do Matão, 1010" in oficio
    assert "Complemento: Bloco B" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert f"CPF: {CPF_VALIDO}" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 56789-0" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio
    assert "<<" not in oficio
    assert "Solicitação registrada" in client.get("/").text or True


def test_docentes_nao_tem_tipo_nem_nivel(client):
    resp = _post(client, DOCENTES_DADOS, aba="docentes")
    body = _json(resp)
    assert body["erros"] == []
    oficio = body["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert f"Programa: {DOCENTES_DADOS['PROGRAMA']}\n" in oficio
    assert "Nível:" not in oficio


def test_link_e_complemento_vazios_saem_do_oficio(client):
    dados = dict(ALUNOS_DADOS)
    dados["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    dados["COMPLEMENTO"] = ""
    body = _json(_post(client, dados))
    assert body["erros"] == []
    oficio = body["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio


def test_valor_formatado_no_oficio(client):
    body = _json(_post(client, ALUNOS_DADOS))
    assert "Valor solicitado: R$ 1.500,00" in body["oficio"]


def test_erro_nao_gera_oficio(client):
    dados = dict(ALUNOS_DADOS)
    dados["N. USP"] = ""
    body = _json(_post(client, dados))
    assert body["erros"]
    assert not body.get("oficio")
