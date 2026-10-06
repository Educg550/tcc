import pytest
from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


ROTULOS = [
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
]


TITULOS_BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]


def test_pagina_inicial_serve_formulario():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_abas_alunos_e_docentes_na_ordem():
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_rotulos_dos_campos_presentes():
    html = client.get("/").text
    for rotulo in ROTULOS:
        assert rotulo in html, f"rótulo ausente: {rotulo}"


def test_titulos_dos_blocos_presentes():
    html = client.get("/").text
    for titulo in TITULOS_BLOCOS:
        assert titulo in html, f"título ausente: {titulo}"


def test_botao_enviar_solicitacao_presente():
    html = client.get("/").text
    assert "Enviar solicitação" in html


def test_cabecalho_institucional():
    html = client.get("/").text
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_arquivos_estaticos_servidos():
    for caminho in ["/style.css", "/app.js", "/assets/usp-logo.png"]:
        r = client.get(caminho)
        assert r.status_code == 200, caminho


def test_cores_da_universidade_no_css():
    css = client.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_css_e_js_sem_recursos_externos():
    for caminho in ["/style.css", "/app.js"]:
        texto = client.get(caminho).text.lower()
        assert "http://" not in texto
        assert "https://" not in texto


def test_solicitacao_vazia_reporta_campos_obrigatorios():
    r = client.post("/solicitar", json={})
    assert "Preencha todos os campos" in r.text
