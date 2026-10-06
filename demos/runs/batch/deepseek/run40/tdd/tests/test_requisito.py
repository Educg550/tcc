import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_root_serves_index():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_index_contains_tabs():
    resp = client.get("/")
    text = resp.text
    assert "ALUNOS" in text
    assert "DOCENTES" in text
    assert text.index("ALUNOS") < text.index("DOCENTES")


def test_index_contains_block_titles():
    resp = client.get("/")
    text = resp.text
    assert "SOLICITANTE E EVENTO" in text
    assert "ENDEREÇO DO SOLICITANTE" in text
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in text


def test_index_contains_all_labels():
    resp = client.get("/")
    text = resp.text
    labels = [
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
    for label in labels:
        assert label in text, f"Rótulo '{label}' não encontrado"


def test_index_contains_button():
    resp = client.get("/")
    assert "Enviar solicitação" in resp.text


def test_index_references_logo():
    resp = client.get("/")
    assert "assets/usp-logo.png" in resp.text


def test_index_contains_usp_name():
    resp = client.get("/")
    assert "Universidade de São Paulo" in resp.text


def test_css_served_and_contains_colors():
    resp = client.get("/style.css")
    assert resp.status_code == 200
    text = resp.text.lower()
    assert "#1094ab" in text
    assert "#64c4d2" in text
    assert "#fcb421" in text


def test_js_served():
    resp = client.get("/app.js")
    assert resp.status_code == 200


def test_logo_served():
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
    assert "image" in resp.headers["content-type"]


def test_index_has_placeholders():
    resp = client.get("/")
    text = resp.text
    assert "placeholder=" in text


def test_index_contains_select_options():
    resp = client.get("/")
    text = resp.text
    assert "Mestrado" in text
    assert "Doutorado" in text
    assert "Participação em evento" in text
    assert "Banca de exame ou defesa" in text
    assert "Outro" in text
    assert "Pôster" in text
    assert "Apresentação oral" in text
    assert "Outra" in text
    assert "Não irá apresentar trabalho" in text
