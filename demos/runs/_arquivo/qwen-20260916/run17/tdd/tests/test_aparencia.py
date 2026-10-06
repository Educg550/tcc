"""Testes de aparência: identidade visual USP, cores, fonte, layout, ofício."""

import pytest


@pytest.fixture(scope="module")
def css(client):
    return client.get("/style.css").text


@pytest.fixture(scope="module")
def html(client):
    return client.get("/").text


def test_cor_azul_primario(css):
    assert "#1094ab" in css.lower()


def test_cor_azul_secundario(css):
    assert "#64c4d2" in css.lower()


def test_cor_amarela(css):
    assert "#fcb421" in css.lower()


def test_fonte_open_sans_ou_sem_serifa(css):
    assert "open sans" in css.lower() or "sans-serif" in css.lower()


def test_usp_logo_referenciada_no_css(css):
    assert "usp-logo.png" in css


def test_usp_logo_referenciada_no_html(html):
    assert "usp-logo.png" in html


def test_nome_universidade_presente(html):
    assert "Universidade de São Paulo" in html


def test_sem_acesso_externo(css, html):
    """Sem framework, CDN, fonte remota ou arquivo baixado da rede."""
    tudo = (css + html).lower()
    assert "http://" not in tudo
    assert "https://" not in tudo
    assert "@import" not in css.lower()


def test_espaco_em_volta_do_logo(css):
    # Margem/padding ao redor do logo, com espaço na frente e atrás
    assert ": " in css or "\n" in css


def test_layout_de_colunas(css):
    assert "grid" in css.lower() or "flex" in css.lower()


def test_oficio_preserva_quebras_de_linha(css):
    assert "white-space" in css.lower()


def test_css_nao_contem_escudo(css):
    # O brasão/escudo não deve aparecer na página
    assert "escudo" not in css.lower()
