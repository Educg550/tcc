import re

import pytest
from fastapi.testclient import TestClient

import app as app_module


client = TestClient(app_module.app)


REQUIRED_STUDENT = {
    "NOME COMPLETO - SEM ABREVIAR": "Maria da Silva",
    "N. USP": "12345678",
    "PROGRAMA": "Ciência da Computação",
    "NÍVEL": "Mestrado",
    "TIPO DE AUXÍLIO": "Participação em evento",
    "E-MAIL": "maria@ime.usp.br",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA": "Congresso de Computação",
    "PERÍODO DO EVENTO, EXAME OU DEFESA": "10/10/2025 a 12/10/2025",
    "CIDADE DO EVENTO, EXAME OU DEFESA": "São Paulo",
    "ESTADO DO EVENTO, EXAME OU DEFESA": "SP",
    "PAÍS DO EVENTO, EXAME OU DEFESA": "Brasil",
    "LINK DO EVENTO, EXAME OU DEFESA": "https://evento.usp.br",
    "VALOR SOLICITADO (R$)": "R$ 1.500,00",
    "DETALHAMENTO DO PEDIDO": "Deslocamento e hospedagem.",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?": "Pôster",
    "DATA DE NASCIMENTO": "01/02/1980",
    "LOGRADOURO": "Rua do Matão",
    "NÚMERO": "1010",
    "COMPLEMENTO": "Bloco B",
    "BAIRRO": "Butantã",
    "CEP": "05508-090",
    "CIDADE": "São Paulo",
    "ESTADO": "SP",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)": "123.456.789-09",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)": "12.345.678-9",
    "NOME DO BANCO": "Banco do Brasil",
    "NÚMERO DA AGÊNCIA": "1234",
    "NÚMERO DA CONTA": "12345-6",
}


REQUIRED_TEACHER = {k: v for k, v in REQUIRED_STUDENT.items()}
REQUIRED_TEACHER.pop("NÍVEL")
REQUIRED_TEACHER.pop("TIPO DE AUXÍLIO")


def _prefix(tab):
    return "alunos" if tab == "ALUNOS" else "docentes"


def _valid_student_payload():
    return {"aba": "ALUNOS", **REQUIRED_STUDENT}


def _valid_teacher_payload():
    return {"aba": "DOCENTES", **REQUIRED_TEACHER}


def test_index_serve_cabecalho_e_duas_abas():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Universidade de São Paulo" in html
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert "Solicitação registrada" not in html


def test_assets_sao_servidos():
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200


def test_envio_aluno_gera_oficio():
    r = client.post("/solicitar", json=_valid_student_payload())
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    oficio = data["oficio"]
    assert "Maria da Silva" in oficio
    assert "12345678" in oficio
    assert "Maria da Silva" in oficio
    assert "maria@ime.usp.br" in oficio
    assert "Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Ciência da Computação - Mestrado" in oficio
    assert "Congresso de Computação" in oficio
    assert "10/10/2025 a 12/10/2025" in oficio
    assert "São Paulo - SP - Brasil" in oficio
    assert "https://evento.usp.br" in oficio
    assert "Pôster" in oficio
    assert "R$ 1.500,00" in oficio
    assert "Deslocamento e hospedagem." in oficio
    assert "Rua do Matão" in oficio
    assert "1010" in oficio
    assert "Bloco B" in oficio
    assert "05508-090" in oficio
    assert "Butantã" in oficio
    assert "01/02/1980" in oficio
    assert "123.456.789-09" in oficio
    assert "12.345.678-9" in oficio
    assert "Banco do Brasil" in oficio
    assert "1234" in oficio
    assert "12345-6" in oficio
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_envio_docente_gera_oficio_verbas():
    r = client.post("/solicitar", json=_valid_teacher_payload())
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    oficio = data["oficio"]
    assert "Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Ciência da Computação" in oficio


def test_docente_nao_exige_nivel_nem_tipo_auxilio():
    payload = _valid_teacher_payload()
    r = client.post("/solicitar", json=payload)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_link_do_evento_vazio_removido_do_oficio():
    payload = _valid_student_payload()
    payload["LINK DO EVENTO, EXAME OU DEFESA"] = ""
    r = client.post("/solicitar", json=payload)
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Link do evento:" not in oficio


def test_complemento_vazio_removido_do_oficio():
    payload = _valid_student_payload()
    payload["COMPLEMENTO"] = ""
    r = client.post("/solicitar", json=payload)
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Complemento:" not in oficio


def test_campo_obrigatorio_vazio_retorna_mensagem_unica():
    payload = _valid_student_payload()
    payload["CIDADE"] = ""
    payload["BAIRRO"] = ""
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    erros = data["erros"]
    assert "Preencha todos os campos" in erros
    assert erros.count("Preencha todos os campos") == 1


def test_valor_invalido():
    payload = _valid_student_payload()
    payload["VALOR SOLICITADO (R$)"] = "0"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "Valor solicitado deve ser maior que 0" in data["erros"]


def test_usp_nao_numerico():
    payload = _valid_student_payload()
    payload["N. USP"] = "12A34"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "N. USP deve conter apenas números" in data["erros"]


def test_agencia_nao_numerica():
    payload = _valid_student_payload()
    payload["NÚMERO DA AGÊNCIA"] = "12-34"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "Número da agência deve conter apenas números" in data["erros"]


def test_email_invalido():
    payload = _valid_student_payload()
    payload["E-MAIL"] = "maria"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "E-mail inválido" in data["erros"]


def test_cpf_fora_do_formato():
    payload = _valid_student_payload()
    payload["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "12345678909"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "CPF deve estar no formato 000.000.000-00" in data["erros"]


def test_cep_fora_do_formato():
    payload = _valid_student_payload()
    payload["CEP"] = "05508090"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "CEP deve estar no formato 00000-000" in data["erros"]


def test_data_fora_do_formato():
    payload = _valid_student_payload()
    payload["DATA DE NASCIMENTO"] = "01021980"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in data["erros"]


def test_cpf_invalido_digitos_verificadores():
    payload = _valid_student_payload()
    payload["CPF (SEPARADOS POR PONTOS E TRAÇO)"] = "123.456.789-00"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "CPF inválido" in data["erros"]


def test_data_inexistente():
    payload = _valid_student_payload()
    payload["DATA DE NASCIMENTO"] = "31/02/1980"
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "Data de nascimento inválida" in data["erros"]


def test_envio_invalido_nao_gera_oficio():
    payload = _valid_student_payload()
    payload["CIDADE"] = ""
    r = client.post("/solicitar", json=payload)
    data = r.json()
    assert data.get("ok") is False
    assert "oficio" not in data or data.get("oficio") is None
