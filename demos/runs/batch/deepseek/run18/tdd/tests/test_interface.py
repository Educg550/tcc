"""Testes da interface do formulário de auxílio financeiro (requisito 01)."""

import re

import pytest
from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

ROTULOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
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
    "Enviar solicitação",
]

_pagina_servida = None


def _pagina():
    global _pagina_servida
    if _pagina_servida is None:
        resposta = cliente.get("/")
        assert resposta.status_code == 200, "a página do formulário deve ser servida em /"
        _pagina_servida = resposta.text
    return _pagina_servida


def _estatico(nome):
    referencia = re.search(r'(?:href|src)="([^"]*' + re.escape(nome) + r')"', _pagina())
    assert referencia, "a página deve referenciar " + nome
    caminho = referencia.group(1).lstrip(".")
    if not caminho.startswith("/"):
        caminho = "/" + caminho
    resposta = cliente.get(caminho)
    assert resposta.status_code == 200, nome + " deve ser servido como arquivo estático"
    return resposta.text


def test_a_pagina_traz_o_cabecalho_institucional_e_as_duas_abas():
    html = _pagina()
    assert "Universidade de São Paulo" in html
    assert "assets/usp-logo.png" in html
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


@pytest.mark.parametrize("rotulo", ROTULOS)
def test_o_rotulo_aparece_na_pagina(rotulo):
    assert rotulo in _pagina()


def test_todo_campo_tem_placeholder_com_exemplo():
    placeholders = re.findall(r"placeholder=['\"]([^'\"]*)['\"]", _pagina())
    assert len(placeholders) >= 25, "todos os campos devem ter placeholder"
    assert all(texto.strip() for texto in placeholders), "nenhum placeholder pode ficar vazio"
    repetidos = [texto for texto in placeholders if texto.strip().upper() in ROTULOS]
    assert repetidos == [], "o placeholder não pode repetir o rótulo do campo"


def test_o_css_traz_as_cores_e_a_fonte_da_universidade():
    css = _estatico("style.css").lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "open sans" in css or "sans-serif" in css


def test_o_javascript_da_tela_e_servido():
    assert _estatico("app.js").strip()


def test_a_confirmacao_aparece_na_interface():
    textos = _pagina() + _estatico("app.js")
    assert "Solicitação registrada" in textos
