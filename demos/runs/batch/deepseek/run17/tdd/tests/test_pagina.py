from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_pagina_inicial_e_servida_como_html():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_pagina_tem_as_duas_abas_na_ordem_alunos_docentes():
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cabecalho_traz_a_identidade_da_universidade():
    html = client.get("/").text
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_arquivos_estaticos_de_estilo_e_comportamento():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_logotipo_da_usp_e_servido_de_assets():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_campos_tem_placeholder_visivel():
    html = client.get("/").text
    assert "placeholder=" in html
