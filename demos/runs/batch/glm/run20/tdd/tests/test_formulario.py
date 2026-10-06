import re
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def formulario_alunos_valido(**extras):
    dados = {
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_de_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_do_evento": "Congresso Nacional",
        "periodo_do_evento": "10 a 12 de outubro de 2025",
        "cidade_do_evento": "São Paulo",
        "estado_do_evento": "SP",
        "pais_do_evento": "Brasil",
        "link_do_evento": "https://exemplo.com",
        "valor_solicitado": "150000",
        "detalhamento_do_pedido": "Inscrição e hospedagem.",
        "apresentacao_de_trabalho": "Pôster",
        "data_de_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    dados.update(extras)
    return dados


def test_oficio_alunos_apos_envio_valido():
    resposta = client.post("/enviar", json={"aba": "alunos", **formulario_alunos_valido()})
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]

    linha = lambda rotulo: re.search(rf"{rotulo}: (.*)", oficio).group(1)

    assert linha("Interessada\(o\)") == "Maria da Silva - 12345678"
    assert linha("E-mail") == "maria@ime.usp.br"
    assert linha("Assunto") == "Solicitação de Auxílio Financeiro - Participação em evento"
    assert linha("Programa") == "Matemática - Mestrado"
    assert linha("A CCP-Matemática")
    assert linha("Evento") == "Congresso Nacional"
    assert linha("Período") == "10 a 12 de outubro de 2025"
    assert linha("Local") == "São Paulo - SP - Brasil"
    assert linha("Link do evento") == "https://exemplo.com"
    assert linha("Apresentação de trabalho") == "Pôster"
    assert linha("Valor solicitado") == "R$ 1.500,00"
    assert linha("Detalhamento") == "Inscrição e hospedagem."
    assert linha("Data de nascimento") == "01/02/1980"
    assert linha("CPF") == "123.456.789-09"
    assert linha("RG / RNM") == "12.345.678-9"
    assert linha("Banco") == "Banco do Brasil"
    assert linha("Agência") == "1234"
    assert linha("Conta") == "56789-0"
    assert re.search(r"Encaminhe-se ao Serviço Financeiro para providências\.", oficio)


def test_oficio_alunos_sem_complemento_e_sem_link():
    resposta = client.post("/enviar", json={"aba": "alunos", **formulario_alunos_valido(link_do_evento="")})
    oficio = resposta.json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio
    assert resposta.json()["ok"]


def test_oficio_docentes():
    dados = formulario_alunos_valido(tipo_de_auxilio=None, nivel=None)
    resposta = client.post("/enviar", json={"aba": "docentes", **dados})
    assert resposta.status_code == 200
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio


def test_serve_pagina_com_abas():
    resposta = client.get("/")
    assert resposta.status_code == 200
    texto = resposta.text
    assert "ALUNOS" in texto and "DOCENTES" in texto
    assert texto.index("ALUNOS") < texto.index("DOCENTES")
    for rotulo in [
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
        assert rotulo in texto
