import re

from fastapi.testclient import TestClient

import app as app_module

cliente = TestClient(app_module.app)

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


def _estatico(nome):
    for prefixo in ("", "/static", "/public"):
        resposta = cliente.get(prefixo + "/" + nome)
        if resposta.status_code == 200:
            return resposta
    return cliente.get("/" + nome)


def test_pagina_serve_formulario_com_identidade_usp():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "Universidade de São Paulo" in resposta.text
    assert "assets/usp-logo.png" in resposta.text


def test_abas_alunos_e_docentes_na_ordem():
    html = cliente.get("/").text
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_rotulos_dos_campos():
    html = cliente.get("/").text
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo


def test_titulos_dos_blocos():
    html = cliente.get("/").text
    for titulo in (
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ):
        assert titulo in html, titulo


def test_botao_enviar_em_cada_aba():
    html = cliente.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_campos_tem_placeholder():
    conteudo = cliente.get("/").text + _estatico("app.js").text
    assert conteudo.count("placeholder") >= 20


def test_logo_usp_e_servido():
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert len(resposta.content) > 0


def test_estilo_usa_as_cores_da_universidade():
    css = _estatico("style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "sans-serif" in css


def test_sem_recursos_externos():
    html = cliente.get("/").text
    for endereco in re.findall(r'(?:src|href)\s*=\s*"([^"]+)"', html):
        assert not endereco.startswith("http"), endereco


def test_sem_brasao():
    html = cliente.get("/").text.lower()
    assert "brasão" not in html
    assert "brasao" not in html
