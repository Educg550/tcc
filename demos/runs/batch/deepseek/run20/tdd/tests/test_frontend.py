import re

import pytest


def _get(client, *caminhos):
    for caminho in caminhos:
        resposta = client.get(caminho)
        if resposta.status_code == 200:
            return resposta
    raise AssertionError(f"nenhum destes caminhos respondeu 200: {caminhos}")


def _texto(resposta):
    return re.sub(r"\s+", " ", resposta.text)


@pytest.fixture
def pagina(client):
    return _get(client, "/", "/index.html")


@pytest.fixture
def css(client):
    return _get(client, "/style.css")


@pytest.fixture
def js(client):
    return _get(client, "/app.js")


def test_pagina_e_html(pagina):
    assert "text/html" in pagina.headers.get("content-type", "")


def test_abas_com_rotulos_exatos_na_ordem(pagina):
    html = _texto(pagina)
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_blocos_tem_titulo(pagina):
    html = _texto(pagina)
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


ROTULOS = (
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
)


def test_rotulos_dos_campos(pagina, js):
    texto = _texto(pagina) + " " + _texto(js)
    assert [rotulo for rotulo in ROTULOS if rotulo not in texto] == []


def test_botao_enviar_em_cada_aba(pagina, js):
    texto = _texto(pagina) + " " + _texto(js)
    assert texto.count("Enviar solicitação") >= 2


def test_opcoes_das_selecoes(pagina, js):
    texto = _texto(pagina) + " " + _texto(js)
    for opcao in (
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opcao in texto, opcao


def test_cabecalho_institucional(pagina):
    html = _texto(pagina)
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_logotipo_e_servido_como_estatico(client):
    resposta = _get(client, "/assets/usp-logo.png", "/usp-logo.png")
    assert resposta.headers.get("content-type", "").startswith("image/")


def test_cores_da_universidade(css):
    estilo = css.text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in estilo


def test_fonte_sem_serifa(css):
    estilo = css.text.lower()
    assert "open sans" in estilo or "sans-serif" in estilo


def test_sem_recursos_externos(pagina, css, js):
    texto = pagina.text + css.text + js.text
    assert "http://" not in texto
    assert "https://" not in texto
    assert "//cdn" not in texto


def test_oficio_preserva_quebras_de_linha(css):
    assert re.search(r"white-space\s*:\s*pre", css.text)
