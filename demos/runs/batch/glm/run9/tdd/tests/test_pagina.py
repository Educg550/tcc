"""Testes da tela: arquivos estáticos servidos, rótulos literais e identidade visual."""

import re
from html.parser import HTMLParser

import pytest


BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

ROTULOS_DAS_DUAS_ABAS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

# Rótulos curtos que também são prefixo de rótulos maiores (NÚMERO DA AGÊNCIA,
# CIDADE DO EVENTO...): precisam ser procurados sem fazer parte de outro rótulo.
ROTULOS_CURTOS = {"NÚMERO", "CIDADE", "ESTADO"}

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

# Títulos de bloco e rótulos do formulário de ALUNOS, na ordem do requisito.
ORDEM_DA_ABA_ALUNOS = [
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


class CamposDeEntrada(HTMLParser):
    """Campos de texto (input/textarea) da página, com seus atributos."""

    TIPOS_SEM_PLACEHOLDER = {
        "submit",
        "button",
        "hidden",
        "reset",
        "checkbox",
        "radio",
        "file",
        "image",
    }

    def __init__(self):
        super().__init__()
        self.campos = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("input", "textarea"):
            return
        atributos = dict(attrs)
        if (atributos.get("type") or "").lower() in self.TIPOS_SEM_PLACEHOLDER:
            return
        self.campos.append((tag, atributos))


def _posicao(texto, rotulo):
    if rotulo in ROTULOS_CURTOS:
        return re.search(rotulo + r"(?!\s*(?:DA|DO))", texto).start()
    return texto.index(rotulo)


@pytest.fixture()
def html(client):
    return client.get("/").text


@pytest.fixture()
def css(client):
    return client.get("/style.css").text


@pytest.fixture()
def js(client):
    return client.get("/app.js").text


def test_pagina_principal_tem_as_abas_alunos_e_docentes_nesta_ordem(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "ALUNOS" in resp.text
    assert "DOCENTES" in resp.text
    assert resp.text.index("ALUNOS") < resp.text.index("DOCENTES")


def test_cada_aba_tem_proprio_formulario_e_botao_de_envio(html):
    assert html.count("<form") == 2
    assert html.count("Enviar solicitação") == 2


@pytest.mark.parametrize("titulo", BLOCOS)
def test_cada_aba_tem_os_tres_blocos_de_campos(html, titulo):
    assert html.count(titulo) >= 2


@pytest.mark.parametrize("rotulo", ROTULOS_DAS_DUAS_ABAS)
def test_rotulos_compartilhados_aparecem_nas_duas_abas(html, rotulo):
    assert html.count(rotulo) >= 2


@pytest.mark.parametrize("rotulo", sorted(ROTULOS_CURTOS))
def test_rotulos_curtos_do_endereco_aparecem_nas_duas_abas(html, rotulo):
    assert len(re.findall(rotulo + r"(?!\s*(?:DA|DO))", html)) >= 2


def test_nivel_e_tipo_de_auxilio_existem_somente_na_aba_alunos(html):
    assert html.count("NÍVEL") == 1
    assert html.count("TIPO DE AUXÍLIO") == 1


@pytest.mark.parametrize("opcao", OPCOES)
def test_todas_as_opcoes_de_selecao_sao_visiveis(html, opcao):
    assert opcao in html


def test_campos_do_formulario_de_alunos_na_ordem_do_requisito(html):
    inicio = html.index("<form")
    formulario = html[inicio : html.index("<form", inicio + 1)]
    posicoes = [_posicao(formulario, rotulo) for rotulo in ORDEM_DA_ABA_ALUNOS]
    assert posicoes == sorted(posicoes)


def test_cabecalho_institucional_da_usp(html, css):
    assert "Universidade de São Paulo" in html
    assert "assets/usp-logo.png" in html + css
    assert html.count("<img") <= 1


def test_titulo_da_confirmacao_esta_na_tela(html, js):
    assert "Solicitação registrada" in html + js


def test_oficio_da_confirmacao_preserva_quebras_de_linha(html):
    assert "<pre" in html


def test_cores_e_fonte_da_identidade_da_usp(css):
    css_minusculo = css.lower()
    assert "#1094ab" in css_minusculo
    assert "#64c4d2" in css_minusculo
    assert "#fcb421" in css_minusculo
    assert "sans-serif" in css_minusculo


def test_nenhum_recurso_e_baixado_da_rede(html, css):
    assert not re.search(r"<script[^>]*src=['\"]https?://", html)
    assert not re.search(r"<link[^>]*href=['\"]https?://", html)
    assert "@import" not in css
    assert not re.search(r"url\(['\"]?https?://", css)


def test_todo_campo_de_texto_tem_placeholder_com_exemplo(html):
    parser = CamposDeEntrada()
    parser.feed(html)
    assert parser.campos
    rotulos = set(ROTULOS_DAS_DUAS_ABAS) | ROTULOS_CURTOS | {"NÍVEL", "TIPO DE AUXÍLIO"}
    for _tag, atributos in parser.campos:
        placeholder = (atributos.get("placeholder") or "").strip()
        assert placeholder, f"campo sem placeholder: {atributos}"
        assert placeholder not in rotulos


def test_detalhamento_aceita_texto_de_varias_linhas(html):
    parser = CamposDeEntrada()
    parser.feed(html)
    assert any(tag == "textarea" for tag, _ in parser.campos)


def test_style_css_e_servido(client):
    resp = client.get("/style.css")
    assert resp.status_code == 200
    assert resp.text.strip()


def test_app_js_e_servido(client):
    resp = client.get("/app.js")
    assert resp.status_code == 200
    assert resp.text.strip()


def test_logo_da_usp_e_servido_como_estatico(client):
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
    assert resp.content
    assert resp.headers["content-type"].startswith("image/")
