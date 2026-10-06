import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


def _base_aluno():
    return {
        "nome": "Maria Silva Santos",
        "nusp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Simpósio Brasileiro",
        "periodo": "10 a 15 de março de 2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://evento.usp.br",
        "valor": "R$ 1.500,00",
        "detalhamento": "Viagem e hospedagem",
        "apresentacao": "Apresentação oral",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "Sala 100",
        "bairro": "Butantã",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }


def _base_docente():
    d = _base_aluno()
    d.pop("nivel", None)
    d.pop("tipo_auxilio", None)
    return d


def _post(client, dados, aba="alunos"):
    return client.post(f"/api/solicitacao/{aba}", json=dados)


def _texto(resp):
    return resp.text


def test_envio_valido_aluno_gera_oficio(client):
    resp = _post(client, _base_aluno(), "alunos")
    assert resp.status_code == 200
    corpo = _texto(resp)
    assert "Interessada(o): Maria Silva Santos - 12345678" in corpo
    assert "E-mail: maria@ime.usp.br" in corpo
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in corpo
    assert "Programa: Ciência da Computação - Mestrado" in corpo
    assert "A CCP-Ciência da Computação aprovou" in corpo
    assert "Evento: Simpósio Brasileiro" in corpo
    assert "Local: São Paulo - SP - Brasil" in corpo
    assert "Link do evento: http://evento.usp.br" in corpo
    assert "Apresentação de trabalho: Apresentação oral" in corpo
    assert "Valor solicitado: R$ 1.500,00" in corpo
    assert "Complemento: Sala 100" in corpo
    assert "CEP: 05508-090" in corpo
    assert "CPF: 123.456.789-09" in corpo
    assert "Encaminhe-se ao Serviço Financeiro" in corpo.replace("para providências.", "")
    assert "Solicitação registrada" in corpo


def test_envio_valido_docente_usa_verba_do_programa(client):
    resp = _post(client, _base_docente(), "docentes")
    assert resp.status_code == 200
    corpo = _texto(resp)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in corpo
    assert "Programa: Ciência da Computação" in corpo
    assert "Programa: Ciência da Computação - Mestrado" not in corpo


def test_link_evento_vazio_sai_do_oficio(client):
    dados = _base_aluno()
    dados["link_evento"] = ""
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 200
    assert "Link do evento:" not in _texto(resp)


def test_complemento_vazio_sai_do_oficio(client):
    dados = _base_aluno()
    dados["complemento"] = ""
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 200
    assert "Complemento:" not in _texto(resp)


def test_campo_obrigatorio_vazio(client):
    dados = _base_aluno()
    dados["nome"] = ""
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    corpo = _texto(resp)
    assert "Preencha todos os campos" in corpo


def test_campo_obrigatorio_vazio_uma_unica_vez(client):
    dados = _base_aluno()
    dados["nome"] = ""
    dados["programa"] = ""
    dados["banco"] = ""
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert _texto(resp).count("Preencha todos os campos") == 1


def test_nusp_nao_numerico(client):
    dados = _base_aluno()
    dados["nusp"] = "12abc678"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "N. USP deve conter apenas números" in _texto(resp)


def test_agencia_nao_numerica(client):
    dados = _base_aluno()
    dados["agencia"] = "12a4"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "Número da agência deve conter apenas números" in _texto(resp)


def test_valor_zero(client):
    dados = _base_aluno()
    dados["valor"] = "R$ 0,00"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "Valor solicitado deve ser maior que 0" in _texto(resp)


def test_email_invalido(client):
    dados = _base_aluno()
    dados["email"] = "maria-ime.usp.br"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "E-mail inválido" in _texto(resp)


def test_cpf_formato_invalido(client):
    dados = _base_aluno()
    dados["cpf"] = "12345678909"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "CPF deve estar no formato 000.000.000-00" in _texto(resp)


def test_cep_formato_invalido(client):
    dados = _base_aluno()
    dados["cep"] = "05508090"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "CEP deve estar no formato 00000-000" in _texto(resp)


def test_data_nascimento_formato_invalido(client):
    dados = _base_aluno()
    dados["data_nascimento"] = "01021980"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _texto(resp)


def test_cpf_digitos_verificadores_invalidos(client):
    dados = _base_aluno()
    dados["cpf"] = "123.456.789-00"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "CPF inválido" in _texto(resp)


def test_data_nascimento_inexistente(client):
    dados = _base_aluno()
    dados["data_nascimento"] = "31/02/1980"
    resp = _post(client, dados, "alunos")
    assert resp.status_code == 422
    assert "Data de nascimento inválida" in _texto(resp)


def test_erro_nao_gera_oficio(client):
    dados = _base_aluno()
    dados["nome"] = ""
    resp = _post(client, dados, "alunos")
    assert "Interessada(o):" not in _texto(resp)


def test_varias_mensagens_de_erro(client):
    dados = _base_aluno()
    dados["nusp"] = "12abc"
    dados["email"] = "invalido"
    resp = _post(client, dados, "alunos")
    corpo = _texto(resp)
    assert "N. USP deve conter apenas números" in corpo
    assert "E-mail inválido" in corpo
