import re

import pytest


def get(client, path):
    r = client.get(path)
    assert r.status_code == 200, path
    return r.text


def get_app(client):
    return get(client, "/")


def get_css(client):
    return get(client, "/style.css")


def get_js(client):
    return get(client, "/app.js")


# --- Estrutura basica e abas ---------------------------------------------------

def test_pagina_contem_raculo_da_usp(client):
    html = get_app(client)
    assert "Universidade de Sao Paulo" in html or "Universidade de São Paulo" in html


def test_abas_com_rotulos_exatos_e_ordem(client):
    html = get_app(client)
    i_alunos = html.find("ALUNOS")
    i_docentes = html.find("DOCENTES")
    assert i_alunos != -1
    assert i_docentes != -1
    assert i_alunos < i_docentes


def test_aba_ativa_inicial(client):
    html = get_app(client)
    assert "active" in html


def test_botao_enviar_solicitacao(client):
    html = get_app(client)
    assert "Enviar solicitacao" in html or "Enviar solicitação" in html


# --- Titulos dos blocos --------------------------------------------------------

def test_titulos_blocos(client):
    html = get_app(client)
    for t in [
        "SOLICITANTE E EVENTO",
        "ENDERECO DO SOLICITANTE",
        "ENDERECO DO SOLICITANTE",
        "INFORMACOES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert (t in html) or (t.replace("O DO", "O DO").lower() in html.lower())


def test_bloco_endereco_e_informacoes(client):
    html = get_app(client).lower()
    assert "solicitante e evento" in html
    assert "endereco do solicitante" in html
    assert "informacoes para pagamento" in html


# --- Campos / labels exatos ----------------------------------------------------

def test_todos_campos_obrigatorios(client):
    html = get_app(client)
    for label in [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERIODO DO EVENTO, EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAIS DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO",
        "DETALHAMENTO DO PEDIDO",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NUMERO",
        "NUMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF",
        "RG / RNM",
        "NOME DO BANCO",
        "NUMERO DA AGENCIA",
        "NÚMERO DA AGÊNCIA",
        "NUMERO DA CONTA",
        "NÚMERO DA CONTA",
    ]:
        assert label in html


def test_campos_exclusivos_alunos(client):
    js = get_js(client)
    html = get_app(client)
    blob = html + js
    assert "NIVEL" in blob or "NÍVEL" in blob
    assert "Mestrado" in blob
    assert "Doutorado" in blob
    assert "TIPO DE AUXILIO" in blob or "TIPO DE AUXÍLIO" in blob
    assert "Banca de exame ou defesa" in blob
    assert "Outro" in blob


def test_apresentacao_opcoes(client):
    js = get_js(client)
    html = get_app(client)
    blob = html + js
    assert "Aposter" not in blob
    assert "Poster" in blob or "Pôster" in blob
    assert "Apresentacao oral" in blob or "Apresentação oral" in blob
    assert "Nao ira apresentar trabalho" in blob or "Não irá apresentar trabalho" in blob


def test_valores_formatados(client):
    js = get_js(client)
    assert re.search(r"R\\?\$", js)
    assert re.search(r"CPF", js, re.IGNORECASE)
    assert re.search(r"CEP", js, re.IGNORECASE)


# --- Placeholders --------------------------------------------------------------

def test_placeholders_existentes(client):
    html = get_app(client)
    placeholders = re.findall(r"placeholder=\"([^\"]+)\"", html)
    labels = re.findall(r"<label[^>]*>([^<]+)</label>", html)
    assert len(placeholders) >= 10
    for p in placeholders:
        for l in labels:
            assert l.strip() != p.strip()


# --- Aparência / CSS -----------------------------------------------------------

def test_cores_institucionais(client):
    css = get_css(client)
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_logo_usp_refere(client):
    html = get_app(client)
    assert "usp-logo.png" in html


def test_sem_brasao(client):
    html = get_app(client).lower()
    assert "brasao" not in html
    assert "escudo" not in html


def test_sem_framework_cdn_remoto(client):
    html = get_app(client)
    assert "http://" not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


# --- Rotas e arquivos estáticos ------------------------------------------------

def test_rota_index(client):
    html = get_app(client)
    assert "<html" in html.lower()


def test_rota_style(client):
    css = get_css(client)
    assert "{" in css


def test_rota_appjs(client):
    js = get_js(client)
    assert "function" in js or "=>" in js or "addEventListener" in js


def test_logo_sirve_estatico(client):
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
    assert "image" in r.headers.get("content-type", "")


def test_sem_recarregar_pagina(client):
    js = get_js(client)
    assert "addEventListener" in js
    assert "submit" in js
