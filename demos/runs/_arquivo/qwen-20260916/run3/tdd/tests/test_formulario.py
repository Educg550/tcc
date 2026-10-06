import json
import re

import pytest

BASE = {
    "nome": "Maria da Silva",
    "nusp": "1234567",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "SBMAC",
    "periodo": "10/11/2024 a 13/11/2024",
    "cidade": "Rio de Janeiro",
    "estado": "RJ",
    "pais": "Brasil",
    "link": "",
    "valor": "R$ 1500,00",
    "detalhamento": "Participar do congresso.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade_solicitante": "São Paulo",
    "estado_solicitante": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}


def doc():
    return BASE


def aluno():
    return BASE


def post(client, kind, payload):
    return client.post(f"/solicitacao/{kind}", json=payload)


def errors(resp):
    return resp.json()["erros"]


def oficio(resp):
    return resp.json()["oficio"]


# ---- static frontend files ---------------------------------------------------


def test_static_files_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    html = r.text
    assert "<form" in html.lower()
    assert client.get("/index.html").status_code == 200
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200


# ---- exact labels and order --------------------------------------------------


ALL_LABELS = [
    "SOLICITANTE E EVENTO",
    "ENDEREÇO DO SOLICITANTE",
    "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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
    "Enviar solicitação",
]


@pytest.mark.parametrize(
    "path",
    ["index.html", "app.js", "style.css"],
)
def test_labels_present_in_sources(client, path):
    src = client.get("/" + path).text
    for label in ALL_LABELS:
        assert label in src, f"missing label {label!r} in {path}"


@pytest.mark.parametrize(
    "path",
    ["index.html", "app.js"],
)
def test_labels_in_order_in_sources(client, path):
    src = client.get("/" + path).text
    positions = []
    for label in ALL_LABELS:
        idx = src.find(label)
        assert idx >= 0, f"missing label {label!r} in {path}"
        positions.append(idx)
    assert positions == sorted(positions), "labels not in declared order in " + path


# ---- tab-specific fields -----------------------------------------------------


def test_nivel_and_tipo_auxilio_only_on_alunos(client):
    html = client.get("/").text
    assert "Mestrado" in html
    assert "Doutorado" in html
    assert "Banca de exame ou defesa" in html
    assert "Outro" in html


# ---- formatting rules --------------------------------------------------------


def test_format_value(client):
    r = client.post("/formato/valor", json={"digitado": "1500"})
    assert r.status_code == 200
    assert r.json()["formatado"] == "R$ 15,00"
    assert client.post("/formato/valor", json={"digitado": "150000"}).json()["formatado"] == "R$ 1.500,00"
    assert client.post("/formato/valor", json={"digitado": "150000000"}).json()["formatado"] == "R$ 1.500.000,00"


def test_format_cpf(client):
    r = client.post("/formato/cpf", json={"digitado": "12345678909"})
    assert r.status_code == 200
    assert r.json()["formatado"] == "123.456.789-09"


def test_format_cep(client):
    r = client.post("/formato/cep", json={"digitado": "05508090"})
    assert r.status_code == 200
    assert r.json()["formatado"] == "05508-090"


def test_format_data_nascimento(client):
    r = client.post("/formato/data", json={"digitado": "01021980"})
    assert r.status_code == 200
    assert r.json()["formatado"] == "01/02/1980"


# ---- validation: required ----------------------------------------------------


def test_required_empty_single_message(client):
    resp = post(client, "aluno", {})
    assert resp.status_code == 200
    assert resp.json()["valido"] is False
    assert "Preencha todos os campos" in errors(resp)
    assert errors(resp).count("Preencha todos os campos") == 1


def test_required_allows_optional_link_complemento(client):
    payload = aluno()
    payload["link"] = ""
    payload["complemento"] = ""
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert resp.json()["valido"] is True, resp.json()


def test_required_missing_each_field(client):
    for k in BASE:
        if k in ("link", "complemento"):
            continue
        payload = aluno()
        payload[k] = ""
        resp = post(client, "aluno", payload)
        assert resp.json()["valido"] is False, f"should reject empty {k}"
        assert "Preencha todos os campos" in errors(resp), f"missing required msg for {k}"


def test_required_aluno_missing_nivel(client):
    payload = aluno()
    payload["nivel"] = ""
    resp = post(client, "aluno", payload)
    assert resp.json()["valido"] is False
    assert "Preencha todos os campos" in errors(resp)


def test_docente_no_nivel_or_tipo(client):
    payload = doc()
    resp = post(client, "docente", payload)
    assert resp.json()["valido"] is False
    assert "Preencha todos os campos" in errors(resp)


def test_docente_valid_without_nivel(client):
    payload = doc()
    payload["cpf"] = "111.444.777-35"
    payload["nivel"] = ""
    payload["tipo_auxilio"] = ""
    resp = post(client, "docente", payload)
    assert resp.json()["valido"] is True, resp.json()


# ---- validation: digits-only -------------------------------------------------


def test_nusp_must_be_digits(client):
    for bad in ["12a3", " 123 ", "123-456", "", "12.345"]:
        payload = aluno()
        payload["nusp"] = bad
        payload["cpf"] = "111.444.777-35"
        resp = post(client, "aluno", payload)
        if bad == "":
            assert "Preencha todos os campos" in errors(resp)
        else:
            assert "N. USP deve conter apenas números" in errors(resp), f"expected digits error for {bad!r}"


def test_agencia_must_be_digits(client):
    for bad in ["12a", "12-3", "", "1234 5"]:
        payload = aluno()
        payload["agencia"] = bad
        payload["cpf"] = "111.444.777-35"
        resp = post(client, "aluno", payload)
        if bad == "":
            assert "Preencha todos os campos" in errors(resp)
        else:
            assert "Número da agência deve conter apenas números" in errors(resp), f"expected agencia digits error for {bad!r}"


# ---- validation: valor -------------------------------------------------------


def test_valor_positive_natural(client):
    payload = aluno()
    payload["valor"] = "R$ 0,00"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert resp.json()["valido"] is False
    assert "Valor solicitado deve ser maior que 0" in errors(resp)


def test_valor_negative(client):
    payload = aluno()
    payload["valor"] = "-R$ 10,00"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert "Valor solicitado deve ser maior que 0" in errors(resp)


def test_valor_accepts_digit_cents(client):
    payload = aluno()
    payload["valor"] = "1500"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert resp.json()["valido"] is True, resp.json()


def test_valor_non_numeric(client):
    payload = aluno()
    payload["valor"] = "abc"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert "Valor solicitado deve ser maior que 0" in errors(resp)


# ---- validation: email -------------------------------------------------------


def test_email_requires_at(client):
    for bad in ["maria", "maria@", "@ime", "", "maria@ime"]:
        payload = aluno()
        payload["email"] = bad
        payload["cpf"] = "111.444.777-35"
        resp = post(client, "aluno", payload)
        if bad == "":
            assert "Preencha todos os campos" in errors(resp)
        else:
            assert "E-mail inválido" in errors(resp), f"expected email invalid for {bad!r}"


def test_email_accepts_domain(client):
    payload = aluno()
    payload["email"] = "maria@ime.usp.br"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert "E-mail inválido" not in errors(resp)


# ---- validation: cpf / cep / data formats ------------------------------------


def test_cpf_format(client):
    for bad in ["123.456.789-0", "12345678909", "", "12a.456.789-09"]:
        payload = aluno()
        payload["cpf"] = bad
        resp = post(client, "aluno", payload)
        if bad == "":
            assert "Preencha todos os campos" in errors(resp)
        else:
            assert "CPF deve estar no formato 000.000.000-00" in errors(resp), f"expected cpf format error for {bad!r}"


def test_cep_format(client):
    for bad in ["05508090", "055080-90", "", "05508-90"]:
        payload = aluno()
        payload["cep"] = bad
        payload["cpf"] = "111.444.777-35"
        resp = post(client, "aluno", payload)
        if bad == "":
            assert "Preencha todos os campos" in errors(resp)
        else:
            assert "CEP deve estar no formato 00000-000" in errors(resp), f"expected cep format error for {bad!r}"


def test_data_format(client):
    for bad in ["1-2-1980", "", "12202020", "01/13/1980"]:
        payload = aluno()
        payload["data_nascimento"] = bad
        payload["cpf"] = "111.444.777-35"
        resp = post(client, "aluno", payload)
        if bad == "":
            assert "Preencha todos os campos" in errors(resp)
        else:
            assert "Data de nascimento deve estar no formato dd/mm/aaaa" in errors(resp), f"expected data format error for {bad!r}"


def test_data_format_accepts_valid(client):
    payload = aluno()
    payload["cpf"] = "111.444.777-35"
    payload["data_nascimento"] = "01/02/1980"
    resp = post(client, "aluno", payload)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" not in errors(resp)


# ---- validation: cpf check digits --------------------------------------------


def test_cpf_check_digit(client):
    payload = aluno()
    payload["cpf"] = "123.456.789-00"
    resp = post(client, "aluno", payload)
    assert "CPF inválido" in errors(resp)


def test_cpf_check_digit_accepts_valid(client):
    payload = aluno()
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert "CPF inválido" not in errors(resp)


# ---- validation: data existence ----------------------------------------------


def test_data_inexistence(client):
    for bad in ["31/02/2020", "31/04/2020", "00/01/2020", "01/00/2020", "32/01/2020"]:
        payload = aluno()
        payload["data_nascimento"] = bad
        payload["cpf"] = "111.444.777-35"
        resp = post(client, "aluno", payload)
        assert "Data de nascimento inválida" in errors(resp), f"expected invalid data for {bad!r}"


def test_data_29_fev_leap(client):
    payload = aluno()
    payload["data_nascimento"] = "29/02/2020"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert "Data de nascimento inválida" not in errors(resp)


def test_data_29_fev_nonleap(client):
    payload = aluno()
    payload["data_nascimento"] = "29/02/2019"
    payload["cpf"] = "111.444.777-35"
    resp = post(client, "aluno", payload)
    assert "Data de nascimento inválida" in errors(resp)


# ---- ofício content: aluno ---------------------------------------------------


OFICIO_ALUNO_LINES = [
    "Interessada(o): Maria da Silva - 1234567",
    "E-mail: maria@ime.usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Matemática - Mestrado",
    "",
    "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
    "interessada(o) acima, conforme segue:",
    "",
    "Dados do evento",
    "Evento: SBMAC",
    "Período: 10/11/2024 a 13/11/2024",
    "Local: Rio de Janeiro - RJ - Brasil",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Participar do congresso.",
    "",
    "Endereço da(o) interessada(o)",
    "Rua do Matão, 1010",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 56789-0",
    "",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def test_oficio_aluno(client):
    payload = aluno()
    resp = post(client, "aluno", payload)
    assert resp.status_code == 200
    assert resp.json()["valido"] is True, resp.json()
    o = oficio(resp)
    assert "Link do evento" not in o
    assert "Complemento" not in o
    for line in OFICIO_ALUNO_LINES:
        assert line in o.splitlines(), f"missing line {line!r}"


def test_oficio_aluno_lines_in_order(client):
    payload = aluno()
    o = oficio(post(client, "aluno", payload))
    positions = []
    for line in OFICIO_ALUNO_LINES:
        assert line in o, f"missing line {line!r}"
        positions.append(o.find(line))
    assert positions == sorted(positions), "ofício lines out of order"


def test_oficio_aluno_link_included(client):
    payload = aluno()
    payload["link"] = "https://sbmac.org"
    payload["complemento"] = "Apto 1"
    resp = post(client, "aluno", payload)
    o = oficio(resp)
    assert "Link do evento: https://sbmac.org" in o
    assert "Complemento: Apto 1" in o


def test_oficio_valor_formatted(client):
    payload = aluno()
    payload["valor"] = "R$ 15.000,00"
    resp = post(client, "aluno", payload)
    assert resp.json()["valido"] is True, resp.json()
    assert "Valor solicitado: R$ 15.000,00" in oficio(resp)


def test_oficio_no_markers_left(client):
    payload = aluno()
    o = oficio(post(client, "aluno", payload))
    assert "<<" not in o
    assert ">>" not in o


# ---- ofício content: docente -------------------------------------------------


def test_oficio_docente(client):
    payload = doc()
    payload["cpf"] = "111.444.777-35"
    payload["nivel"] = ""
    payload["tipo_auxilio"] = ""
    resp = post(client, "docente", payload)
    assert resp.json()["valido"] is True, resp.json()
    o = oficio(resp)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in o
    assert "Programa: Matemática" in o
    assert "Programa: Matemática - Mestrado" not in o
    assert "Interessada(o): Maria da Silva - 1234567" in o
    assert "Valor solicitado: R$ 1.500,00" in o
    assert "Encaminhe-se ao Serviço Financeiro para providências." in o
    assert "<<" not in o


# ---- all errors at once ------------------------------------------------------


def test_multiple_errors_listed(client):
    payload = aluno()
    payload["nusp"] = "abc"
    payload["email"] = "maria"
    payload["cpf"] = "12345678909"
    payload["cep"] = "05508090"
    payload["data_nascimento"] = "31/02/2020"
    payload["agencia"] = "x1"
    payload["valor"] = "R$ 0,00"
    resp = post(client, "aluno", payload)
    assert resp.json()["valido"] is False
    e = errors(resp)
    for msg in [
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ]:
        assert msg in e, f"missing {msg!r} in {e}"
    assert "Preencha todos os campos" not in e
    assert "oficio" not in resp.json()


# ---- appearance hints in sources --------------------------------------------


def test_appearance_strings(client):
    html = client.get("/").text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert html.find("ALUNOS") < html.find("DOCENTES")
    assert "assets/usp-logo.png" in html

    js = client.get("/app.js").text
    css = client.get("/style.css").text
    assert "Solicitação registrada" in js + html
    assert "Universidade de São Paulo" in js + html

    for color in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert color in css

    combined = (html + js + css).lower()
    assert "brasão" not in combined
    assert "brasao" not in combined
    assert "escudo" not in combined

    assert "Open Sans" in css

    combined_raw = html + js + css
    assert "cdn" not in combined_raw.lower()
    assert "http://" not in combined_raw and "https://" not in combined_raw


# ---- placeholder fields ------------------------------------------------------


def test_placeholders_present(client):
    html = client.get("/").text
    placeholders = re.findall(r"placeholder\s*=\s*[\"']([^\"']+)[\"']", html)
    assert len(placeholders) >= 25
