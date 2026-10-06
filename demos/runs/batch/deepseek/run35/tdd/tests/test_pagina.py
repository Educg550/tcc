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

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]


# Alguns rótulos de seleção que só a aba de alunos tem.
OPCOES = [
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Pôster",
    "Apresentação oral",
    "Não irá apresentar trabalho",
]


def pagina():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    return resposta.text


def test_pagina_do_formulario_responde():
    assert cliente.get("/").status_code == 200


def test_duas_abas_com_rotulos_exatos_na_ordem():
    html = pagina()
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_cada_aba_tem_seu_botao_enviar():
    html = pagina()
    assert html.count("Enviar solicitação") >= 2


def test_titulos_dos_blocos_visiveis():
    html = pagina()
    for bloco in BLOCOS:
        assert bloco in html


def test_rotulos_exatos_dos_campos():
    html = pagina()
    for rotulo in ROTULOS:
        assert rotulo in html


def test_opcoes_dos_campos_de_selecao():
    html = pagina()
    for opcao in OPCOES:
        assert opcao in html


def test_cabecalho_institucional_da_usp():
    html = pagina()
    assert "Universidade de São Paulo" in html
    assert "usp-logo.png" in html


def test_confirmacao_mostra_titulo_solicitacao_registrada():
    textos = [pagina(), cliente.get("/app.js").text]
    assert any("Solicitação registrada" in texto for texto in textos)
