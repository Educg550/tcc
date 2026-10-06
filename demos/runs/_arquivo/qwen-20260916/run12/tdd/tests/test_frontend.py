import re

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def index_html(client):
    return client.get("/").text


@pytest.fixture(scope="module")
def style_css(client):
    return client.get("/style.css").text


@pytest.fixture(scope="module")
def app_js(client):
    return client.get("/app.js").text


EXATOS = [
    "ALUNOS",
    "DOCENTES",
    "Enviar solicita\u00e7\u00e3o",
    "SOLICITANTE E EVENTO",
    "ENDERE\u00c7O DO SOLICITANTE",
    "INFORMA\u00c7\u00d5ES PARA PAGAMENTO / REEMBOLSO",
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "N\u00cdVEL",
    "TIPO DE AUX\u00cdLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PER\u00cdODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PA\u00cdS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "N\u00daMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "NOME DO BANCO",
    "N\u00daMERO DA AG\u00caNCIA",
    "N\u00daMERO DA CONTA",
]


def test_exatos_aparecem(index_html):
    for texto in EXATOS:
        assert texto in index_html


def test_opcoes_nivel(index_html):
    assert "Mestrado" in index_html
    assert "Doutorado" in index_html


def test_opcoes_apresentacao(index_html):
    assert "Apresenta\u00e7\u00e3o oral" in index_html
    assert "N\u00e3o ir\u00e1 apresentar trabalho" in index_html


def test_aba_ativa(index_html):
    assert re.search(r"class=\"[^"]*\btab\b[^"]*\bactive\b[^"]*\"[^>]*>[^<]*ALUNOS", index_html)


def test_campos_iguais_em_ambas_abas(index_html):
    count = index_html.count("NOME COMPLETO - SEM ABREVIAR")
    assert count >= 2


def test_nivel_somente_alunos(index_html):
    assert index_html.count("TIPO DE AUX\u00cdLIO") == 1


def test_docentes_sem_nivel(index_html):
    assert index_html.count("N\u00cdVEL") == 1


def test_placeholders_presentes(index_html):
    placeholders = re.findall(r'placeholder="([^"]+)"', index_html)
    assert len(placeholders) >= 30
    for p in placeholders:
        assert p not in EXATOS


def test_abas_sem_recarregar(index_html):
    assert "<form" in index_html
    assert not re.search(r"<form[^>]+action=", index_html)


def test_cabecalho_usp(index_html):
    assert "assets/usp-logo.png" in index_html
    assert "Universidade de S\u00e3o Paulo" in index_html


def test_css_estatico(servido):
    pass


def test_css_estatico(client):
    resp = client.get("/style.css")
    assert resp.status_code == 200


def test_app_js_estatico(client):
    resp = client.get("/app.js")
    assert resp.status_code == 200


def test_sem_fonte_remota(style_css):
    assert "@import" not in style_css
    assert "http" not in style_css


def test_sem_brasao(index_html):
    assert "bras" not in index_html.lower()
    assert "escudo" not in index_html.lower()


def test_cor_primaria(style_css):
    assert "#1094ab" in style_css


def test_cor_secundaria(style_css):
    assert "#64c4d2" in style_css


def test_cor_amarela(style_css):
    assert "#fcb421" in style_css


def test_open_sans(style_css):
    assert "Open Sans" in style_css


def test_margem_logotipo(style_css):
    # uma regra que d\u00e1 margem em todos os lados do logotipo
    assert re.search(r"margin:\s*[^;]+;", style_css)


def test_oficio_pre_formatado(style_css):
    assert re.search(r"white-space:\s*pre-wrap", style_css)


def test_formatadores_em_app_js(app_js):
    assert "1.500,00" in app_js
    assert re.search(r"replace\([^)]*\d\)\)\)" , app_js)


def test_formatador_cep_em_app_js(app_js):
    assert re.search(r"05508-090", app_js) or "(\d{5})(\d{3})" in app_js


def test_formatador_cpf_em_app_js(app_js):
    assert re.search(r"\d{3}\)\.\(\\d{3}\)\.\(\\d{3}\)-\(\\d{2}\)", app_js) or re.search(
        r"\$1\.\$2\.\$3-\$4", app_js
    )


def test_formatador_data_em_app_js(app_js):
    assert re.search(r"\$1/\$2/\$3", app_js)


def test_oficio_template_em_app_js(app_js):
    assert "Interessada(o):" in app_js
    assert "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias." in app_js


def test_titulo_confirmacao(index_html):
    assert "Solicita\u00e7\u00e3o registrada" in index_html
