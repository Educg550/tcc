import re

from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

ROTULOS = [
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


def _pagina():
    return cliente.get("/")


def test_pagina_inicial_serve_o_formulario():
    resposta = _pagina()
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_cabecalho_com_a_identidade_da_universidade():
    html = _pagina().text
    assert "Universidade de São Paulo" in html
    assert "assets/usp-logo.png" in html


def test_logo_servido_como_estatico():
    assert cliente.get("/assets/usp-logo.png").status_code == 200


def test_pagina_sem_o_brasao():
    html = _pagina().text.lower()
    assert "brasao" not in html
    assert "brasão" not in html
    assert "escudo" not in html


def test_abas_alunos_e_docentes():
    html = _pagina().text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_dos_blocos():
    html = _pagina().text
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_rotulos_dos_campos():
    html = _pagina().text
    for rotulo in ROTULOS:
        assert rotulo in html


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in _pagina().text


def test_placeholders_sao_exemplos_e_nao_rotulos():
    html = _pagina().text
    exemplos = re.findall(r"""placeholder=["']([^"']*)["']""", html)
    assert len(exemplos) >= 26
    for exemplo in exemplos:
        assert exemplo.strip()
        assert exemplo not in ROTULOS


def test_css_com_as_cores_da_universidade():
    css = cliente.get("/style.css").text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_css_com_fonte_sem_serifa():
    assert "sans-serif" in cliente.get("/style.css").text.lower()


def test_javascript_servido():
    resposta = cliente.get("/app.js")
    assert resposta.status_code == 200
    assert resposta.text.strip()
