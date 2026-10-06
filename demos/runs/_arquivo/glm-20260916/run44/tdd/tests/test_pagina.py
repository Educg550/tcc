"""Contrato da página servida em GET / e dos arquivos estáticos dela."""

import re

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

OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
]

# 25 campos de preenchimento (fora das seleções) em cada um dos 2 formulários
QUANTIDADE_DE_PLACEHOLDERS = 50


def test_pagina_abre_com_cabecalho_institucional(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    corpo = resposta.text
    assert "Universidade de São Paulo" in corpo
    assert "assets/usp-logo.png" in corpo


def test_pagina_tem_as_abas_alunos_e_docentes_nessa_ordem(client):
    corpo = client.get("/").text
    assert "ALUNOS" in corpo
    assert "DOCENTES" in corpo
    assert corpo.index("ALUNOS") < corpo.index("DOCENTES")


def test_pagina_tem_todos_os_rotulos(client):
    corpo = client.get("/").text
    for rotulo in ROTULOS:
        assert rotulo in corpo, f"rótulo ausente: {rotulo}"


def test_pagina_tem_as_opcoes_das_selecoes(client):
    corpo = client.get("/").text
    for opcao in OPCOES:
        assert opcao in corpo, f"opção ausente: {opcao}"


def test_cada_formulario_tem_seu_botao_enviar(client):
    corpo = client.get("/").text
    assert corpo.count("Enviar solicitação") >= 2


def test_todo_campo_tem_placeholder(client):
    corpo = client.get("/").text
    placeholders = re.findall(r'placeholder="([^"]*)"', corpo)
    assert len(placeholders) >= QUANTIDADE_DE_PLACEHOLDERS
    assert all(lugar.strip() for lugar in placeholders)


def test_o_titulo_da_confirmacao_existe_na_tela(client):
    html = client.get("/").text
    js = client.get("/app.js").text
    assert "Solicitação registrada" in html or "Solicitação registrada" in js


def test_style_css_e_app_js_sao_referenciados_e_servidos(client):
    corpo = client.get("/").text
    assert "style.css" in corpo
    assert "app.js" in corpo

    estilo = client.get("/style.css")
    assert estilo.status_code == 200
    assert estilo.text.strip() != ""

    script = client.get("/app.js")
    assert script.status_code == 200
    assert script.text.strip() != ""


def test_logo_da_usp_e_servida(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content != b""
