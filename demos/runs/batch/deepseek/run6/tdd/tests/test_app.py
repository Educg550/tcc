from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _texto_da_aplicacao():
    return client.get("/").text + client.get("/app.js").text


def test_pagina_inicial_e_servida_como_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_arquivos_estaticos_sao_servidos():
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


def test_logo_da_usp_e_servido():
    assert client.get("/assets/usp-logo.png").status_code == 200


def test_abas_alunos_e_docentes_na_ordem():
    texto = _texto_da_aplicacao()
    assert "ALUNOS" in texto
    assert "DOCENTES" in texto
    assert texto.index("ALUNOS") < texto.index("DOCENTES")


def test_identidade_usp():
    texto = _texto_da_aplicacao()
    assert "Universidade de São Paulo" in texto
    assert "assets/usp-logo.png" in texto


def test_titulos_dos_blocos():
    texto = _texto_da_aplicacao()
    for titulo in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert titulo in texto, f"título de bloco ausente: {titulo}"


def test_rotulos_dos_campos():
    texto = _texto_da_aplicacao()
    for rotulo in [
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
    ]:
        assert rotulo in texto, f"rótulo ausente: {rotulo}"


def test_botao_enviar_solicitacao_nas_duas_abas():
    html = client.get("/").text
    assert html.count("Enviar solicitação") >= 2


def test_titulo_da_confirmacao():
    assert "Solicitação registrada" in _texto_da_aplicacao()


def test_cores_da_universidade_no_css():
    css = client.get("/style.css").text
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_sem_recursos_externos_no_html():
    html = client.get("/").text
    assert "http://" not in html
    assert "https://" not in html
