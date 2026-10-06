def test_pagina_inicial_e_servida(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_pagina_liga_o_css_e_o_js(html):
    assert "style.css" in html
    assert "app.js" in html


def test_style_css_e_servido(client):
    assert client.get("/style.css").status_code == 200


def test_app_js_e_servido(client):
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip()


def test_logotipo_usp_e_servido(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")
