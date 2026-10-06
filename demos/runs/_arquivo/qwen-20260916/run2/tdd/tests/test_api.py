from tests.conftest import find_tag

import pytest

VALID_ALUNOS = {
    "nome_completo": "Maria Silva",
    "nusp": "12345678",
    "programa": "Matematica",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participacao em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "XVI Congreso",
    "periodo_evento": "01/01/2026 a 05/01/2026",
    "cidade_evento": "Buenos Aires",
    "estado_evento": "Buenos Aires",
    "pais_evento": "Argentina",
    "link_evento": "http://exemplo.org",
    "valor_solicitado": 150000,
    "detalhamento": "Solicito ajuda para participar do congresso",
    "apresenta_trabalho": "Poster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matao",
    "numero": "101",
    "complemento": "Apto 2",
    "bairro": "Butanta",
    "cep": "05508-090",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

VALID_DOCENTES = {
    "nome_completo": "Joao Souza",
    "nusp": "87654321",
    "programa": "Fisica",
    "email": "joao@ime.usp.br",
    "nome_evento": "Coloquio",
    "periodo_evento": "10/03/2026",
    "cidade_evento": "Sao Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "valor_solicitado": 150000,
    "detalhamento": "Participacao em banca",
    "apresenta_trabalho": "Poster",
    "data_nascimento": "15/06/1975",
    "logradouro": "Rua da Prata",
    "numero": "20",
    "bairro": "Centro",
    "cep": "01000-000",
    "cidade": "Sao Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "98.765.432-1",
    "banco": "Itau",
    "agencia": "0001",
    "conta": "11111-1",
}


def test_valid_submission_returns_200(client):
    r = client.post("/solicitacao", json={"aba": "alunos", **VALID_ALUNOS})
    assert r.status_code == 200, r.text


def test_invalid_field_returns_422(client):
    r = client.post("/solicitacao", json={"aba": "alunos", **{**VALID_ALUNOS, "nome_completo": ""}})
    assert r.status_code == 422, r.text


def test_malformed_body_returns_400(client):
    r = client.post("/solicitacao", content="oi", headers={"Content-Type": "text/plain"})
    assert r.status_code == 400, r.text


def test_error_messages(client):
    expected = {
        "Preencha todos os campos": {**VALID_ALUNOS, "programa": ""},
        "N. USP deve conter apenas numeros": {**VALID_ALUNOS, "nusp": "12a45678"},
        "Numero da agencia deve conter apenas numeros": {**VALID_ALUNOS, "agencia": "12a4"},
        "Valor solicitado deve ser maior que 0": {**VALID_ALUNOS, "valor_solicitado": 0},
        "E-mail invalido": {**VALID_ALUNOS, "email": "sem-arroba"},
        "CPF deve estar no formato 000.000.000-00": {**VALID_ALUNOS, "cpf": "12345678909"},
        "CEP deve estar no formato 00000-000": {**VALID_ALUNOS, "cep": "05508090"},
        "Data de nascimento deve estar no formato dd/mm/aaaa": {**VALID_ALUNOS, "data_nascimento": "01-02-1980"},
        "CPF invalido": {**VALID_ALUNOS, "cpf": "123.456.789-00"},
        "Data de nascimento invalida": {**VALID_ALUNOS, "data_nascimento": "31/02/1980"},
    }
    for msg, payload in expected.items():
        r = client.post("/solicitacao", json={"aba": "alunos", **payload})
        assert r.status_code == 422, (msg, r.text)
        assert msg in r.text, (msg, r.text)


def test_all_errors_at_once(client):
    empty = {k: "" for k in VALID_ALUNOS}
    r = client.post("/solicitacao", json={"aba": "alunos", **empty})
    assert r.status_code == 422, r.text
    assert "Preencha todos os campos" in r.text


def test_oficio_alunos(client):
    r = client.post("/solicitacao", json={"aba": "alunos", **VALID_ALUNOS})
    assert r.status_code == 200, r.text
    oficio = r.json()["oficio"]
    assert "Interessada(o): Maria Silva - 12345678" in oficio
    assert "E-mail: maria@ime.usp.br" in oficio
    assert "Assunto: Solicitacao de Auxilio Financeiro - Participacao em evento" in oficio
    assert "Programa: Matematica - Doutorado" in oficio
    assert "Evento: XVI Congreso" in oficio
    assert "Link do evento: http://exemplo.org" in oficio
    assert "Valor solicitado: R$ 1.500,00" in oficio
    assert "Complemento: Apto 2" in oficio
    assert "Encaminhe-se ao Servico Financeiro para providencias." in oficio


def test_oficio_alunos_sem_link_e_complemento(client):
    r = client.post("/solicitacao", json={"aba": "alunos", **{**VALID_ALUNOS, "link_evento": "", "complemento": ""}})
    assert r.status_code == 200, r.text
    oficio = r.json()["oficio"]
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio


def test_oficio_docentes(client):
    r = client.post("/solicitacao", json={"aba": "docentes", **VALID_DOCENTES})
    assert r.status_code == 200, r.text
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitacao de Auxilio Financeiro - Verba do programa" in oficio
    assert "Programa: Fisica" in oficio
    assert "Doutorado" not in oficio


def test_valor_solicitado_acima_do_limite(client):
    r = client.post("/solicitacao", json={"aba": "alunos", **{**VALID_ALUNOS, "valor_solicitado": 999999999}})
    assert r.status_code == 422, r.text
    assert "Valor solicitado deve ser maior que 0" in r.text
