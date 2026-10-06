import html as html_lib
import re

from fastapi.testclient import TestClient

from app import app
from tests.helpers import build_payload, form_action, get_forms, name_after_label

client = TestClient(app)


def _strip_tags(text):
    return html_lib.unescape(re.sub(r"<[^>]+>", "", text))


def test_oficio_alunos_contem_todos_os_dados():
    html = client.get("/").text
    alunos, _ = get_forms(html)
    payload = build_payload(alunos, "alunos")
    resp = client.post(form_action(alunos), data=payload)
    assert resp.status_code == 200
    texto = _strip_tags(resp.text)

    assert "Solicitação registrada" in texto
    assert "Interessada(o): Maria da Silva Santos - 9876543" in texto
    assert "E-mail: maria.silva@usp.br" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Ciência da Computação - Mestrado" in texto
    assert "Evento: Congresso Brasileiro de Computação" in texto
    assert "Período: 10/03/2024 a 15/03/2024" in texto
    assert "Local: Fortaleza - CE - Brasil" in texto
    assert "Link do evento: https://evento.exemplo.br" in texto
    assert "Apresentação de trabalho: Pôster" in texto
    assert "Valor solicitado: R$ 1.500,00" in texto
    assert "Detalhamento: Solicito auxílio para participação no evento." in texto
    assert "Rua das Flores, 123" in texto
    assert "Complemento: Apto 45" in texto
    assert "CEP: 05508-090" in texto
    assert "Butantã, São Paulo - SP" in texto
    assert "Data de nascimento: 01/02/1980" in texto
    assert "CPF: 123.456.789-01" in texto
    assert "RG / RNM: 12.345.678-9" in texto
    assert "Banco: Banco do Brasil" in texto
    assert "Agência: 1234" in texto
    assert "Conta: 56789-0" in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
    assert "<<" not in texto
    assert ">>" not in texto


def test_oficio_docentes_usa_assunto_e_programa_fixos():
    html = client.get("/").text
    _, docentes = get_forms(html)
    payload = build_payload(docentes, "docentes")
    resp = client.post(form_action(docentes), data=payload)
    assert resp.status_code == 200
    texto = _strip_tags(resp.text)

    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Direito" in texto
    assert "Programa: Direito -" not in texto
    assert "Interessada(o): Maria da Silva Santos - 9876543" in texto
    assert "<<" not in texto
    assert ">>" not in texto


def test_link_do_evento_ausente_do_oficio_quando_vazio():
    html = client.get("/").text
    alunos, _ = get_forms(html)
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "LINK DO EVENTO, EXAME OU DEFESA")] = ""
    resp = client.post(form_action(alunos), data=payload)
    texto = _strip_tags(resp.text)
    assert "Solicitação registrada" in texto
    assert "Link do evento:" not in texto


def test_complemento_ausente_do_oficio_quando_vazio():
    html = client.get("/").text
    alunos, _ = get_forms(html)
    payload = build_payload(alunos, "alunos")
    payload[name_after_label(alunos, "COMPLEMENTO")] = ""
    resp = client.post(form_action(alunos), data=payload)
    texto = _strip_tags(resp.text)
    assert "Solicitação registrada" in texto
    assert "Complemento:" not in texto
