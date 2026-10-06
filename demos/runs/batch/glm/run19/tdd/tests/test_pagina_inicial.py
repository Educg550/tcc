"""Testes da página inicial do formulário de auxílio financeiro."""

import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_index_retorna_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_index_tem_titulo_da_pagina():
    response = client.get("/")
    assert "Auxílio Financeiro" in response.text


def test_index_tem_duas_abas_com_rotulos_exatos():
    response = client.get("/")
    html = response.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    pos_alunos = html.find("ALUNOS")
    pos_docentes = html.find("DOCENTES")
    assert pos_alunos != -1
    assert pos_docentes != -1
    assert pos_alunos < pos_docentes


def test_index_abas_sao_clicaveis():
    response = client.get("/")
    html = response.text
    assert 'id="tab-alunos"' in html
    assert 'id="tab-docentes"' in html


def test_index_aba_alunos_ativa_por_padrao():
    response = client.get("/")
    html = response.text
    # a aba ALUNOS deve ter classe indicando que está ativa
    padrao = re.compile(r'<[^>]*id="tab-alunos"[^>]*class="[^"]*active[^"]*"', re.IGNORECASE)
    assert padrao.search(html) is not None


def test_index_aba_docentes_nao_ativa_por_padrao():
    response = client.get("/")
    html = response.text
    padrao = re.compile(r'<[^>]*id="tab-docentes"[^>]*class="[^"]*active[^"]*"', re.IGNORECASE)
    assert padrao.search(html) is None


def test_index_formularios_presentes():
    response = client.get("/")
    html = response.text
    assert '<form' in html
    # dois formulários: um para alunos, um para docentes
    assert html.count("<form") == 2


def test_index_titulos_dos_blocos():
    response = client.get("/")
    html = response.text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_index_rotulos_comuns():
    response = client.get("/")
    html = response.text
    rotulos = [
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
        assert rotulo in html, f"Rótulo ausente: {rotulo}"


def test_index_rotulos_somente_na_aba_alunos():
    response = client.get("/")
    html = response.text
    assert "NÍVEL" in html
    assert "TIPO DE AUXÍLIO" in html
    # o formulário de docentes não deve conter NÍVEL nem TIPO DE AUXÍLIO
    m = re.search(r'<form[^>]*id="form-docentes"[\s\S]*?</form>', html)
    assert m is not None
    form_docentes = m.group(0)
    assert "NÍVEL" not in form_docentes
    assert "TIPO DE AUXÍLIO" not in form_docentes


def test_index_opcoes_de_nivel():
    response = client.get("/")
    html = response.text
    assert "Mestrado" in html
    assert "Doutorado" in html


def test_index_opcoes_de_tipo_de_auxilio():
    response = client.get("/")
    html = response.text
    assert "Participação em evento" in html
    assert "Banca de exame ou defesa" in html
    assert "Outro" in html


def test_index_opcoes_de_apresentacao():
    response = client.get("/")
    html = response.text
    for opcao in ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert opcao in html


def test_index_botoes_enviar():
    response = client.get("/")
    html = response.text
    assert html.count("Enviar solicitação") == 2


def test_index_campos_obrigatorios_marcados():
    response = client.get("/")
    html = response.text
    # LINK DO EVENTO é opcional: não deve ter required
    m = re.search(r'<input[^>]*id="alunos-link-evento"[^>]*>', html)
    if m:
        assert "required" not in m.group(0)
    m = re.search(r'<input[^>]*id="alunos-complemento"[^>]*>', html)
    if m:
        assert "required" not in m.group(0)


def test_index_tem_placeholders():
    response = client.get("/")
    html = response.text
    assert "placeholder" in html.lower()


def test_static_style_css():
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "css" in response.headers["content-type"]


def test_static_app_js():
    response = client.get("/static/app.js")
    assert response.status_code == 200


def test_style_usa_cores_da_usp():
    response = client.get("/static/style.css")
    css = response.text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_index_referencia_logo_da_usp():
    response = client.get("/")
    html = response.text
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html


def test_index_nao_tem_brasao():
    response = client.get("/")
    html = response.text.lower()
    assert "brasao" not in html
    assert "escudo" not in html


def test_index_referencia_fonte_open_sans():
    response = client.get("/")
    html = response.text
    # não deve carregar fonte remota (CDN)
    assert "fonts.googleapis" not in html
    # deve referenciar Open Sans no CSS
    css = client.get("/static/style.css").text.lower()
    assert "open sans" in css


def test_index_nao_usa_cdn_externo():
    response = client.get("/")
    html = response.text
    assert "cdn." not in html
    assert "https://" not in html


def test_assets_logo_disponivel():
    response = client.get("/static/assets/usp-logo.png")
    assert response.status_code == 200
