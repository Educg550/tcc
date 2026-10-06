from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)


def test_css_servido_como_estatico():
    resposta = cliente.get("/style.css")
    assert resposta.status_code == 200
    assert "css" in resposta.headers["content-type"]


def test_js_servido_como_estatico():
    resposta = cliente.get("/app.js")
    assert resposta.status_code == 200
    assert "javascript" in resposta.headers["content-type"]


def test_logo_usp_servido():
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert "png" in resposta.headers["content-type"]


def test_cores_da_universidade_no_css():
    css = cliente.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_fonte_sem_serifa():
    css = cliente.get("/style.css").text.lower()
    assert "sans-serif" in css


def test_sem_recursos_externos():
    for caminho in ("/style.css", "/app.js"):
        texto = cliente.get(caminho).text.lower()
        assert "http://" not in texto
        assert "https://" not in texto
