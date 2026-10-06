import re

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def _form_alunos(**overrides):
    dados = {
        "nome_completo": "Maria Silva Santos",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso Brasileiro",
        "periodo": "10 a 15 de maio de 2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "https://evento.example.com",
        "valor_solicitado": "1500,00",
        "detalhamento": "Passagem aérea e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Bloco A",
        "bairro": "Cidade Universitária",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(overrides)
    return dados


def _form_docentes(**overrides):
    dados = _form_alunos()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados.update(overrides)
    return dados


def _cpf_valido():
    # Gera um CPF com dígitos verificadores válidos.
    base = "123456789"
    def dv(nums):
        soma = sum(int(n) * (len(nums) + 1 - i) for i, n in enumerate(nums))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto
    d1 = dv(base)
    d2 = dv(base + str(d1))
    return f"{base[:3]}.{base[3:6]}.{base[6:]}-{d1}{d2}"


# --- Tela / abas ---

def test_pagina_tem_abas_alunos_e_docentes_nessa_ordem(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_aba_alunos_ativa_ao_abrir(client):
    html = client.get("/").text
    assert re.search(r'class="[^"]*aba[^"]*ativa[^"]*"', html) or \
        re.search(r'class="[^"]*ativa[^"]*"', html)


def test_formularios_tem_botao_enviar(client):
    html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


# --- Cabeçalho institucional ---

def test_cabecalho_institucional(client):
    html = client.get("/").text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html


# --- Aparência / cores ---

def test_css_usa_cores_da_universidade(client):
    css = client.get("/style.css")
    assert css.status_code == 200
    assert "#1094ab" in css.text.lower()
    assert "#64c4d2" in css.text.lower()
    assert "#fcb421" in css.text.lower()


def test_css_sem_fonte_remota(client):
    css = client.get("/style.css").text.lower()
    assert "@import" not in css
    assert "fonts.googleapis" not in css


# --- Validação: campos obrigatórios ---

def test_campo_obrigatorio_vazio_mostra_uma_msg(client):
    dados = _form_alunos()
    dados["nome_completo"] = ""
    r = client.post("/solicitacao", data=dados)
    assert "Preencha todos os campos" in r.text
    assert r.text.count("Preencha todos os campos") == 1


def test_multiplos_campos_vazios_mostram_uma_msg(client):
    dados = _form_alunos()
    dados["nome_completo"] = ""
    dados["programa"] = ""
    r = client.post("/solicitacao", data=dados)
    assert r.text.count("Preencha todos os campos") == 1


def test_n_usp_nao_digitos(client):
    r = client.post("/solicitacao", data=_form_alunos(n_usp="12a456"))
    assert "N. USP deve conter apenas números" in r.text


def test_agencia_nao_digitos(client):
    r = client.post("/solicitacao", data=_form_alunos(agencia="12a4"))
    assert "Número da agência deve conter apenas números" in r.text


def test_valor_solicitado_invalido(client):
    r = client.post("/solicitacao", data=_form_alunos(valor_solicitado="0,00"))
    assert "Valor solicitado deve ser maior que 0" in r.text


def test_email_invalido(client):
    r = client.post("/solicitacao", data=_form_alunos(email="mariasemarroba"))
    assert "E-mail inválido" in r.text


def test_cpf_formato_invalido(client):
    r = client.post("/solicitacao", data=_form_alunos(cpf="12345678909"))
    assert "CPF deve estar no formato 000.000.000-00" in r.text


def test_cep_formato_invalido(client):
    r = client.post("/solicitacao", data=_form_alunos(cep="05508090"))
    assert "CEP deve estar no formato 00000-000" in r.text


def test_data_nascimento_formato_invalido(client):
    r = client.post("/solicitacao", data=_form_alunos(data_nascimento="1980-02-01"))
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.text


def test_cpf_invalido(client):
    r = client.post("/solicitacao", data=_form_alunos(cpf="123.456.789-00"))
    assert "CPF inválido" in r.text


def test_data_nascimento_inexistente(client):
    r = client.post("/solicitacao", data=_form_alunos(data_nascimento="31/02/1980"))
    assert "Data de nascimento inválida" in r.text
    r2 = client.post("/solicitacao", data=_form_alunos(data_nascimento="01/13/1980"))
    assert "Data de nascimento inválida" in r2.text


# --- Ofício de ALUNOS ---

def test_oficio_alunos_tem_marcadores_preenchidos(client):
    dados = _form_alunos(cpf=_cpf_valido())
    r = client.post("/solicitacao", data=dados)
    assert r.status_code == 200
    texto = r.text
    assert "Solicitação registrada" in texto
    assert "Interessada(o): Maria Silva Santos - 12345678" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Evento: Congresso Brasileiro" in texto
    assert "Local: São Paulo - SP - Brasil" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "CPF: " + _cpf_valido() in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_docentes_assunto_e_programa(client):
    dados = _form_docentes(cpf=_cpf_valido())
    r = client.post("/solicitacao", data=dados)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in r.text
    # Programa sem nível
    assert "Programa: Ciência da Computação" in r.text


def test_link_vazio_sai_do_oficio(client):
    dados = _form_alunos(cpf=_cpf_valido(), link_evento="")
    r = client.post("/solicitacao", data=dados)
    assert "Link do evento:" not in r.text


def test_complemento_vazio_sai_do_oficio(client):
    dados = _form_alunos(cpf=_cpf_valido(), complemento="")
    r = client.post("/solicitacao", data=dados)
    assert "Complemento:" not in r.text


def test_cabecalho_institucional_na_confirmacao(client):
    dados = _form_alunos(cpf=_cpf_valido())
    r = client.post("/solicitacao", data=dados)
    assert "usp-logo.png" in r.text
    assert "Universidade de São Paulo" in r.text


def test_erro_nao_gera_oficio(client):
    dados = _form_alunos(cpf=_cpf_valido(), email="invalido")
    r = client.post("/solicitacao", data=dados)
    assert "Interessada(o):" not in r.text


# --- Estáticos ---

def test_staticos_servidos(client):
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
