import re

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALUNOS_FIELDS = {
    "nome_completo": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Ciencia da Computacao",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participacao em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "Congresso de Computacao",
    "periodo_evento": "10/10/2024 a 12/10/2024",
    "cidade_evento": "Sao Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "http://evento.usp.br",
    "valor_solicitado": "150000",
    "detalhamento": "Participacao no evento",
    "apresentacao": "Poster",
    "data_nascimento": "01021980",
    "logradouro": "Rua do Matao",
    "numero": "1010",
    "complemento": "Bloco B",
    "bairro": "Butanta",
    "cep": "05508090",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "12345678909",
    "rg": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "numero_agencia": "1234",
    "numero_conta": "12345-6",
}


# ---------------------------------------------------------------------------
# Pagina inicial
# ---------------------------------------------------------------------------

def test_index_serve_pagina(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_duas_abas_com_rotulos_exatos(client):
    resp = client.get("/")
    html = resp.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_botao_enviar_solicitacao(client):
    resp = client.get("/")
    assert "Enviar solicitação" in resp.text


def test_blocos_titulos_visiveis(client):
    resp = client.get("/")
    html = resp.text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_assets_referenciados(client):
    resp = client.get("/")
    html = resp.text
    assert "assets/usp-logo.png" in html
    assert "style.css" in html
    assert "app.js" in html


def test_estaticos_servidos(client):
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
    logo = client.get("/assets/usp-logo.png")
    assert logo.status_code == 200


def test_nome_universidade_e_programa(client):
    resp = client.get("/")
    html = resp.text
    assert "Universidade de São Paulo" in html


# ---------------------------------------------------------------------------
# Rotulos exatos presentes na pagina
# ---------------------------------------------------------------------------

ROTULOS_OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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
]


@pytest.mark.parametrize("rotulo", ROTULOS_OBRIGATORIOS)
def test_rotulos_exatos(client, rotulo):
    resp = client.get("/")
    assert rotulo in resp.text


# ---------------------------------------------------------------------------
# Endpoint de submissao - validacao
# ---------------------------------------------------------------------------

def _post(client, data):
    return client.post("/solicitacao", json=data)


def test_submissao_alunos_valida(client):
    resp = _post(client, ALUNOS_FIELDS)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("ok") is True
    assert "oficio" in body


def test_oficio_contem_dados(client):
    resp = _post(client, ALUNOS_FIELDS)
    oficio = resp.json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Evento: Congresso de Computacao" in oficio
    assert "R$ 1.500,00" in oficio
    assert "CEP: 05508-090" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio


def test_oficio_quebras_de_linha_mantidas(client):
    resp = _post(client, ALUNOS_FIELDS)
    oficio = resp.json()["oficio"]
    assert "\n" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_docentes_sem_tipo_e_nivel(client):
    data = dict(ALUNOS_FIELDS)
    data.pop("nivel", None)
    data.pop("tipo_auxilio", None)
    data["aba"] = "DOCENTES"
    resp = _post(client, data)
    assert resp.status_code == 200
    oficio = resp.json()["oficio"]
    assert "Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Ciencia da Computacao" in oficio


def test_oficio_omite_link_vazio(client):
    data = dict(ALUNOS_FIELDS)
    data["link_evento"] = ""
    resp = _post(client, data)
    oficio = resp.json()["oficio"]
    assert "Link do evento:" not in oficio


def test_oficio_omite_complemento_vazio(client):
    data = dict(ALUNOS_FIELDS)
    data["complemento"] = ""
    resp = _post(client, data)
    oficio = resp.json()["oficio"]
    assert "Complemento:" not in oficio


def test_erro_campos_obrigatorios_vazios(client):
    data = dict(ALUNOS_FIELDS)
    data["nome_completo"] = ""
    data["email"] = ""
    resp = _post(client, data)
    body = resp.json()
    assert body.get("ok") is not True
    assert "Preencha todos os campos" in body["erros"]
    assert body["erros"].count("Preencha todos os campos") == 1


def test_erro_n_usp_nao_digitos(client):
    data = dict(ALUNOS_FIELDS)
    data["n_usp"] = "12a45678"
    resp = _post(client, data)
    body = resp.json()
    assert "N. USP deve conter apenas números" in body["erros"]


def test_erro_agencia_nao_digitos(client):
    data = dict(ALUNOS_FIELDS)
    data["numero_agencia"] = "12a4"
    resp = _post(client, data)
    body = resp.json()
    assert "Número da agência deve conter apenas números" in body["erros"]


def test_erro_valor_zero(client):
    data = dict(ALUNOS_FIELDS)
    data["valor_solicitado"] = "0"
    resp = _post(client, data)
    body = resp.json()
    assert "Valor solicitado deve ser maior que 0" in body["erros"]


def test_erro_email_invalido(client):
    data = dict(ALUNOS_FIELDS)
    data["email"] = "maria-ime"
    resp = _post(client, data)
    body = resp.json()
    assert "E-mail inválido" in body["erros"]


def test_erro_cpf_formato(client):
    data = dict(ALUNOS_FIELDS)
    data["cpf"] = "12345678909"
    resp = _post(client, data)
    body = resp.json()
    assert "CPF deve estar no formato 000.000.000-00" in body["erros"]


def test_erro_cep_formato(client):
    data = dict(ALUNOS_FIELDS)
    data["cep"] = "05508090"
    resp = _post(client, data)
    body = resp.json()
    assert "CEP deve estar no formato 00000-000" in body["erros"]


def test_erro_data_formato(client):
    data = dict(ALUNOS_FIELDS)
    data["data_nascimento"] = "01021980"
    resp = _post(client, data)
    body = resp.json()
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body["erros"]


def test_erro_cpf_invalido(client):
    data = dict(ALUNOS_FIELDS)
    # CPF com formato correto mas digitos verificadores errados
    data["cpf"] = "111.111.111-11"
    resp = _post(client, data)
    body = resp.json()
    assert "CPF inválido" in body["erros"]


def test_erro_data_invalida(client):
    data = dict(ALUNOS_FIELDS)
    data["data_nascimento"] = "31/02/1980"
    resp = _post(client, data)
    body = resp.json()
    assert "Data de nascimento inválida" in body["erros"]


def test_erro_valor_nao_natural(client):
    data = dict(ALUNOS_FIELDS)
    data["valor_solicitado"] = "abc"
    resp = _post(client, data)
    body = resp.json()
    assert "Valor solicitado deve ser maior que 0" in body["erros"]


def test_multiplos_erros_retornados(client):
    data = dict(ALUNOS_FIELDS)
    data["n_usp"] = "abc"
    data["email"] = "sem-arroba"
    resp = _post(client, data)
    body = resp.json()
    erros = body["erros"]
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros


def test_erro_nao_gera_oficio(client):
    data = dict(ALUNOS_FIELDS)
    data["nome_completo"] = ""
    resp = _post(client, data)
    body = resp.json()
    assert body.get("ok") is not True
    assert "oficio" not in body
