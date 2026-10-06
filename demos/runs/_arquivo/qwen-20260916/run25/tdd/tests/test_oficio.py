from test_api_validacao import alunos, docentes
from conftest import client, html_da_pagina


def oficio_de(corpo):
    resposta = client().post("/solicitacao", json=corpo)
    assert resposta.json()["erros"] == []
    return resposta.json()["oficio"]


def oficio_alunos(**campos):
    return oficio_de(alunos(**campos))


def oficio_docentes(**campos):
    return oficio_de(docentes(**campos))


def test_titulo_da_confirmacao():
    assert "Solicita\u00e7\u00e3o registrada" in html_da_pagina()


def test_linha_do_interessado():
    assert (
        "Interessada(o): Maria Silva Souza - 1234567" in oficio_alunos()
    )


def test_email_e_assunto():
    texto = oficio_alunos()
    assert "E-mail: maria@ime.usp.br" in texto
    assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Participa\u00e7\u00e3o em evento" in texto
    assert "Programa: Ci\u00eancia da Computa\u00e7\u00e3o - Doutorado" in texto


def test_corpo_do_oficio():
    texto = oficio_alunos()
    assert "A CCP-Ci\u00eancia da Computa\u00e7\u00e3o aprovou na data de hoje" in texto
    assert "Dados do evento" in texto
    assert "Evento: XVII SBC" in texto
    assert "Per\u00edodo: 10 a 14 de julho de 2025" in texto
    assert "Local: Belo Horizonte - MG - Brasil" in texto
    assert "Link do evento: https://sbc.org.br" in texto
    assert "Apresenta\u00e7\u00e3o de trabalho: P\u00f4ster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Participa\u00e7\u00e3o com apresenta\u00e7\u00e3o de trabalho." in texto


def test_bloco_endereco():
    texto = oficio_alunos()
    assert "Endere\u00e7o da(o) interessada(o)" in texto
    assert "Rua do Mat\u00e3o, 1010" in texto
    assert "Complemento: Bloco C" in texto
    assert "CEP: 05508-090" in texto
    assert "Cidade Universit\u00e1ria, S\u00e3o Paulo - SP" in texto


def test_bloco_pagamento():
    texto = oficio_alunos()
    assert "Dados para pagamento" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-09" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Ag\u00eancia: 1234" in texto
    assert "Conta: 56789-0" in texto


def test_encerramento():
    assert (
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias."
        in oficio_alunos()
    )


def test_oficio_da_aba_docentes():
    texto = oficio_docentes()
    assert "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa" in texto
    assert "Programa: Ci\u00eancia da Computa\u00e7\u00e3o\n" in texto + "\n"
    assert "Programa: Ci\u00eancia da Computa\u00e7\u00e3o - " not in texto


def test_linha_do_link_sai_quando_vazia():
    texto = oficio_alunos(link="")
    assert "Link do evento:" not in texto
    assert "Valor solicitado: R$ 1.500,00" in texto


def test_linha_do_complemento_sai_quando_vazia():
    texto = oficio_alunos(complemento="")
    assert "Complemento:" not in texto
    assert "CEP: 05508-090" in texto


def test_valor_formatado_no_oficio():
    assert "Valor solicitado: R$ 1.500.000,00" in oficio_alunos(valor="150000000")


def test_quebras_de_linha_preservadas():
    assert "\n" in oficio_alunos()
