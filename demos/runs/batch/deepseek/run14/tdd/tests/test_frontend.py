from fastapi.testclient import TestClient

from app import app

CLIENTE = TestClient(app)

ROTULOS = [
    "SOLICITANTE E EVENTO",
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
    "ENDEREÇO DO SOLICITANTE",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]


def pagina():
    resposta = CLIENTE.get("/")
    assert resposta.status_code == 200
    return resposta.content.decode("utf-8")


def estatico(caminho):
    resposta = CLIENTE.get(caminho)
    assert resposta.status_code == 200, caminho
    return resposta.content.decode("utf-8")


def test_pagina_inicial_e_html():
    assert "text/html" in CLIENTE.get("/").headers["content-type"]


def test_abas_alunos_e_docentes_na_ordem():
    html = pagina()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_rotulos_visiveis():
    html = pagina()
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in pagina()


def test_cabecalho_institucional():
    html = pagina()
    assert "assets/usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_pagina_carrega_os_arquivos_da_tela():
    html = pagina()
    assert "style.css" in html
    assert "app.js" in html


def test_cores_da_universidade():
    css = estatico("/style.css").lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css


def test_javascript_da_tela():
    assert estatico("/app.js").strip()


def test_logo_servido():
    resposta = CLIENTE.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_placeholders_com_exemplos_de_preenchimento():
    texto = pagina() + estatico("/app.js")
    assert texto.count("placeholder") >= 10
