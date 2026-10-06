import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

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


def pagina():
    r = client.get("/")
    assert r.status_code == 200
    return r.text


def test_pagina_inicial_servida():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_cabecalho_usp():
    html = pagina()
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_abas_na_ordem():
    html = pagina()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in pagina()


def test_titulos_dos_blocos():
    html = pagina()
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


@pytest.mark.parametrize("rotulo", ROTULOS)
def test_rotulo_presente(rotulo):
    assert rotulo in pagina()


def test_referencia_assets_estaticos():
    html = pagina()
    assert "style.css" in html
    assert "app.js" in html


def test_style_css_servido():
    r = client.get("/style.css")
    assert r.status_code == 200
    css = r.text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "sans-serif" in css


def test_app_js_servido():
    r = client.get("/app.js")
    assert r.status_code == 200


def test_logo_servido():
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def _post_op():
    schema = client.get("/openapi.json").json()
    for path, ops in schema["paths"].items():
        if "post" in ops:
            return path, ops["post"]
    raise AssertionError("nenhuma rota POST encontrada")


def _campos(op):
    content = (op.get("requestBody") or {}).get("content", {})
    for ctype, media in content.items():
        props = (media.get("schema") or {}).get("properties", {})
        if props:
            return ctype, list(props.keys())
    return None, []


def test_solicitacao_vazia_retorna_erro():
    path, op = _post_op()
    ctype, campos = _campos(op)
    dados = {c: "" for c in campos}
    if ctype and "json" in ctype:
        r = client.post(path, json=dados)
    else:
        r = client.post(path, data=dados)
    assert r.status_code < 500
    assert "Preencha todos os campos" in r.text
