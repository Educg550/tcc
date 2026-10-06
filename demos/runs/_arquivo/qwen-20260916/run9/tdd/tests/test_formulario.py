import re
import pytest
from fastapi.testclient import TestClient

try:
    from app import app
except ImportError:
    app = None

if app is not None:
    client = TestClient(app)
else:
    client = None


BASE_STUDENT = {
    "aba": "ALUNOS",
    "nome_completo": "Maria da Silva",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "SBC",
    "periodo_evento": "01/10/2023 a 05/10/2023",
    "cidade_evento": "Rio de Janeiro",
    "estado_evento": "RJ",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor_solicitado": "150000",
    "detalhamento": "Detalhes aqui",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Av. Prof. Luciano Gualberto",
    "numero": "374",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "123456789",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "123456",
}

BASE_TEACHER = {
    "aba": "DOCENTES",
    "nome_completo": "João da Silva",
    "n_usp": "1234567",
    "programa": "Ciência da Computação",
    "email": "joao@ime.usp.br",
    "nome_evento": "SBC",
    "periodo_evento": "01/10/2023 a 05/10/2023",
    "cidade_evento": "Rio de Janeiro",
    "estado_evento": "RJ",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor_solicitado": "150000",
    "detalhamento": "Detalhes aqui",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Av. Prof. Luciano Gualberto",
    "numero": "374",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "123456789",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "123456",
}


def _post(data):
    if client is None:
        pytest.skip("app not importable")
    return client.post("/solicitar", json=data)


@pytest.fixture(autouse=True)
def check_app():
    if client is None:
        pytest.skip("app not importable")


def test_get():
    r = client.get("/")
    assert r.status_code == 200


def test_valid_student():
    r = _post(BASE_STUDENT)
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert "erros" in j
    assert j["erros"] == []
    assert "oficio" in j
    assert isinstance(j["oficio"], str)


def test_valid_teacher():
    r = _post(BASE_TEACHER)
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert "erros" in j
    assert j["erros"] == []
    assert "oficio" in j
    assert isinstance(j["oficio"], str)


def test_student_no_level_and_type():
    d = dict(BASE_STUDENT)
    d["nivel"] = ""
    d["tipo_auxilio"] = ""
    r = _post(d)
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert "erros" in j
    assert "Preencha todos os campos" in j["erros"]


def test_teacher_no_level_and_type():
    d = dict(BASE_TEACHER)
    d["nivel"] = ""
    d["tipo_auxilio"] = ""
    r = _post(d)
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j, dict)
    assert "erros" in j
    assert "Preencha todos os campos" in j["erros"]


def test_valid_email():
    d = dict(BASE_STUDENT)
    d["email"] = "x@y.z"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "E-mail inválido" not in j["erros"]

    d = dict(BASE_STUDENT)
    d["email"] = "bad"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "E-mail inválido" in j["erros"]

    d = dict(BASE_STUDENT)
    d["email"] = "@y.z"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "E-mail inválido" in j["erros"]


def test_cpf_format():
    d = dict(BASE_STUDENT)
    d["cpf"] = "12345678909"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "CPF deve estar no formato 000.000.000-00" in j["erros"]


def test_cpf_check_digits():
    d = dict(BASE_STUDENT)
    d["cpf"] = "123.456.789-00"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "CPF inválido" in j["erros"]


def test_cep_format():
    d = dict(BASE_STUDENT)
    d["cep"] = "05508090"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "CEP deve estar no formato 00000-000" in j["erros"]


def test_data_format():
    d = dict(BASE_STUDENT)
    d["data_nascimento"] = "01021980"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in j["erros"]


def test_data_invalid():
    d = dict(BASE_STUDENT)
    d["data_nascimento"] = "29/02/2021"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Data de nascimento inválida" in j["erros"]

    d = dict(BASE_STUDENT)
    d["data_nascimento"] = "13/13/1980"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Data de nascimento inválida" in j["erros"]


def test_nusp_format():
    d = dict(BASE_STUDENT)
    d["n_usp"] = "abc"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "N. USP deve conter apenas números" in j["erros"]


def test_agencia_format():
    d = dict(BASE_STUDENT)
    d["agencia"] = "abc"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Número da agência deve conter apenas números" in j["erros"]


def test_valor_format():
    d = dict(BASE_STUDENT)
    d["valor_solicitado"] = "-5"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Valor solicitado deve ser maior que 0" in j["erros"]


def test_valor_invalid_string():
    d = dict(BASE_STUDENT)
    d["valor_solicitado"] = "abc"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Valor solicitado deve ser maior que 0" in j["erros"]


def test_valor_zero():
    d = dict(BASE_STUDENT)
    d["valor_solicitado"] = "0"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "Valor solicitado deve ser maior que 0" in j["erros"]


def test_optional_fields():
    d = dict(BASE_STUDENT)
    d["link_evento"] = ""
    d["complemento"] = ""
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "erros" in j
    assert j["erros"] == []


def test_oficio_content():
    r = _post(BASE_STUDENT)
    j = r.json()
    assert isinstance(j, dict)
    assert "oficio" in j
    o = j["oficio"]
    assert "Maria da Silva" in o
    assert "1234567" in o
    assert "Ciência da Computação" in o
    assert "Mestrado" in o
    assert "Participação em evento" in o
    assert "SBC" in o
    assert "R$ 1.500,00" in o
    assert "123.456.789-09" in o
    assert "05508-090" in o


def test_oficio_teacher():
    r = _post(BASE_TEACHER)
    j = r.json()
    assert isinstance(j, dict)
    assert "oficio" in j
    o = j["oficio"]
    assert "João da Silva" in o
    assert "Verba do programa" in o
    assert "Ciência da Computação" in o
    assert "Mestrado" not in o
    assert "Participação em evento" not in o


def test_oficio_lines():
    r = _post(BASE_STUDENT)
    j = r.json()
    assert isinstance(j, dict)
    assert "oficio" in j
    o = j["oficio"]
    assert "Interessada(o): Maria da Silva - 1234567" in o
    assert "E-mail: maria@ime.usp.br" in o
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in o
    assert "Programa: Ciência da Computação - Mestrado" in o
    assert "A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a" in o
    assert "interessada(o) acima, conforme segue:" in o
    assert "Dados do evento" in o
    assert "Evento: SBC" in o
    assert "Período: 01/10/2023 a 05/10/2023" in o
    assert "Local: Rio de Janeiro - RJ - Brasil" in o
    assert "Link do evento:" not in o
    assert "Apresentação de trabalho: Pôster" in o
    assert "Valor solicitado: R$ 1.500,00" in o
    assert "Detalhamento: Detalhes aqui" in o
    assert "Endereço da(o) interessada(o)" in o
    assert "Av. Prof. Luciano Gualberto, 374" in o
    assert "Complemento:" not in o
    assert "CEP: 05508-090" in o
    assert "Butantã, São Paulo - SP" in o
    assert "Dados para pagamento" in o
    assert "Data de nascimento: 01/02/1980" in o
    assert "CPF: 123.456.789-09" in o
    assert "RG / RNM: 123456789" in o
    assert "Banco: Banco do Brasil" in o
    assert "Agência: 1234" in o
    assert "Conta: 123456" in o
    assert "Encaminhe-se ao Serviço Financeiro para providências." in o


def test_oficio_link():
    d = dict(BASE_STUDENT)
    d["link_evento"] = "http://sbc.org.br"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "oficio" in j
    assert "Link do evento: http://sbc.org.br" in j["oficio"]


def test_oficio_complemento():
    d = dict(BASE_STUDENT)
    d["complemento"] = "Sala 10"
    r = _post(d)
    j = r.json()
    assert isinstance(j, dict)
    assert "oficio" in j
    assert "Complemento: Sala 10" in j["oficio"]


def test_oficio_teacher_lines():
    r = _post(BASE_TEACHER)
    j = r.json()
    assert isinstance(j, dict)
    assert "oficio" in j
    o = j["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in o
    assert "Programa: Ciência da Computação" in o
    assert " - Mestrado" not in o


def test_static_index():
    r = client.get("/index.html")
    assert r.status_code == 200
    t = r.text
    assert "ALUNOS" in t
    assert "DOCENTES" in t

    # check blocks
    for b in ["SOLICITANTE E EVENTO", "ENDEREÇO DO SOLICITANTE", "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO"]:
        assert b in t

    # check labels in order
    labels = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "NÍVEL",
        "TIPO DE AUXÍLIO",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
    ]
    for l in labels:
        assert l in t

    # order of labels
    idx = [t.index(l) for l in labels]
    assert idx == sorted(idx)

    assert "Mestrado" in t
    assert "Doutorado" in t
    assert "Participação em evento" in t
    assert "Banca de exame ou defesa" in t
    assert "Outro" in t
    assert "Pôster" in t
    assert "Apresentação oral" in t
    assert "Não irá apresentar trabalho" in t
    assert "Enviar solicitação" in t
    assert "Universidade de São Paulo" in t


def test_static_style():
    r = client.get("/style.css")
    assert r.status_code == 200
    c = r.text
    assert "#1094ab" in c
    assert "#64c4d2" in c
    assert "#fcb421" in c


def test_static_app():
    r = client.get("/app.js")
    assert r.status_code == 200
    c = r.text
    assert "format" in c.lower()


def test_static_asset():
    r = client.get("/assets/usp-logo.png")
    assert r.status_code == 200
