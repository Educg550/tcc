"""Aparência: identidade visual da USP e disposição em uma tela só."""

import re

from fastapi.testclient import TestClient

from app import app


client = TestClient(app)
CSS = client.get("/style.css").text
HTML = client.get("/").text


AZUL_PRIMARIO = "#1094ab"
AZUL_SECUNDARIO = "#64c4d2"
AMARELO = "#fcb421"


def test_cores_da_universidade_presentes():
    for cor in (AZUL_PRIMARIO, AZUL_SECUNDARIO, AMARELO):
        assert cor.lower() in CSS.lower(), cor


def test_azul_primario_dominante():
    qtd = lambda c: CSS.lower().count(c.lower())
    assert qtd(AZUL_PRIMARIO) >= qtd(AZUL_SECUNDARIO)
    assert qtd(AZUL_PRIMARIO) >= qtd(AMARELO)


def test_fonte_sem_serifa():
    assert re.search(r"font-family", CSS)
    assert not re.search(r'serif(?!-)', CSS) or re.search(r'sans-serif', CSS)


def test_campos_em_varias_colunas():
    # a tela cabe sem rolagem: distribuição horizontal, várias colunas
    assert re.search(r'grid-template-columns', CSS) or re.search(r'flex', CSS) or re.search(r'display:\s*grid', CSS)
    assert re.search(r'grid-template-columns[^;]*minmax|grid-template-columns[^;]*%', CSS) or "columns" in CSS


def test_cabecalho_com_nome_da_universidade():
    assert "Universidade de São Paulo" in HTML
    assert re.search(r'assets/usp-logo\.png', HTML)


def test_margem_livre_ao_redor_do_logotipo():
    # margem nos quatro lados ao redor do logo: padding no contêiner do cabeçalho
    assert re.search(r'padding', CSS)


def test_oficio_preserva_quebras_de_linha():
    assert re.search(r'white-space|pre-line|pre-wrap', CSS)
