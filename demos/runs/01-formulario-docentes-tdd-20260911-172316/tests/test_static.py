from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_pagina_principal_carrega():
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_pagina_tem_cabecalho_institucional():
    html = client.get("/").text
    assert "Universidade de São Paulo" in html


def test_pagina_tem_as_duas_abas_na_ordem_certa():
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_pagina_tem_titulos_dos_tres_blocos():
    html = client.get("/").text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_pagina_tem_botao_enviar_solicitacao_nas_duas_abas():
    html = client.get("/").text
    assert html.count("Enviar solicitação") == 2


def test_rotulos_dos_campos_aparecem_na_pagina():
    html = client.get("/").text
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
        assert rotulo in html


def test_style_css_e_servido_e_usa_as_cores_da_usp():
    resposta = client.get("/style.css")
    assert resposta.status_code == 200
    assert "#1094ab" in resposta.text


def test_app_js_e_servido():
    resposta = client.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip() != ""


def test_logo_da_usp_e_servido():
    resposta = client.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
