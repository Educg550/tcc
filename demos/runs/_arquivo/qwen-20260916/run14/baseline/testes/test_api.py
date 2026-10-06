from fastapi.testclient import TestClient

from app import app
from testes.test_oficio import BASE, aluno, docente


client = TestClient(app)


def test_aluno():
    r = client.post("/oficio", json=aluno().model_dump())
    assert r.status_code == 200
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in r.text
    assert "Preencha todos os campos" not in r.text


def test_docente():
    r = client.post("/oficio", json=docente().model_dump())
    assert r.status_code == 200
    assert "Verba do programa" in r.text


def test_erro():
    r = client.post("/oficio", json=aluno(nusp="abc").model_dump())
    assert r.status_code == 422
    assert r.text == "N. USP deve conter apenas números"


def test_estatico():
    assert client.get("/").status_code == 200
