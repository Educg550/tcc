import re

from conftest import ROTULOS, caminho_estatico


def test_pagina_inicial(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers['content-type']


def test_abas_nessa_ordem(index_html):
    assert 'ALUNOS' in index_html
    assert 'DOCENTES' in index_html
    assert index_html.index('ALUNOS') < index_html.index('DOCENTES')


def test_cabecalho_institucional(index_html):
    assert 'Universidade de São Paulo' in index_html
    assert 'usp-logo' in index_html


def test_titulos_dos_blocos(index_html):
    titulos = ['SOLICITANTE E EVENTO', 'ENDEREÇO DO SOLICITANTE', 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO']
    posicoes = [index_html.index(titulo) for titulo in titulos]
    assert posicoes == sorted(posicoes)


def test_rotulos_exatos(index_html):
    for rotulo in ROTULOS:
        assert rotulo in index_html, rotulo


def test_cada_aba_tem_seu_botao_enviar(index_html):
    assert index_html.count('Enviar solicitação') >= 2


def test_opcoes_das_selecoes(index_html, app_js):
    pagina = index_html + app_js
    for opcao in ['Mestrado', 'Doutorado', 'Participação em evento', 'Banca de exame ou defesa', 'Outro']:
        padrao = r'>\s*' + re.escape(opcao) + r'\s*<'
        assert len(re.findall(padrao, pagina)) == 1, opcao
    for opcao in ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho']:
        padrao = r'>\s*' + re.escape(opcao) + r'\s*<'
        assert len(re.findall(padrao, pagina)) == 2, opcao


def test_todo_campo_tem_placeholder_e_nenhum_repete_rotulo(index_html):
    campos = []
    for tag in re.findall(r'<(?:input|textarea)\b[^>]*>', index_html, re.I):
        if re.search(r'type="(?:submit|button|reset|hidden|image)"', tag, re.I):
            continue
        campos.append(tag)
    assert len(campos) >= 50
    placeholders = []
    for tag in campos:
        m = re.search(r'placeholder="([^"]*)"', tag, re.I)
        assert m, 'Campo sem placeholder: ' + tag
        placeholders.append(m.group(1).strip().casefold())
    for rotulo in ROTULOS:
        assert rotulo.strip().casefold() not in placeholders, rotulo


def test_css_com_identidade_usp(client, index_html):
    resposta = client.get(caminho_estatico(index_html, 'style.css'))
    assert resposta.status_code == 200
    css = resposta.text
    for cor in ['#1094ab', '#64c4d2', '#fcb421']:
        assert cor in css, cor
    assert 'Open Sans' in css
    assert 'sans-serif' in css


def test_app_js_servido(client, index_html):
    assert client.get(caminho_estatico(index_html, 'app.js')).status_code == 200


def test_logo_usp_servido(client, index_html):
    m = re.search(r'src="([^"]*usp-logo[^"]*)"', index_html, re.I)
    assert m, 'página não referencia o logotipo da USP'
    caminho = m.group(1)
    if not caminho.startswith('/'):
        caminho = '/' + caminho
    resposta = client.get(caminho)
    assert resposta.status_code == 200
    assert len(resposta.content) > 0


def test_titulo_da_confirmacao(index_html, app_js):
    assert 'Solicitação registrada' in index_html + app_js


def test_nenhum_recurso_remoto(client, index_html):
    css = client.get(caminho_estatico(index_html, 'style.css')).text
    js = client.get(caminho_estatico(index_html, 'app.js')).text
    assert 'http' not in css
    assert 'http' not in js
    assert not re.search(r'<(?:link|script|img)[^>]+https?:', index_html, re.I)
    assert not re.search(r'@import\s+https?:', css, re.I)
