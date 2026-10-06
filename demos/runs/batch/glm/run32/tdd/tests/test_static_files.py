"""Testes para os arquivos estáticos do frontend."""
import re


def test_index_html_existe(client):
    resposta = client.get("/")
    assert resposta.status_code == 200


def test_style_css_e_servido_como_texto_css(client):
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    assert "text/css" in resposta.headers["content-type"]


def test_app_js_e_servido_como_javascript(client):
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert "javascript" in resposta.headers["content-type"]


def test_logo_usp_e_servido_como_imagem(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")


def test_index_contem_script_e_stylesheet(client):
    resposta = client.get("/")
    corpo = resposta.text
    assert "style.css" in corpo
    assert "app.js" in corpo
