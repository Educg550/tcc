import re
from html import unescape
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def cliente():
    from app import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def pagina(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    return resposta.text


def _texto(pagina):
    return re.sub(r"\s+", " ", unescape(pagina))


ROTULOS_DOS_CAMPOS = [
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


def test_pagina_inicial_serve_o_formulario(pagina):
    assert "<html" in pagina.lower()


def test_cabecalho_institucional(pagina):
    texto = _texto(pagina)
    assert "Universidade de São Paulo" in texto
    assert "usp-logo.png" in texto


def test_sem_brasao(pagina):
    texto = _texto(pagina).lower()
    assert "brasão" not in texto
    assert "escudo" not in texto


def test_abas_alunos_e_docentes_na_ordem(pagina):
    texto = _texto(pagina)
    assert "ALUNOS" in texto
    assert "DOCENTES" in texto
    assert texto.index("ALUNOS") < texto.index("DOCENTES")


@pytest.mark.parametrize("rotulo", ROTULOS_DOS_CAMPOS)
def test_rotulo_visivel(pagina, rotulo):
    assert rotulo in _texto(pagina)


@pytest.mark.parametrize(
    "titulo",
    [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ],
)
def test_titulo_de_bloco(pagina, titulo):
    assert titulo in _texto(pagina)


@pytest.mark.parametrize(
    "opcao",
    [
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ],
)
def test_opcao_de_selecao(pagina, opcao):
    assert opcao in _texto(pagina)


def test_botao_enviar_solicitacao_em_cada_aba(pagina):
    assert _texto(pagina).count("Enviar solicitação") >= 2


class _CamposHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.campos = []

    def handle_starttag(self, tag, attrs):
        if tag in ("input", "textarea", "select"):
            self.campos.append({"tag": tag, **dict(attrs)})


def _campos_digitaveis(pagina):
    parser = _CamposHTML()
    parser.feed(pagina)
    return [
        campo
        for campo in parser.campos
        if campo["tag"] in ("input", "textarea")
        and campo.get("type", "text").lower()
        not in {"hidden", "submit", "button", "checkbox", "radio", "reset", "file"}
    ]


def test_todo_campo_tem_placeholder(pagina):
    campos = _campos_digitaveis(pagina)
    assert campos
    assert [c for c in campos if not (c.get("placeholder") or "").strip()] == []


def test_placeholder_nao_regete_o_rotulo(pagina):
    for campo in _campos_digitaveis(pagina):
        assert campo["placeholder"].strip().upper() not in ROTULOS_DOS_CAMPOS


def test_arquivos_de_estilo_e_comportamento(cliente):
    estilo = cliente.get("/style.css")
    assert estilo.status_code == 200
    assert estilo.text.strip()

    comportamento = cliente.get("/app.js")
    assert comportamento.status_code == 200
    assert comportamento.text.strip()


def test_cores_da_identidade_da_universidade(cliente):
    css = cliente.get("/style.css").text.lower()
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in css


def test_logotipo_servido_como_estatico(cliente):
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content.startswith(b"\x89PNG")


def test_titulo_da_confirmacao(cliente, pagina):
    comportamento = cliente.get("/app.js").text
    assert "Solicitação registrada" in pagina or "Solicitação registrada" in comportamento
