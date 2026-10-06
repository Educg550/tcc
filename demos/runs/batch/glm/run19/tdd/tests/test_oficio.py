"""Testes do ofício gerado após envio válido."""

from fastapi.testclient import TestClient

from app import app
from tests.test_validacao import dados_alunos_validos, dados_docentes_validos

client = TestClient(app)


def test_oficio_alunos_linhas_principais():
    response = client.post("/solicitar", json=dados_alunos_validos())
    body = response.json()
    oficio = body.get("oficio", "")
    assert oficio != ""
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Evento: Congresso de Matemática" in oficio
    assert "Valor solicitado: R$ 1,00" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_oficio_alunos_nao_tem_linha_link_quando_vazio():
    response = client.post("/solicitar", json=dados_alunos_validos(link=""))
    body = response.json()
    oficio = body.get("oficio", "")
    assert "Link do evento:" not in oficio


def test_oficio_alunos_nao_tem_linha_complemento_quando_vazio():
    response = client.post("/solicitar", json=dados_alunos_validos(complemento=""))
    body = response.json()
    oficio = body.get("oficio", "")
    assert "Complemento:" not in oficio


def test_oficio_alunos_com_link_e_complemento_preenchidos():
    response = client.post(
        "/solicitar",
        json=dados_alunos_validos(link="https://exemplo.com", complemento="Apto 12"),
    )
    body = response.json()
    oficio = body.get("oficio", "")
    assert "Link do evento: https://exemplo.com" in oficio
    assert "Complemento: Apto 12" in oficio


def test_oficio_docentes_assunto_e_programa():
    response = client.post("/solicitar", json=dados_docentes_validos())
    body = response.json()
    oficio = body.get("oficio", "")
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    # não deve incluir NÍVEL
    assert "Programa: Matemática -" not in oficio


def test_oficio_valor_formatado():
    response = client.post("/solicitar", json=dados_alunos_validos(valor=150000))
    body = response.json()
    oficio = body.get("oficio", "")
    assert "Valor solicitado: R$ 1.500,00" in oficio


def test_oficio_contem_secoes():
    response = client.post("/solicitar", json=dados_alunos_validos())
    body = response.json()
    oficio = body.get("oficio", "")
    assert "Dados do evento" in oficio
    assert "Endereço da(o) interessada(o)" in oficio
    assert "Dados para pagamento" in oficio
    assert "A CCP-" in oficio
    assert "aprovou na data de hoje, a solicitação de auxílio financeiro" in oficio


def test_oficio_mantem_quebras_de_linha():
    response = client.post("/solicitar", json=dados_alunos_validos())
    body = response.json()
    oficio = body.get("oficio", "")
    linhas = oficio.split("\n")
    assert len(linhas) > 10
