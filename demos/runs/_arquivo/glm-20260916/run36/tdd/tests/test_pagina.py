import re


def _ordem_no_html(html, rotulos):
    posicao = 0
    for rotulo in rotulos:
        indice = html.find(rotulo, posicao)
        assert indice >= 0, f"esperava encontrar {rotulo!r} após a posição {posicao}"
        posicao = indice + len(rotulo)


def _primeiro_grupo(html, padrao, fallback):
    encontrado = re.search(padrao, html)
    return encontrado.group(1) if encontrado else fallback


def _caminho_do_css(html):
    return _primeiro_grupo(html, r'href="([^"]*style\.css)"', "/style.css")


def _caminho_do_js(html):
    return _primeiro_grupo(html, r'src="([^"]*app\.js)"', "/app.js")


def _caminho_do_logo(html):
    return _primeiro_grupo(html, r'src="([^"]*usp-logo\.png)"', "/assets/usp-logo.png")


def test_pagina_responde(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers.get("content-type", "")


def test_cabecalho_institucional(client):
    html = client.get("/").text
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_abas_alunos_e_docentes_em_ordem(client):
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.find("ALUNOS") < html.find("DOCENTES")


def test_blocos_em_ordem(client):
    html = client.get("/").text
    _ordem_no_html(html, [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ])


def test_rotulos_dos_campos_em_ordem(client):
    html = client.get("/").text
    _ordem_no_html(html, [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "NÍVEL",
        "Mestrado",
        "Doutorado",
        "TIPO DE AUXÍLIO",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
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
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
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
    ])


def test_botao_enviar_solicitacao(client):
    html = client.get("/").text
    assert "Enviar solicitação" in html


def test_titulo_da_confirmacao_aparece_na_aplicacao(client):
    html = client.get("/").text
    js = client.get(_caminho_do_js(html)).text
    assert "Solicitação registrada" in html or "Solicitação registrada" in js


def test_arquivos_estaticos_servidos(client):
    html = client.get("/").text
    assert client.get(_caminho_do_css(html)).status_code == 200
    assert client.get(_caminho_do_js(html)).status_code == 200
    assert client.get(_caminho_do_logo(html)).status_code == 200


def test_css_usa_as_cores_da_instituicao(client):
    html = client.get("/").text
    css = client.get(_caminho_do_css(html)).text
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "sans-serif" in css.lower()
