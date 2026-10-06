from test_validacao import BASE, CPF_VALIDO
from conftest import _cliente


def teste_oficio_alunos():
    resp = _cliente().post("/solicitacao", json=dict(BASE, cpf=CPF_VALIDO))
    assert resp.status_code == 200
    o = resp.json()["oficio"]
    assert "Interessada(o): Maria Silva - 1234567" in o
    assert "E-mail: maria@ime.usp.br" in o
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in o
    assert "Programa: Matemática - Doutorado" in o
    assert "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a" in o
    assert "interessada(o) acima, conforme segue:" in o
    assert "Dados do evento" in o
    assert "Evento: Congresso" in o
    assert "Período: 01/05 a 05/05" in o
    assert "Local: São Paulo - SP - Brasil" in o
    assert "Apresentação de trabalho: Pôster" in o
    assert "Valor solicitado: R$ 1.500,00" in o
    assert "Detalhamento: Detalhes" in o
    assert "Endereço da(o) interessada(o)" in o
    assert "Rua A, 100" in o
    assert "CEP: 05508-090" in o
    assert "Centro, São Paulo - SP" in o
    assert "Dados para pagamento" in o
    assert "Data de nascimento: 01/02/1980" in o
    assert "CPF: " + CPF_VALIDO in o
    assert "RG / RNM: 12.345.678-9" in o
    assert "Banco: Banco do Brasil" in o
    assert "Agência: 1234" in o
    assert "Conta: 56789-0" in o
    assert "Encaminhe-se ao Serviço Financeiro para providências." in o


def teste_omissao_linhas_opcionais():
    resp = _cliente().post("/solicitacao", json=dict(BASE, cpf=CPF_VALIDO))
    o = resp.json()["oficio"]
    assert "Link do evento:" not in o
    assert "Complemento:" not in o


def teste_linhas_opcionais_presentes():
    resp = _cliente().post(
        "/solicitacao",
        json=dict(BASE, cpf=CPF_VALIDO, link_evento="http://x.com", complemento="Apto 1"),
    )
    o = resp.json()["oficio"]
    assert "Link do evento: http://x.com" in o
    assert "Complemento: Apto 1" in o


def teste_oficio_docentes():
    resp = _cliente().post("/solicitacao", json=dict(BASE, aba="docentes", cpf=CPF_VALIDO))
    o = resp.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in o
    assert "Programa: Matemática\n" in o
    assert "Verba do programa" in o


def teste_confirmacao():
    resp = _cliente().post("/solicitacao", json=dict(BASE, cpf=CPF_VALIDO))
    assert resp.status_code == 200
    assert "oficio" in resp.json()
