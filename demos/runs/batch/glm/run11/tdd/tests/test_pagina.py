"""A página inicial serve o formulário com abas, rótulos e mensagens exatas."""

import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _html():
    return client.get("/").text


def test_pagina_inicial_ok():
    assert client.get("/").status_code == 200


def test_abas_rotulos():
    html = _html()
    assert re.search(r">\s*ALUNOS\s*<", html)
    assert re.search(r">\s*DOCENTES\s*<", html)


def test_alunos_ativa_na_abertura():
    m = re.search(r"<[^>]*class=\"([^\"]*)\"[^>]*>\s*ALUNOS\s*<", _html())
    assert m
    assert re.search(r"\bactive\b", m.group(1))


def test_rotulos_dos_campos():
    html = _html()
    rotulos = [
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
    for rotulo in rotulos:
        assert rotulo in html, rotulo


def test_nivel_e_tipo_de_auxilio_somente_na_aba_alunos():
    html = _html()
    alunos = _secao_por_id(html, "form-alunos")
    docentes = _secao_por_id(html, "form-docentes")
    assert "NÍVEL" in alunos
    assert "TIPO DE AUXÍLIO" in alunos
    assert "NÍVEL" not in docentes
    assert "TIPO DE AUXÍLIO" not in docentes


def test_cabecalho_institucional():
    html = _html()
    assert "Universidade de São Paulo" in html
    assert re.search(r"src=\"?/?(assets/)?usp-logo\.png", html)
    assert "Pós-Graduação IME-USP" in html


def test_botao_enviar_existe():
    assert "Enviar solicitação" in _html()


def test_mensagens_validacao_presentes_no_html():
    html = _html()
    mensagens = [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        "CPF inválido",
        "Data de nascimento inválida",
    ]
    for msg in mensagens:
        assert msg in html, msg


def _secao_por_id(html, id_valor):
    m = re.search(
        r"<[^>]*id=\"" + id_valor + r"\"[^>]*>(.*?)</form>", html, re.DOTALL
    )
    assert m, id_valor
    return m.group(1)
