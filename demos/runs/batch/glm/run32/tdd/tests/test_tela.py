"""Testes da estrutura da tela: cabeçalho, abas, blocos e campos."""
import re

BLOCOS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
]


def corpo(client):
    return client.get("/").text


def test_cabecalho_institucional(corpo_index):
    corpo = corpo_index
    assert "Universidade de São Paulo" in corpo
    assert "/assets/usp-logo.png" in corpo or "assets/usp-logo.png" in corpo


def test_abas_alunos_e_docentes_em_ordem(corpo_index):
    corpo = corpo_index
    pos_alunos = corpo.index("ALUNOS")
    pos_docentes = corpo.index("DOCENTES")
    assert pos_alunos < pos_docentes


def test_todos_os_blocos_estao_presentes(corpo_index):
    corpo = corpo_index
    for bloco in BLOCOS:
        assert bloco in corpo


def test_rotulos_do_bloco_solicitante(corpo_index):
    corpo = corpo_index
    rotulos = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
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
    for rotulo in rotulos:
        assert rotulo in corpo


def test_rotulos_do_bloco_endereco(corpo_index):
    corpo = corpo_index
    rotulos = [
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
    ]
    for rotulo in rotulos:
        assert rotulo in corpo


def test_rotulos_do_bloco_pagamento(corpo_index):
    corpo = corpo_index
    rotulos = [
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ]
    for rotulo in rotulos:
        assert rotulo in corpo


def test_selecoes_do_bloco_solicitante(corpo_index):
    corpo = corpo_index
    for opcao in ["Mestrado", "Doutorado"]:
        assert opcao in corpo
    for opcao in [
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
    ]:
        assert opcao in corpo
    for opcao in ["Pôster", "Apresentação oral", "Outra", "Não irá apresentar trabalho"]:
        assert opcao in corpo


def test_todos_os_campos_têm_placeholder(corpo_index):
    corpo = corpo_index
    assert corpo.count('placeholder="') >= 20


def test_estilos_da_pagina_nao_usam_fonte_remota(client):
    css = client.get("/style.css").text
    assert "@import" not in css
    assert "http://" not in css
    assert "https://" not in css


def test_javascript_nao_usa_fonte_externa(client):
    js = client.get("/app.js").text
    assert "http://" not in js
    assert "https://" not in js
