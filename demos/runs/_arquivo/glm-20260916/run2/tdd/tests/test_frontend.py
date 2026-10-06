import re

ROTULOS_SOLICITANTE_E_EVENTO = [
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
]

ROTULOS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]

ROTULOS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

TITULOS_DE_BLOCO = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]

TODOS_OS_ROTULOS = ROTULOS_SOLICITANTE_E_EVENTO + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO

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

CAMPO = re.compile(r"""<(?:input|textarea)[^>]*>""")
FONTE_DE_IMAGEM = re.compile(r"""<img[^>]*src=["']([^"']*)["']""", re.IGNORECASE)
PLACEHOLDER = re.compile(r"""placeholder=["']([^"']*)["']""")


def test_pagina_inicial_existe(client):
    assert client.get("/").status_code == 200


def test_abas_na_ordem(client):
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_de_bloco_e_rotulos(client):
    html = client.get("/").text
    for texto in TITULOS_DE_BLOCO + TODOS_OS_ROTULOS:
        assert texto in html, texto


def test_botao_enviar_em_cada_aba(client):
    html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_opcoes_de_selecao(client):
    html = client.get("/").text
    for opcao in OPCOES:
        assert opcao in html, opcao


def test_docentes_nao_tem_campos_exclusivos_de_alunos(client):
    html = client.get("/").text
    assert html.count("NÍVEL") == 1
    assert html.count("TIPO DE AUXÍLIO") == 1


def test_referencia_css_e_js(client):
    html = client.get("/").text
    assert "style.css" in html
    assert "app.js" in html


def test_cabecalho_usp(client, buscar):
    html = client.get("/").text
    css = buscar("/style.css")
    texto_css = css.text if css is not None else ""
    assert "usp-logo.png" in html or "usp-logo.png" in texto_css
    assert "Universidade de São Paulo" in html
    for fonte in FONTE_DE_IMAGEM.findall(html):
        assert "brasao" not in fonte.lower()
        assert "escudo" not in fonte.lower()


def test_logotipo_servido(buscar):
    assert buscar("/assets/usp-logo.png") is not None


def test_placeholders_nos_campos(client):
    html = client.get("/").text
    campos = CAMPO.findall(html)
    assert campos
    for campo in campos:
        if any(tipo in campo for tipo in ("hidden", "submit", "button", "image")):
            continue
        assert "placeholder" in campo, campo
    rotulos = {rotulo.casefold() for rotulo in TODOS_OS_ROTULOS}
    for exemplo in PLACEHOLDER.findall(html):
        assert exemplo.casefold() not in rotulos, exemplo


def test_folha_de_estilo(buscar):
    resposta = buscar("/style.css")
    assert resposta is not None
    css = resposta.text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css or "#fcb421" in css
    assert "sans-serif" in css
    assert "grid" in css or "flex" in css
    assert "http://" not in css and "https://" not in css


def test_script(buscar):
    resposta = buscar("/app.js")
    assert resposta is not None
    assert "R$" in resposta.text


def test_titulo_da_confirmacao(client, buscar):
    html = client.get("/").text
    js = buscar("/app.js")
    texto_js = js.text if js is not None else ""
    assert "Solicitação registrada" in html or "Solicitação registrada" in texto_js
