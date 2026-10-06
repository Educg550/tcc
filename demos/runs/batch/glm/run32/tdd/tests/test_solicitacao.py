"""Testes do ofício gerado após envio válido."""
from test_solicitacao import SOLICITACAO_DOCENTE_VALIDA, SOLICITACAO_VALIDA


def test_oficio_alunos_contem_dados(client):
    resposta = post(client, SOLICITACAO_VALIDA)
    oficio = resposta.json()["oficio"]
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: joao@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Banca de exame ou defesa" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso Nacional" in oficio
    assert "Período: 10 a 12 de agosto" in oficio
    assert "Local: São Paulo - SP - Brasil" in oficio
    assert "Link do evento: www.congreso.br" in oficio
    assert "Apresentação de trabalho: Pôster" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Detalhamento: Auxílio para passagens." in oficio
    assert "Rua Sul, 123" in oficio
    assert "Complemento: Apto 45" in oficio
    assert "CEP: 05508-090" in oficio
    assert "Butantã, São Paulo - SP" in oficio
    assert "Data de nascimento: 01/02/1980" in oficio
    assert "CPF: 123.456.789-09" in oficio
    assert "RG / RNM: 12.345.678-9" in oficio
    assert "Banco: Banco do Brasil" in oficio
    assert "Agência: 1234" in oficio
    assert "Conta: 54321-X" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_alunos_sem_link_e_complemento(client):
    dados = dict(SOLICITACAO_VALIDA)
    dados["link"] = ""
    dados["complemento"] = ""
    resposta = post(client, dados)
    oficio = resposta.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_oficio_docente_sem_nivel_e_tipo(client):
    resposta = post(client, SOLICITACAO_DOCENTE_VALIDA)
    oficio = resposta.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Mestrado" not in oficio.split("Programa: Matemática")[1].split("\n")[0]
