from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


POST = {"nome": "Fulana da Silva", "numero_usp": "1234567", "programa": "Matemática",
        "nivel": "Mestrado", "tipo_auxilio": "Participação em evento", "email": "fulana@ime.usp.br",
        "evento": "Congresso de Matemática", "periodo": "10 a 12 de maio", "cidade": "São Paulo",
        "estado_evento": "SP", "pais": "Brasil", "link": "", "valor_centavos": 150000,
        "detalhamento": "Inscrição", "apresentacao": "Pôster", "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão", "numero": "1010", "complemento": "", "bairro": "Butantã",
        "cep": "05508-090", "cidade_endereco": "São Paulo", "estado_endereco": "SP",
        "cpf": "153.509.460-56", "rg": "12.345.678-9", "banco": "Banco do Brasil",
        "agencia": "1234", "conta": "12345-6"}


def test_sem_payload():
    r = client.post("/solicitacao")
    assert r.status_code == 422


def test_campos_vazios():
    dados = POST | {"nome": "", "email": "", "logradouro": ""}
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 422
    assert r.json()["erros"] == ["Preencha todos os campos"]


def test_todos_os_erros_juntos():
    dados = POST | {"numero_usp": "12a4", "agencia": "1a23", "valor_centavos": 0,
                    "email": "fulana", "cpf": "12345678900", "cep": "1234",
                    "data_nascimento": "01/13/1980"}
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 422
    assert r.json()["erros"] == ["Preencha todos os campos",
                                 "N. USP deve conter apenas números",
                                 "Número da agência deve conter apenas números",
                                 "Valor solicitado deve ser maior que 0",
                                 "E-mail inválido",
                                 "CPF deve estar no formato 000.000.000-00",
                                 "CEP deve estar no formato 00000-000",
                                 "Data de nascimento deve estar no formato dd/mm/aaaa"]


def test_cpf_com_dados_invalidos():
    dados = POST | {"cpf": "529.982.247-25"}
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 422
    assert r.json()["erros"] == ["CPF inválido"]


def test_data_inexistente():
    dados = POST | {"data_nascimento": "31/02/2001"}
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 422
    assert r.json()["erros"] == ["Data de nascimento inválida"]


def test_docente_com_campos_de_aluno_ignorados():
    dados = POST | {"aba": "docentes", "nivel": "Mestrado", "tipo_auxilio": "Participação em evento"}
    r = client.post("/solicitacao", json=dados)
    assert r.status_code == 200
