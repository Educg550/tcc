"""Testes do Requisito 01: formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Só testes. Nenhuma linha de código de produção aqui.
"""

import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Serviço dos arquivos estáticos (frontend)
# ---------------------------------------------------------------------------


def test_index_existe():
    r = client.get("/")
    assert r.status_code == 200


def test_index_declara_charset_e_viewport():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert '<meta charset="utf-8"' in html
    assert 'name="viewport"' in html


def test_index_referencia_style_e_app_no_proprio_dominio():
    html = client.get("/").text
    assert re.search(r'<link[^>]+style\.css', html)
    assert re.search(r'<script[^>]+app\.js', html)
    # nada de framework, CDN ou recurso remoto
    assert "cdn." not in html
    assert "unpkg.com" not in html
    assert "https://" not in html
    assert "http://" not in html


def test_assets_sao_servidos():
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


def test_style_css_e_app_js_existem():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_style_nao_usa_fonte_remota():
    css = client.get("/style.css").text
    assert "@import" not in css
    assert "https://" not in css
    assert "http://" not in css
    assert "url(" not in css
    # fonte sem serifa quando a Open Sans não estiver disponível
    assert re.search(r"font-family:[^;}]*Open Sans[^;}]*sans-serif", css, re.I)


def test_js_nao_busca_rede():
    js = client.get("/app.js").text
    for proibido in ("fetch(", "XMLHttpRequest", "axios"):
        assert proibido not in js
    assert "https://" not in js
    assert "http://" not in js


def test_logo_no_html():
    html = client.get("/").text
    assert re.search(r'src="assets/usp-logo\.png"', html)


def test_brasao_ausente():
    html = client.get("/").text
    assert "brasao" not in html.lower()
    assert "brasão" not in html.lower()
    assert "escudo" not in html.lower()
    arquivos = {a["caminho"] for a in [{"caminho": p} for p in ("/", "/style.css", "/app.js")]}
    del arquivos
    css = client.get("/style.css").text
    js = client.get("/app.js").text
    assert "escudo" not in css.lower()
    assert "escudo" not in js.lower()
