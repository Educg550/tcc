import json

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_formatos_como_strings_sao_aceitos():
    # a API deve aceitar strings com digitos crus, como o front manda
    dados = {
        "aba": "alunos",
        "nome_completo": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nome_evento": "Congresso",
        "periodo": "10 a 12 de julho",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "",
        "valor_solicitado": "1500",
        "detalhamento": "Inscrição",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    r = client.post("/api/solicitacao", json=dados)
    assert r.status_code == 200
    body = r.json()
    assert body["valido"] is True
    assert "Valor solicitado: R$ 15,00" in body["oficio"]
