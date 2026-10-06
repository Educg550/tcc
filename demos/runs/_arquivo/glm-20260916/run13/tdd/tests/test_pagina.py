import re

import pytest
from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

ROTULOS = [
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


def _html():
    texto = cliente.get("/").text.casefold()
    return re.sub(r"\s+", " ", texto)


def test_pagina_inicial_responde():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers.get("content-type", "")


def test_style_css_e_app_js_servidos():
    assert cliente.get("/style.css").status_code == 200
    assert cliente.get("/app.js").status_code == 200


def test_pagina_liga_css_e_js():
    html = _html()
    assert "style.css" in html
    assert "app.js" in html


def test_abas_alunos_e_docentes_nessa_ordem():
    html = _html()
    assert "alunos" in html
    assert "docentes" in html
    assert html.index("alunos") < html.index("docentes")


def test_tres_blocos_na_ordem():
    html = _html()
    blocos = [
        "solicitante e evento",
        "endereço do solicitante",
        "informações para pagamento / reembolso",
    ]
    for bloco in blocos:
        assert bloco in html
    posicoes = [html.index(bloco) for bloco in blocos]
    assert posicoes == sorted(posicoes)


@pytest.mark.parametrize("rotulo", ROTULOS)
def test_rotulo_presente(rotulo):
    assert rotulo.casefold() in _html()


def test_opcoes_das_selecoes():
    html = _html()
    for opcao in (
        "mestrado",
        "doutorado",
        "participação em evento",
        "banca de exame ou defesa",
        "outro",
        "pôster",
        "apresentação oral",
        "outra",
        "não irá apresentar trabalho",
    ):
        assert opcao in html


def test_botao_enviar_em_cada_aba():
    pagina = _html() + re.sub(r"\s+", " ", cliente.get("/app.js").text.casefold())
    assert pagina.count("enviar solicitação") >= 2


def test_campos_com_placeholder():
    pagina = cliente.get("/").text + cliente.get("/app.js").text
    assert "placeholder" in pagina.casefold()


def test_cabecalho_institucional_usp():
    html = cliente.get("/").text
    assert "Universidade de São Paulo".casefold() in html.casefold()
    assert "assets/usp-logo.png" in html


def test_logo_usp_servida():
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_titulo_da_confirmacao():
    pagina = cliente.get("/").text + cliente.get("/app.js").text
    assert "Solicitação registrada".casefold() in pagina.casefold()


def test_cores_da_usp():
    css = cliente.get("/style.css").text.casefold()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css


def test_fonte_open_sans_ou_sem_serifa():
    css = cliente.get("/style.css").text.casefold()
    assert "open sans" in css or "sans-serif" in css


def test_css_sem_fonte_remota():
    css = cliente.get("/style.css").text.casefold()
    assert "@import" not in css
    assert "fonts.googleapis" not in css
