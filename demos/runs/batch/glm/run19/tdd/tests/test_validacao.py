"""Testes de validação do backend."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def dados_alunos_validos(**overrides):
    dados = {
        "tipo": "alunos",
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso de Matemática",
        "periodo": "10 a 15 de julho de 2024",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "",
        "valor": 100,
        "detalhamento": "Inscrição e transporte",
        "apresentacao": "Pôster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "529.982.247-25",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    dados.update(overrides)
    return dados


def dados_docentes_validos(**overrides):
    dados = dados_alunos_validos(tipo="docentes")
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    dados.update(overrides)
    return dados


def test_envio_valido_alunos_retorna_oficio():
    response = client.post("/solicitar", json=dados_alunos_validos())
    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is True
    assert "Solicitação registrada" in body.get("titulo", "")


def test_envio_valido_docentes_retorna_oficio():
    response = client.post("/solicitar", json=dados_docentes_validos())
    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is True


def test_campo_obrigatorio_vazio():
    response = client.post("/solicitar", json=dados_alunos_validos(nome=""))
    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is False
    erros = body.get("erros", [])
    assert "Preencha todos os campos" in erros


def test_campo_n_usp_invalido():
    response = client.post("/solicitar", json=dados_alunos_validos(n_usp="1234-5678"))
    body = response.json()
    assert body.get("ok") is False
    assert "N. USP deve conter apenas números" in body.get("erros", [])


def test_agencia_invalida():
    response = client.post("/solicitar", json=dados_alunos_validos(agencia="12.34"))
    body = response.json()
    assert body.get("ok") is False
    assert "Número da agência deve conter apenas números" in body.get("erros", [])


def test_valor_zero_ou_negativo():
    response = client.post("/solicitar", json=dados_alunos_validos(valor=0))
    body = response.json()
    assert body.get("ok") is False
    assert "Valor solicitado deve ser maior que 0" in body.get("erros", [])


def test_email_invalido():
    response = client.post("/solicitar", json=dados_alunos_validos(email="maria@"))
    body = response.json()
    assert body.get("ok") is False
    assert "E-mail inválido" in body.get("erros", [])

    response = client.post("/solicitar", json=dados_alunos_validos(email="maria"))
    body = response.json()
    assert body.get("ok") is False
    assert "E-mail inválido" in body.get("erros", [])


def test_cpf_formato_invalido():
    response = client.post("/solicitar", json=dados_alunos_validos(cpf="529.982.247-2X"))
    body = response.json()
    assert body.get("ok") is False
    assert "CPF deve estar no formato 000.000.000-00" in body.get("erros", [])


def test_cep_invalido():
    response = client.post("/solicitar", json=dados_alunos_validos(cep="05508-09"))
    body = response.json()
    assert body.get("ok") is False
    assert "CEP deve estar no formato 00000-000" in body.get("erros", [])


def test_data_nascimento_formato_invalido():
    response = client.post("/solicitar", json=dados_alunos_validos(nascimento="01-02-1980"))
    body = response.json()
    assert body.get("ok") is False
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in body.get("erros", [])


def test_cpf_digito_verificador_invalido():
    response = client.post("/solicitar", json=dados_alunos_validos(cpf="529.982.247-24"))
    body = response.json()
    assert body.get("ok") is False
    assert "CPF inválido" in body.get("erros", [])


def test_data_nascimento_inexistente():
    response = client.post("/solicitar", json=dados_alunos_validos(nascimento="31/02/1980"))
    body = response.json()
    assert body.get("ok") is False
    assert "Data de nascimento inválida" in body.get("erros", [])

    response = client.post("/solicitar", json=dados_alunos_validos(nascimento="01/13/1980"))
    body = response.json()
    assert body.get("ok") is False
    assert "Data de nascimento inválida" in body.get("erros", [])


def test_multiplos_erros_de_uma_vez():
    response = client.post(
        "/solicitar",
        json=dados_alunos_validos(
            n_usp="12a3",
            email="sem-arroba",
            cpf="123",
        ),
    )
    body = response.json()
    assert body.get("ok") is False
    erros = body.get("erros", [])
    assert "N. USP deve conter apenas números" in erros
    assert "E-mail inválido" in erros
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_link_e_complemento_opcionais():
    response = client.post("/solicitar", json=dados_alunos_validos(link="", complemento=""))
    body = response.json()
    assert body.get("ok") is True


def test_erros_docentes_mesma_validacao():
    response = client.post("/solicitar", json=dados_docentes_validos(n_usp="abc"))
    body = response.json()
    assert body.get("ok") is False
    assert "N. USP deve conter apenas números" in body.get("erros", [])
