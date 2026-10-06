from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_pagina_inicial_serve_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_pagina_inicial_tem_abas_alunos_e_docentes():
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html


def test_pagina_inicial_tem_titulos_dos_blocos():
    html = client.get("/").text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_pagina_inicial_tem_nome_da_universidade():
    html = client.get("/").text
    assert "Universidade de São Paulo" in html


def test_pagina_inicial_tem_botao_enviar():
    html = client.get("/").text
    assert "Enviar solicitação" in html


def test_pagina_inicial_tem_rotulos_dos_campos():
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


def test_style_css_servido_sem_recurso_remoto():
    resp = client.get("/style.css")
    assert resp.status_code == 200
    assert "text/css" in resp.headers["content-type"]
    assert "http://" not in resp.text
    assert "https://" not in resp.text


def test_app_js_servido_sem_recurso_remoto():
    resp = client.get("/app.js")
    assert resp.status_code == 200
    assert "http://" not in resp.text
    assert "https://" not in resp.text


def test_logo_usp_servido():
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
