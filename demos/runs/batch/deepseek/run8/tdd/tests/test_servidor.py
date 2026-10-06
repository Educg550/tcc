from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

PAGINAS = ["/", "/index.html", "/static/index.html"]
ESTILOS = ["/style.css", "/static/style.css", "/css/style.css"]
SCRIPTS = ["/app.js", "/static/app.js", "/js/app.js"]
LOGOS = ["/assets/usp-logo.png", "/static/assets/usp-logo.png"]


def _busca(caminhos, predicado):
    for caminho in caminhos:
        resposta = client.get(caminho)
        if resposta.status_code == 200 and predicado(resposta):
            return resposta
    return None


def test_servidor_entrega_pagina_do_formulario():
    resposta = _busca(PAGINAS, lambda r: "ALUNOS" in r.text and "DOCENTES" in r.text)
    assert resposta is not None, "nenhuma rota entrega a página com as abas"
    assert "text/html" in resposta.headers["content-type"]


def test_servidor_entrega_css_da_identidade():
    resposta = _busca(ESTILOS, lambda r: "#1094ab" in r.text.lower())
    assert resposta is not None, "css da identidade visual não é servido"


def test_servidor_entrega_javascript():
    resposta = _busca(SCRIPTS, lambda r: r.text.strip())
    assert resposta is not None, "app.js não é servido"


def test_servidor_entrega_logotipo():
    resposta = _busca(LOGOS, lambda r: r.content[:8] == b"\x89PNG\r\n\x1a\n")
    assert resposta is not None, "logotipo da USP não é servido"
