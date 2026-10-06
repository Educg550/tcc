"""Testes da página única: abas, campos, rótulos, placeholders e blocos."""

import re

import pytest


@pytest.fixture(scope="module")
def html(client):
    return client.get("/").text


LABELS = [
    "ALUNOS",
    "DOCENTES",
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
    "Enviar solicitação",
]


@pytest.mark.parametrize("label", LABELS)
def test_rotulo_aparece_na_pagina(html, label):
    """Todos os rótulos exatos definidos no requisito aparecem na tela."""
    assert label in html


def test_abas_na_ordem_exata(html):
    """As duas abas têm os rótulos exatos ALUNOS e DOCENTES, nessa ordem."""
    i, j = html.index("ALUNOS"), html.index("DOCENTES")
    assert i < j


def test_abas_com_seletor_distinguivel(html):
    """Existe um mecanismo (atributos) que distingue a aba ativa da inativa."""
    assert re.search(r"data-tab|aria-selected|role=.tab\"", html)


def test_dois_botoes_de_envio(html):
    """Cada aba tem o seu próprio botão Enviar solicitação ao fim."""
    assert html.count("Enviar solicitação") >= 2


def test_campo_nivel_existe_html(html):
    assert re.search(r"name=.nivel.", html)


def test_campo_tipo_auxilio_existe_html(html):
    assert re.search(r"name=.tipo_auxilio.", html)


def test_campo_valor_existe_html(html):
    assert re.search(r"name=.valor.", html)


def test_campo_link_existe_html(html):
    assert re.search(r"name=.link_evento.", html)


def test_campo_complemento_existe_html(html):
    assert re.search(r"name=.complemento.", html)


def test_todos_os_campos_tem_placeholder(html):
    """Todo input/select/textarea tem placeholder com exemplo de preenchimento."""
    for i, field in enumerate(re.finditer(r"<(input|select|textarea)\b", html)):
        # Pega o trecho do elemento até o fechamento '>'
        fim = html.index(">", i)
        assert "placeholder=" in html[i:fim], f"campo {i} sem placeholder"


@pytest.mark.parametrize("img,css", [("/assets/usp-logo.png", "/style.css")])
def test_estaticos_servidos(client, img, css):
    assert client.get(img).status_code == 200
    assert client.get(css).status_code == 200


def test_app_js_servido(client):
    assert client.get("/app.js").status_code == 200


def test_style_css_e_app_js_servem_a_pagina(html):
    assert "style.css" in html and "app.js" in html
