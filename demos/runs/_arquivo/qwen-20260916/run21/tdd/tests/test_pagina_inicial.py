from conftest import _cliente


def teste_abre_pagina():
    resp = _cliente().get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def teste_cabecalho_institucional():
    resp = _cliente().get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in open("style.css", encoding="utf-8").read()


def teste_css_e_js_servidos():
    c = _cliente()
    assert c.get("/style.css").status_code == 200
    assert c.get("/app.js").status_code == 200
