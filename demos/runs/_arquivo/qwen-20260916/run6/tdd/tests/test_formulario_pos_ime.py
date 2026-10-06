import re

import pytest


LABELS = {
    "alunos": [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ],
    "docentes": [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ],
}


def test_backend_app_exists_and_routes():
    import app

    client = app.app
    assert hasattr(client, "routes"), "backend não expõe uma aplicação ASGI"
    paths = {getattr(r, "path", None) for r in client.routes}
    assert any("/index.html" in p for p in paths if p), "falta rota para index.html"
    assert any(p and ("/api/" in p or "/form" in p) for p in paths), "falta rota de API"


def test_formulao_has_tabs():
    import app

    client = app.app
    resp = client.get("/index.html")
    assert resp.status_code == 200, "index.html não é servido"
    assert "text/html" in resp.headers["content-type"]
    html = resp.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html


def test_form_fields_alunos_present():
    import app

    client = app.app
    html = client.get("/index.html").text
    labels = [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
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
    missing = [l for l in labels if l not in html]
    assert not missing, f"Rótulos ausentes no formulário: {missing}"


def test_form_fields_docentes_no_nivel_tipo():
    import app

    client = app.app
    html = client.get("/index.html").text
    assert "NÍVEL" in html
    assert "TIPO DE AUXÍLIO" in html
    # A diferença dos docentes aparece no ofício ("Verba do programa")
    assert "Enviar solicitação" in html


def test_alunos_select_options():
    import app

    client = app.app
    html = client.get("/index.html").text
    for opt in ("Mestrado", "Doutorado"):
        assert opt in html
    for opt in ("Participação em evento", "Banca de exame ou defesa", "Outro"):
        assert opt in html
    for opt in (
        "Pôster",
        "Apresentação oral",
        "Outra",
        "Não irá apresentar trabalho",
    ):
        assert opt in html


def test_static_assets_and_frontend_files():
    import app

    client = app.app
    resp = client.get("/assets/usp-logo.png")
    assert resp.status_code == 200
    resp_css = client.get("/style.css")
    assert resp_css.status_code == 200
    assert "text/css" in resp_css.headers["content-type"]
    resp_js = client.get("/app.js")
    assert resp_js.status_code == 200
    assert "javascript" in resp_js.headers["content-type"]
    css = resp_css.text
    for token in ("#1094ab", "#64c4d2", "#fcb421", "Open Sans"):
        assert token in css, f"Token de estilo ausente: {token}"
    assert "Universidade de São Paulo" in client.get("/index.html").text


def _payload(aba):
    p = {
        "aba": aba,
        "nome": "João da Silva",
        "nusp": "123456",
        "programa": "Matemática",
        "email": "joao@ime.usp.br",
        "link_evento": "https://event.example",
        "valor": "R$ 1.500,00",
        "evento": "Congresso",
        "periodo": "01/02/2024 - 05/02/2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "detalhamento": "Participar do congresso para apresentar pesquisa.",
        "apresentar": "Pôster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua Exemplo",
        "numero": "100",
        "complemento": "Apto 10",
        "bairro": "Bairro",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "123456-7",
    }
    if aba == "alunos":
        p["nivel"] = "Mestrado"
        p["tipo_auxilio"] = "Participação em evento"
    return p


def _post(payload):
    import app

    client = app.app
    resp = client.post("/api/solicitar", json=payload)
    assert resp.status_code == 200, f"status={resp.status_code} body={resp.text[:500]}"
    return resp.json()


def _oficio(data):
    return "\n".join(data["oficio"]) if isinstance(data["oficio"], list) else data["oficio"]


def _errors(data):
    return data.get("erros", [])


def _assert_ok(data):
    assert not _errors(data), f"esperava sem erros, veio {data}"


@pytest.mark.parametrize("aba", ("alunos", "docentes"))
def test_valid_submission_returns_oficio(aba):
    data = _post(_payload(aba))
    _assert_ok(data)
    of = _oficio(data)
    assert "Interessada(o): João da Silva - 123456" in of
    assert "E-mail: joao@ime.usp.br" in of
    assert "A CCP-Matemática aprovou na data de hoje" in of
    assert "Encaminhe-se ao Serviço Financeiro para providências." in of
    assert "Link do evento:" in of
    assert "Complemento: Apto 10" in of


def test_oficio_alunos():
    data = _post(_payload("alunos"))
    _assert_ok(data)
    of = _oficio(data)
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in of
    assert "Programa: Matemática - Mestrado" in of


def test_oficio_docentes():
    data = _post(_payload("docentes"))
    _assert_ok(data)
    of = _oficio(data)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in of
    assert "Programa: Matemática" in of


def test_oficio_optional_lines_omitted():
    p = _payload("alunos")
    p["link_evento"] = ""
    p["complemento"] = ""
    data = _post(p)
    _assert_ok(data)
    of = _oficio(data)
    lines = [ln.strip() for ln in of.split("\n")]
    assert not any(ln.startswith("Link do evento:") for ln in lines), "linha de link vazia presente"
    assert not any(ln.startswith("Complemento:") for ln in lines), "linha de complemento vazia presente"


def test_error_empty_required():
    p = _payload("alunos")
    p["nome"] = ""
    data = _post(p)
    assert "Preencha todos os campos" in _errors(data)
    assert "oficio" not in data or _oficio(data) == ""


def test_error_nusp():
    p = _payload("alunos")
    p["nusp"] = "12a"
    data = _post(p)
    assert "N. USP deve conter apenas números" in _errors(data)


def test_error_agencia():
    p = _payload("alunos")
    p["agencia"] = "1a2"
    data = _post(p)
    assert "Número da agência deve conter apenas números" in _errors(data)


def test_error_valor():
    for bad in ("", "0", "-5", "abc"):
        p = _payload("alunos")
        p["valor"] = bad
        data = _post(p)
        assert "Valor solicitado deve ser maior que 0" in _errors(data), f"valor {bad!r}"


def test_error_email():
    for bad in ("", "abc", "a@", "@b"):
        p = _payload("alunos")
        p["email"] = bad
        data = _post(p)
        assert "E-mail inválido" in _errors(data), f"email {bad!r}"


def test_error_cpf_format():
    p = _payload("alunos")
    p["cpf"] = "12345678909"
    data = _post(p)
    assert "CPF deve estar no formato 000.000.000-00" in _errors(data)


def test_error_cep_format():
    p = _payload("alunos")
    p["cep"] = "05508090"
    data = _post(p)
    assert "CEP deve estar no formato 00000-000" in _errors(data)


def test_error_nascimento_format():
    p = _payload("alunos")
    p["nascimento"] = "1980-02-01"
    data = _post(p)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _errors(data)


def test_error_cpf_check_digit():
    p = _payload("alunos")
    p["cpf"] = "111.111.111-11"
    data = _post(p)
    assert "CPF inválido" in _errors(data)


def test_error_nascimento_invalid_date():
    p = _payload("alunos")
    p["nascimento"] = "31/02/1990"
    data = _post(p)
    assert "Data de nascimento inválida" in _errors(data)


def test_multiple_errors_shown():
    p = _payload("alunos")
    p["nusp"] = "x"
    p["cep"] = "bad"
    data = _post(p)
    errors = _errors(data)
    assert any("N. USP" in e for e in errors)
    assert any("CEP" in e for e in errors)
    assert "oficio" not in data or _oficio(data) == ""
