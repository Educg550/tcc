import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def pagina_inicial():
    return cliente.get("/").text


def test_pagina_inicial_e_servida():
    assert cliente.get("/").status_code == 200


def test_abas_alunos_e_docentes_na_ordem():
    html = pagina_inicial()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_titulos_dos_blocos_visiveis():
    html = pagina_inicial()
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html


def test_rotulos_dos_campos_visiveis():
    html = pagina_inicial()
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo


def test_botao_enviar_solicitacao():
    assert "Enviar solicitação" in pagina_inicial()


def test_identidade_institucional_no_cabecalho():
    html = pagina_inicial()
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html + cliente.get("/style.css").text


def test_estilos_da_universidade_no_css():
    resposta = cliente.get("/style.css")
    assert resposta.status_code == 200
    css = resposta.text.lower()
    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css


def test_javascript_e_servido():
    assert cliente.get("/app.js").status_code == 200


def test_logotipo_e_servido():
    resposta = cliente.get("/assets/usp-logo.png")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("image/")


def _rota_de_envio():
    for rota in app.routes:
        metodos = getattr(rota, "methods", set()) or set()
        if "POST" in metodos:
            return rota.path
    return None


def test_envio_vazio_mostra_campos_obrigatorios():
    rota = _rota_de_envio()
    assert rota is not None
    resposta = cliente.post(rota, data={})
    assert "Preencha todos os campos" in resposta.text


def test_envio_invalido_nao_gera_oficio():
    rota = _rota_de_envio()
    assert rota is not None
    resposta = cliente.post(rota, data={})
    assert "Encaminhe-se ao Serviço Financeiro para providências." not in resposta.text
