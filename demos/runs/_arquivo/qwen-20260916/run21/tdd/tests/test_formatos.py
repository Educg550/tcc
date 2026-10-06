import re


def _js():
    return open("app.js", encoding="utf-8").read()


def teste_appjs_formata_valor():
    js = _js()
    assert "R$" in js
    assert re.search(r"R\$\s*(\d{1,3}\.\d{3}|\d)", js)


def teste_appjs_formata_cpf():
    assert re.search(r"\d{3}\?\.\?\d{3}\?\.\?\d{3}\?-", _js())


def teste_appjs_formata_cep():
    assert re.search(r"\d{5}-\d{3}", _js())


def teste_appjs_formata_data():
    assert re.search(r"dd/mm/aaaa", _js())
