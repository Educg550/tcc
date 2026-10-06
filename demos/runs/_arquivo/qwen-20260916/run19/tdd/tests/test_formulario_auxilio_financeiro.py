import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


ALUNOS = {
    "nome_completo": "Maria Silva Souza",
    "nusp": "1234567",
    "programa": "Ciência da Computação",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria.silva@ime.usp.br",
    "nome_evento": "XXII Conferência Internacional de Computação",
    "periodo_evento": "10 a 14 de julho de 2026",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://example.com/evento",
    "valor_solicitado": "1500.00",
    "detalhamento": "Participação como ouvinte na conferência principal.",
    "apresentar_trabalho": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Apto 501",
    "bairro": "Cidade Universitária",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "nome_banco": "Banco do Brasil",
    "numero_agencia": "1234",
    "numero_conta": "56789-0",
}

DOCENTES = {
    "nome_completo": "João Oliveira",
    "nusp": "7654321",
    "programa": "Matemática",
    "email": "joao.oliveira@ime.usp.br",
    "nome_evento": "Colóquio de Matemática",
    "periodo_evento": "01 a 05 de agosto de 2026",
    "cidade_evento": "Rio de Janeiro",
    "estado_evento": "RJ",
    "pais_evento": "Brasil",
    "link_evento": "https://example.com/coloquio",
    "valor_solicitado": "2500.00",
    "detalhamento": "Organização e participação no colóquio.",
    "apresentar_trabalho": "Apresentação oral",
    "data_nascimento": "15/03/1975",
    "logradouro": "Av. Prof. Almeida Prado",
    "numero": "532",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "11.222.333-4",
    "nome_banco": "Caixa Econômica Federal",
    "numero_agencia": "4321",
    "numero_conta": "10000-1",
}


def _payload(aba, base=None, overrides=None):
    if base is None:
        base = ALUNOS if aba == "alunos" else DOCENTES

    if aba == "alunos":
        data = {
            "aba": "alunos",
            "nome_completo": base["nome_completo"],
            "nusp": base["nusp"],
            "programa": base["programa"],
            "nivel": base["nivel"],
            "tipo_auxilio": base["tipo_auxilio"],
            "email": base["email"],
            "nome_evento": base["nome_evento"],
            "periodo_evento": base["periodo_evento"],
            "cidade_evento": base["cidade_evento"],
            "estado_evento": base["estado_evento"],
            "pais_evento": base["pais_evento"],
            "link_evento": base["link_evento"],
            "valor_solicitado": base["valor_solicitado"],
            "detalhamento": base["detalhamento"],
            "apresentar_trabalho": base["apresentar_trabalho"],
            "data_nascimento": base["data_nascimento"],
            "logradouro": base["logradouro"],
            "numero": base["numero"],
            "complemento": base["complemento"],
            "bairro": base["bairro"],
            "cep": base["cep"],
            "cidade": base["cidade"],
            "estado": base["estado"],
            "cpf": base["cpf"],
            "rg_rnm": base["rg_rnm"],
            "nome_banco": base["nome_banco"],
            "numero_agencia": base["numero_agencia"],
            "numero_conta": base["numero_conta"],
        }
    else:
        data = {
            "aba": "docentes",
            "nome_completo": base["nome_completo"],
            "nusp": base["nusp"],
            "programa": base["programa"],
            "email": base["email"],
            "nome_evento": base["nome_evento"],
            "periodo_evento": base["periodo_evento"],
            "cidade_evento": base["cidade_evento"],
            "estado_evento": base["estado_evento"],
            "pais_evento": base["pais_evento"],
            "link_evento": base["link_evento"],
            "valor_solicitado": base["valor_solicitado"],
            "detalhamento": base["detalhamento"],
            "apresentar_trabalho": base["apresentar_trabalho"],
            "data_nascimento": base["data_nascimento"],
            "logradouro": base["logradouro"],
            "numero": base["numero"],
            "complemento": base["complemento"],
            "bairro": base["bairro"],
            "cep": base["cep"],
            "cidade": base["cidade"],
            "estado": base["estado"],
            "cpf": base["cpf"],
            "rg_rnm": base["rg_rnm"],
            "nome_banco": base["nome_banco"],
            "numero_agencia": base["numero_agencia"],
            "numero_conta": base["numero_conta"],
        }

    if overrides:
        data.update(overrides)

    return data


def _errors(client, payload):
    r = client.post("/solicitacao", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "errors" in body
    return body.get("errors", [])


def _has_error(errors, msg):
    return any(msg in e for e in errors)


def test_get_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/index.html",
        "/style.css",
        "/app.js",
        "/assets/usp-logo.png",
    ],
)
def test_static_files_available(client, path):
    r = client.get(path)
    assert r.status_code == 200


def test_index_has_exact_labels(client):
    r = client.get("/")
    html = r.text

    for label in [
        "ALUNOS",
        "DOCENTES",
        "SOLICITANTE E EVENTO",
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
        "ENDEREÇO DO SOLICITANTE",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NÚMERO",
        "COMPLEMENTO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
        "CPF (SEPARADOS POR PONTOS E TRAÇO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
        "NOME DO BANCO",
        "NÚMERO DA AGÊNCIA",
        "NÚMERO DA CONTA",
        "Enviar solicitação",
        "Mestrado",
        "Doutorado",
        "Participação em evento",
        "Banca de exame ou defesa",
        "Outro",
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ]:
        assert label in html


def test_appjs_contains_all_error_messages(client):
    r = client.get("/app.js")
    js = r.text

    for msg in [
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
        "CPF inválido",
        "Data de nascimento inválida",
        "Solicitação registrada",
    ]:
        assert msg in js


def test_css_contains_usp_colors_and_font(client):
    r = client.get("/style.css")
    css = r.text

    assert "#1094ab" in css
    assert "#64c4d2" in css
    assert "#fcb421" in css
    assert "Open Sans" in css


def test_valid_alunos_returns_officio(client):
    payload = _payload("alunos")
    r = client.post("/solicitacao", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body.get("errors", []) == []

    of = body["oficio"]
    assert "Solicitação registrada" in body
    assert "Assunto: Solicitação de Auxílio Financeiro - " + payload["tipo_auxilio"] in of
    assert "Programa: " + payload["programa"] + " - " + payload["nivel"] in of
    assert "R$ 1.500,00" in of


def test_valid_docentes_returns_officio(client):
    payload = _payload("docentes")
    r = client.post("/solicitacao", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body.get("errors", []) == []

    of = body["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in of
    assert "Programa: " + payload["programa"] in of
    assert "R$ 2.500,00" in of
    assert "Complemento" not in of


@pytest.mark.parametrize(
    "aba, field",
    [
        ("alunos", "nome_completo"),
        ("alunos", "nusp"),
        ("alunos", "programa"),
        ("alunos", "email"),
        ("alunos", "nome_evento"),
        ("alunos", "data_nascimento"),
        ("docentes", "nome_completo"),
        ("docentes", "nusp"),
    ],
)
def test_empty_required_field_triggers_fill_all(client, aba, field):
    errors = _errors(client, _payload(aba, overrides={field: ""}))
    assert _has_error(errors, "Preencha todos os campos")


def test_nusp_only_digits(client):
    errors = _errors(client, _payload("alunos", overrides={"nusp": "12A"}))
    assert _has_error(errors, "N. USP deve conter apenas números")


def test_agencia_only_digits(client):
    errors = _errors(client, _payload("alunos", overrides={"numero_agencia": "1A34"}))
    assert _has_error(errors, "Número da agência deve conter apenas números")


def test_valor_maior_que_zero(client):
    errors = _errors(client, _payload("alunos", overrides={"valor_solicitado": "0"}))
    assert _has_error(errors, "Valor solicitado deve ser maior que 0")


def test_email_invalido(client):
    errors = _errors(client, _payload("alunos", overrides={"email": "semarrobac.br"}))
    assert _has_error(errors, "E-mail inválido")


def test_cep_formato(client):
    errors = _errors(client, _payload("alunos", overrides={"cep": "05508090"}))
    assert _has_error(errors, "CEP deve estar no formato 00000-000")


def test_data_nascimento_formato(client):
    errors = _errors(client, _payload("alunos", overrides={"data_nascimento": "01-02-1980"}))
    assert _has_error(errors, "Data de nascimento deve estar no formato dd/mm/aaaa")


def test_data_nascimento_invalida(client):
    errors = _errors(client, _payload("alunos", overrides={"data_nascimento": "31/02/2000"}))
    assert _has_error(errors, "Data de nascimento inválida")


def test_cpf_formato(client):
    errors = _errors(client, _payload("alunos", overrides={"cpf": "123456789"}))
    assert _has_error(errors, "CPF deve estar no formato 000.000.000-00")


def test_cpf_digito_verificador(client):
    errors = _errors(client, _payload("alunos", overrides={"cpf": "123.456.789-00"}))
    assert _has_error(errors, "CPF inválido")


@pytest.mark.parametrize("valor", ["1500", "150000", "150000000"])
def test_format_valor_brl(client, valor):
    expected = {
        "1500": "R$ 15,00",
        "150000": "R$ 1.500,00",
        "150000000": "R$ 1.500.000,00",
    }[valor]

    r = client.get(f"/format/valor?raw={valor}")
    assert r.status_code == 200
    assert r.json()["formatted"] == expected


@pytest.mark.parametrize(
    "endpoint, raw, expected",
    [
        ("cpf", "12345678909", "123.456.789-09"),
        ("cep", "05508090", "05508-090"),
        ("data", "01021980", "01/02/1980"),
    ],
)
def test_format_endpoints(client, endpoint, raw, expected):
    r = client.get(f"/format/{endpoint}?raw={raw}")
    assert r.status_code == 200
    assert r.json()["formatted"] == expected
