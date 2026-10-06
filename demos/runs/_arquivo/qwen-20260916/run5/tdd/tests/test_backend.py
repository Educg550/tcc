from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

ALUNO_OK = {
    "aba": "alunos",
    "nome_completo": "Maria da Silva",
    "n_usp": "12345678",
    "programa": "Ciência da Computação",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@usp.br",
    "nome_evento": "SBIA",
    "periodo_evento": "01/01/2024 a 05/01/2024",
    "cidade_evento": "Campinas",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://sbia.org",
    "valor_solicitado": "R$ 1.500,00",
    "detalhamento": "Auxílio para participação",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua A",
    "numero": "100",
    "complemento": "Apto 1",
    "bairro": "Centro",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}


def test_oficio_alunos():
    r = client.post("/solicitacao", json=ALUNO_OK)
    assert r.status_code == 200
    t = r.json()["oficio"]
    for s in (
        "Maria da Silva - 12345678",
        "E-mail: maria@usp.br",
        "Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Ciência da Computação - Doutorado",
        "Evento: SBIA",
        "Período: 01/01/2024 a 05/01/2024",
        "Local: Campinas - SP - Brasil",
        "Link do evento: https://sbia.org",
        "Pôster",
        "R$ 1.500,00",
        "Apto 1",
        "05508-090",
        "Banco: Banco do Brasil",
        "Agência: 1234",
    ):
        assert s in t


def test_oficio_docentes():
    d = dict(ALUNO_OK)
    d["aba"] = "docentes"
    d.pop("nivel")
    d.pop("tipo_auxilio")
    r = client.post("/solicitacao", json=d)
    assert r.status_code == 200
    t = r.json()["oficio"]
    assert "Solicitação de Auxílio Financeiro - Verba do programa" in t
    assert "Programa: Ciência da Computação" in t
    assert "Doutorado" not in t


def test_linha_vazia_sai_do_oficio():
    d = dict(ALUNO_OK)
    d["link_evento"] = ""
    d["complemento"] = ""
    r = client.post("/solicitacao", json=d)
    assert r.status_code == 200
    t = r.json()["oficio"]
    assert "Link do evento:" not in t
    assert "Complemento:" not in t


def test_validacao():
    d = dict(ALUNO_OK)
    d["email"] = "semarroba"
    d["n_usp"] = "abc"
    r = client.post("/solicitacao", json=d)
    assert r.status_code == 400
    erros = r.json()["erros"]
    assert "E-mail inválido" in erros
    assert "N. USP deve conter apenas números" in erros


def test_omitir_obrigatorio():
    d = dict(ALUNO_OK)
    d["nome_completo"] = ""
    r = client.post("/solicitacao", json=d)
    assert r.status_code == 400
    assert "Preencha todos os campos" in r.json()["erros"]


def test_docentes_nao_pede_nivel():
    d = dict(ALUNO_OK)
    d["aba"] = "docentes"
    d.pop("nivel")
    d.pop("tipo_auxilio")
    r = client.post("/solicitacao", json=d)
    assert r.status_code == 200


