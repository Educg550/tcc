from fastapi.testclient import TestClient

from app import app


def postar(dados, aba="alunos"):
    return TestClient(app).post("/api/validar", json={"aba": aba, "dados": dados})


def test_alunos_todos_campos_validos():
    dados = {
        "nome_completo": "Maria da Silva",
        "n_usp": "1234567",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso de Matemática",
        "periodo": "10 a 12 de julho",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com",
        "valor": "150000",
        "detalhamento": "Passagem e hospedagem",
        "apresentacao": "Pôster",
        "nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "12345678909",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    resposta = postar(dados)
    assert resposta.status_code == 200
    assert resposta.json()["valido"] is True
