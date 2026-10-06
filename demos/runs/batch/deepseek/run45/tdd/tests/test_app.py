import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


@pytest.fixture
def valid_student_data():
    return {
        "nome_completo": "João da Silva",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "joao@example.com",
        "nome_evento": "Congresso de Computação",
        "periodo_evento": "10/10/2024 a 15/10/2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://evento.com",
        "valor_solicitado": "150000",
        "detalhamento": "Participação no evento",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua Exemplo",
        "numero": "123",
        "complemento": "Apto 4",
        "bairro": "Centro",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "12345678909",
        "rg": "1234567",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }


def test_index_has_two_tabs(valid_student_data):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.index("ALUNOS") < html.index("DOCENTES")


def test_alunos_tab_active_by_default():
    resp = client.get("/")
    assert 'id="tab-alunos" class="active"' in resp.text or 'class="tab active"' in resp.text


def test_student_fields_required(valid_student_data):
    data = valid_student_data.copy()
    del data["nivel"]
    del data["tipo_auxilio"]
    resp = client.post("/solicitar/alunos", data=data)
    assert resp.status_code == 200


def test_docente_form_lacks_nivel_and_tipo(valid_student_data):
    data = valid_student_data.copy()
    del data["nivel"]
    del data["tipo_auxilio"]
    resp = client.post("/solicitar/docentes", data=data)
    assert resp.status_code == 200


def test_required_field_empty(valid_student_data):
    data = valid_student_data.copy()
    data["nome_completo"] = ""
    resp = client.post("/solicitar/alunos", data=data)
    assert "Preencha todos os campos" in resp.text


def test_n_usp_not_digits(valid_student_data):
    data = valid_student_data.copy()
    data["n_usp"] = "123abc"
    resp = client.post("/solicitar/alunos", data=data)
    assert "N. USP deve conter apenas números" in resp.text


def test_agencia_not_digits(valid_student_data):
    data = valid_student_data.copy()
    data["agencia"] = "12ab"
    resp = client.post("/solicitar/alunos", data=data)
    assert "Número da agência deve conter apenas números" in resp.text


def test_valor_invalido(valid_student_data):
    data = valid_student_data.copy()
    data["valor_solicitado"] = "0"
    resp = client.post("/solicitar/alunos", data=data)
    assert "Valor solicitado deve ser maior que 0" in resp.text


def test_email_invalido(valid_student_data):
    data = valid_student_data.copy()
    data["email"] = "joaoexample.com"
    resp = client.post("/solicitar/alunos", data=data)
    assert "E-mail inválido" in resp.text


def test_cpf_formato_invalido(valid_student_data):
    data = valid_student_data.copy()
    data["cpf"] = "1234567890"
    resp = client.post("/solicitar/alunos", data=data)
    assert "CPF deve estar no formato 000.000.000-00" in resp.text


def test_cep_formato_invalido(valid_student_data):
    data = valid_student_data.copy()
    data["cep"] = "1234567"
    resp = client.post("/solicitar/alunos", data=data)
    assert "CEP deve estar no formato 00000-000" in resp.text


def test_data_formato_invalido(valid_student_data):
    data = valid_student_data.copy()
    data["data_nascimento"] = "1980-02-01"
    resp = client.post("/solicitar/alunos", data=data)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in resp.text


def test_cpf_digitos_verificadores_invalidos(valid_student_data):
    data = valid_student_data.copy()
    data["cpf"] = "11111111111"
    resp = client.post("/solicitar/alunos", data=data)
    assert "CPF inválido" in resp.text


def test_data_inexistente(valid_student_data):
    data = valid_student_data.copy()
    data["data_nascimento"] = "31/02/1980"
    resp = client.post("/solicitar/alunos", data=data)
    assert "Data de nascimento inválida" in resp.text


def test_erros_multiplos(valid_student_data):
    data = valid_student_data.copy()
    data["nome_completo"] = ""
    data["n_usp"] = "abc"
    data["email"] = "invalido"
    resp = client.post("/solicitar/alunos", data=data)
    assert "Preencha todos os campos" in resp.text
    assert "N. USP deve conter apenas números" in resp.text
    assert "E-mail inválido" in resp.text


def test_envio_valido_gera_oficio(valid_student_data):
    resp = client.post("/solicitar/alunos", data=valid_student_data)
    assert "Solicitação registrada" in resp.text
    assert "João da Silva - 12345678" in resp.text
    assert "joao@example.com" in resp.text
    assert "Solicitação de Auxílio Financeiro - Participação em evento" in resp.text
    assert "Ciência da Computação - Mestrado" in resp.text
    assert "Congresso de Computação" in resp.text
    assert "10/10/2024 a 15/10/2024" in resp.text
    assert "São Paulo - SP - Brasil" in resp.text
    assert "http://evento.com" in resp.text
    assert "Pôster" in resp.text
    assert "R$ 1.500,00" in resp.text
    assert "Rua Exemplo, 123" in resp.text
    assert "Apto 4" in resp.text
    assert "05508-090" in resp.text
    assert "Centro, São Paulo - SP" in resp.text
    assert "01/02/1980" in resp.text
    assert "123.456.789-09" in resp.text
    assert "Banco do Brasil" in resp.text
    assert "1234" in resp.text
    assert "56789-0" in resp.text


def test_link_e_complemento_opcionais(valid_student_data):
    data = valid_student_data.copy()
    data["link_evento"] = ""
    data["complemento"] = ""
    resp = client.post("/solicitar/alunos", data=data)
    assert "Link do evento:" not in resp.text
    assert "Complemento:" not in resp.text


def test_docente_oficio_diferente(valid_student_data):
    data = valid_student_data.copy()
    del data["nivel"]
    del data["tipo_auxilio"]
    resp = client.post("/solicitar/docentes", data=data)
    assert "Solicitação registrada" in resp.text
    assert "Solicitação de Auxílio Financeiro - Verba do programa" in resp.text
    assert "Programa: Ciência da Computação" in resp.text


def test_formatacao_valor_cpf_cep_data(valid_student_data):
    data = valid_student_data.copy()
    data["valor_solicitado"] = "150000000"
    data["cpf"] = "12345678909"
    data["cep"] = "05508090"
    data["data_nascimento"] = "01021980"
    resp = client.post("/solicitar/alunos", data=data)
    assert "R$ 1.500.000,00" in resp.text
    assert "123.456.789-09" in resp.text
    assert "05508-090" in resp.text
    assert "01/02/1980" in resp.text
