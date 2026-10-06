"""A API valida a solicitação e devolve as mensagens de erro na ordem."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def _ok(overrides=None, aba="alunos"):
    dados = {
        "nomeCompleto": "Maria da Silva",
        "numeroUsp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipoAuxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "nomeEvento": "Congresso Nacional",
        "periodo": "10 a 12 de outubro de 2025",
        "cidadeEvento": "São Paulo",
        "estadoEvento": "SP",
        "paisEvento": "Brasil",
        "linkEvento": "",
        "valorSolicitado": "R$ 1.500,00",
        "detalhamento": "Passagem aérea",
        "apresentacao": "Pôster",
        "dataNascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numeroEndereco": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "nomeBanco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }
    if aba == "docentes":
        dados.pop("nivel")
        dados.pop("tipoAuxilio")
    if overrides:
        dados.update(overrides)
    return dados


def _post(dados, aba="alunos"):
    return client.post("/api/solicitar/" + aba, json=dados)


def test_solicitacao_valida_alunos():
    r = _post(_ok())
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert r.json()["erros"] == []


def test_solicitacao_valida_docentes():
    r = _post(_ok(aba="docentes"), aba="docentes")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_campo_obrigatorio_vazio():
    r = _post(_ok({"nomeCompleto": ""}))
    assert r.status_code == 400
    assert r.json()["erros"] == ["Preencha todos os campos"]


def test_numero_usp_com_letras():
    r = _post(_ok({"numeroUsp": "12345abc"}))
    assert r.json()["erros"] == ["N. USP deve conter apenas números"]


def test_agencia_com_letras():
    r = _post(_ok({"agencia": "12a3"}))
    assert r.json()["erros"] == ["Número da agência deve conter apenas números"]


def test_valor_zero():
    r = _post(_ok({"valorSolicitado": "R$ 0,00"}))
    assert r.json()["erros"] == ["Valor solicitado deve ser maior que 0"]


def test_email_invalido():
    r = _post(_ok({"email": "maria"}))
    assert r.json()["erros"] == ["E-mail inválido"]


def test_cpf_formato_errado():
    r = _post(_ok({"cpf": "12345678909"}))
    assert r.json()["erros"] == ["CPF deve estar no formato 000.000.000-00"]


def test_cpf_verificador_errado():
    r = _post(_ok({"cpf": "123.456.789-00"}))
    assert r.json()["erros"] == ["CPF inválido"]


def test_cep_formato_errado():
    r = _post(_ok({"cep": "05508090"}))
    assert r.json()["erros"] == ["CEP deve estar no formato 00000-000"]


def test_data_formato_errado():
    r = _post(_ok({"dataNascimento": "1980-02-01"}))
    assert r.json()["erros"] == ["Data de nascimento deve estar no formato dd/mm/aaaa"]


def test_data_inexistente():
    r = _post(_ok({"dataNascimento": "31/02/1980"}))
    assert r.json()["erros"] == ["Data de nascimento inválida"]


def test_multiplos_erros():
    r = _post(_ok({"email": "maria", "cpf": "12345678909", "cep": "05508090"}))
    assert r.json()["erros"] == [
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
    ]


def test_alunos_sem_nivel_ou_tipo_e_erro():
    dados = _ok()
    dados.pop("nivel")
    r = _post(dados)
    assert r.json()["erros"] == ["Preencha todos os campos"]


def test_docentes_com_nivel_nao_dá_erro():
    dados = _ok(aba="docentes")
    dados["nivel"] = "Mestrado"
    r = _post(dados, aba="docentes")
    assert r.json()["ok"] is True
