import pytest

from tests.test_api import VALID_ALUNOS


def test_error_messages_acentos(client):
    expected = {
        "N. USP deve conter apenas números": {**VALID_ALUNOS, "nusp": "12a45678"},
        "Número da agência deve conter apenas números": {**VALID_ALUNOS, "agencia": "12a4"},
        "Data de nascimento deve estar no formato dd/mm/aaaa": {**VALID_ALUNOS, "data_nascimento": "01-02-1980"},
    }
    for msg, payload in expected.items():
        r = client.post("/solicitacao", json={"aba": "alunos", **payload})
        assert r.status_code == 422, (msg, r.text)
        assert msg in r.text, (msg, r.text)


def test_oficio_acentos(client):
    r = client.post("/solicitacao", json={"aba": "alunos", **VALID_ALUNOS})
    assert r.status_code == 200, r.text
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro" in oficio
