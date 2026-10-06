ROTULOS = [
    "ALUNOS",
    "DOCENTES",
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
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


def test_pagina_inicial_e_html(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cada_aba_tem_formulario_com_botao_enviar(client):
    html = client.get("/").text
    assert html.count("<form") >= 2
    assert html.count("Enviar solicitação") >= 2


def test_rotulos_exatos_estao_na_pagina(client):
    html = client.get("/").text
    ausentes = [rotulo for rotulo in ROTULOS if rotulo not in html]
    assert ausentes == []


def test_opcoes_das_selecoes_estao_no_frontend(client):
    frontend = client.get("/").text + client.get("/app.js").text
    ausentes = [opcao for opcao in OPCOES if opcao not in frontend]
    assert ausentes == []


def test_campos_tem_placeholder(client):
    html = client.get("/").text.lower()
    assert html.count("placeholder") >= 20


def test_style_e_appjs_servidos(client):
    for caminho in ("/style.css", "/app.js"):
        resposta = client.get(caminho)
        assert resposta.status_code == 200, caminho
        assert resposta.text.strip()


def test_logo_da_usp_servida(client):
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.content


def test_identidade_visual_da_usp(client):
    html = client.get("/").text
    css = client.get("/style.css").text.lower()
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    assert "#1094ab" in css


def test_titulo_da_confirmacao_no_frontend(client):
    frontend = client.get("/").text + client.get("/app.js").text
    assert "Solicitação registrada" in frontend
