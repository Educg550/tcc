import re
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_index_serve_pagina():
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")


def test_assets_servidos():
    assert client.get("/assets/usp-logo.png").status_code == 200


def test_headers_cacheados():
    for path in ("/", "/style.css", "/app.js", "/assets/usp-logo.png"):
        h = client.get(path).headers
        assert h.get("cache-control") == "public, max-age=31536000"


def test_pagina_possui_dois_formularios_e_botoes():
    html = client.get("/").text
    assert html.count("<form") == 2
    assert html.count('type="submit"') == 2


def test_aba_ativa_no_carregamento():
    html = client.get("/").text
    assert html.count('class="aba ativa"') == 1
    assert re.search(r'<button[^>]*class="aba ativa"[^>]*>\s*ALUNOS\s*<', html)


def test_pagina_monta_com_javascript():
    html = client.get("/").text
    assert 'src="app.js"' in html
    assert re.search(r'<script[^>]*type="module"[^>]*>', html)
