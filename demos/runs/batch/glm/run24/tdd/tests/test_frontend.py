import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

INDEX = client.get("/")
HTML = INDEX.text


def _valid_alunos_payload(**overrides):
    base = {
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Nacional de Matemática",
        "periodo": "10 a 12 de outubro de 2025",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "",
        "valor_solicitado": "1500",
        "detalhamento": "Passagem aérea e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01021980",
        "logradouro": "Rua do Matão",
        "numero": "1010",
        "complemento": "",
        "bairro": "Butantã",
        "cep": "05508090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "52998224725",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
        "aba": "ALUNOS",
    }
    base.update(overrides)
    return base


def _base_docentes():
    base = _valid_alunos_payload()
    base.pop("nivel")
    base.pop("tipo_auxilio")
    base["aba"] = "DOCENTES"
    return base


def _valid_docentes_payload(**overrides):
    base = _base_docentes()
    base.update(overrides)
    return base


def _ok(response):
    return response.status_code == 200 and response.json()["ok"] is True


def _get(response, key):
    return response.json()[key]


def _doc_valido_complemento():
    _doc_valido = _valid_docentes_payload()
    _doc_valido["complemento"] = "Apto 12"
    _doc_valido["link_evento"] = ""
    return _doc_valido


def test_index_servido():
    assert INDEX.status_code == 200
    assert "<!DOCTYPE html>" in HTML


def test_estaticos_servidos():
    for path in ["/static/style.css", "/static/app.js", "/static/assets/usp-logo.png"]:
        response = client.get(path)
        assert response.status_code == 200, path


def test_static_nao_persiste(tmp_path, monkeypatch):
    pass


def test_html_abas():
    assert re.search(r"ALUNOS", HTML)
    assert re.search(r"DOCENTES", HTML)


def test_html_cabecalho_institucional():
    assert "usp-logo.png" in HTML
    assert "Universidade de São Paulo" in HTML


def test_html_rotulos_blocos():
    for rotulo in [
        "SOLICITANTE E EVENTO",
        "ENDEREÇO DO SOLICITANTE",
        "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO",
    ]:
        assert rotulo in HTML, rotulo


def test_alunos_envio_valido_gera_oficio():
    response = client.post("/solicitar", json=_valid_alunos_payload())
    assert _ok(response)
    oficio = _get(response, "oficio")
    assert "Interessada(o): Maria da Silva - 12345678" in oficio
    assert "Programa: Matemática - Mestrado" in oficio
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in oficio
    assert "Congresso Nacional de Matemática" in oficio
    assert "São Paulo - SP - Brasil" in oficio
    assert "R$ 15,00" in oficio
    assert "Link do evento" not in oficio
    assert "Complemento" not in oficio


def test_docentes_envio_valido_gera_oficio():
    response = client.post("/solicitar", json=_valid_docentes_payload())
    assert _ok(response)
    oficio = _get(response, "oficio")
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Mestrado" not in oficio


def test_oficio_complemento_e_link_presentes_quando_preenchidos():
    response = client.post("/solicitar", json=_doc_valido_complemento())
    assert _ok(response)
    oficio = _get(response, "oficio")
    assert "Link do evento:" not in oficio
    assert "Complemento: Apto 12" in oficio


def test_valor_formatado_com_milhar():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(valor_solicitado="150000")
    )
    assert _ok(response)
    assert "R$ 1.500,00" in _get(response, "oficio")


def test_campo_obrigatorio_vazio():
    response = client.post("/solicitar", json=_valid_alunos_payload(nome=""))
    assert response.status_code == 200
    assert response.json()["ok"] is False
    erros = _get(response, "erros")
    assert erros == ["Preencha todos os campos"]


def test_campo_opcional_vazio_ok():
    response = client.post("/solicitar", json=_valid_alunos_payload())
    assert _ok(response)


def test_n_usp_digitos():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(n_usp="12a45")
    )
    assert response.json()["ok"] is False
    assert "N. USP deve conter apenas números" in _get(response, "erros")


def test_agencia_digitos():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(agencia="12-3")
    )
    assert response.json()["ok"] is False
    assert "Número da agência deve conter apenas números" in _get(response, "erros")


def test_valor_zero():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(valor_solicitado="0")
    )
    assert response.json()["ok"] is False
    assert "Valor solicitado deve ser maior que 0" in _get(response, "erros")


def test_email_invalido():
    for email in ["maria", "maria@", "@ime.usp.br"]:
        response = client.post(
            "/solicitar", json=_valid_alunos_payload(email=email)
        )
        assert response.json()["ok"] is False, email
        assert "E-mail inválido" in _get(response, "erros"), email


def test_cpf_formato_invalido():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(cpf="1234567890")
    )
    assert response.json()["ok"] is False
    assert "CPF deve estar no formato 000.000.000-00" in _get(response, "erros")


def test_cep_formato_invalido():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(cep="05508-090")
    )
    assert response.json()["ok"] is False
    assert "CEP deve estar no formato 00000-000" in _get(response, "erros")


def test_data_formato_invalido():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(data_nascimento="01/02/1980")
    )
    assert response.json()["ok"] is False
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _get(
        response, "erros"
    )


def test_cpf_verificador_invalido():
    response = client.post(
        "/solicitar", json=_valid_alunos_payload(cpf="52998224700")
    )
    assert response.json()["ok"] is False
    assert "CPF inválido" in _get(response, "erros")
    assert "CPF deve estar no formato 000.000.000-00" not in _get(response, "erros")


def test_data_inexistente():
    for data in ["31022020", "010220", "15152020"]:
        response = client.post(
            "/solicitar", json=_valid_alunos_payload(data_nascimento=data)
        )
        assert response.json()["ok"] is False, data
        assert "Data de nascimento inválida" in _get(response, "erros"), data


def test_todos_erros_relevantes_juntos():
    payload = _valid_alunos_payload()
    payload.update(
        {
            "n_usp": "abc",
            "agencia": "12a",
            "valor_solicitado": "0",
            "email": "semarroba",
            "cpf": "11111111111",
            "cep": "1234567",
            "data_nascimento": "321320",
        }
    )
    response = client.post("/solicitar", json=payload)
    erros = _get(response, "erros")
    assert set(erros) == {
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF inválido",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    }
    assert "Preencha todos os campos" not in erros


def test_docentes_validacao():
    response = client.post("/solicitar", json=_valid_docentes_payload(email="x"))
    assert response.json()["ok"] is False
    assert "E-mail inválido" in _get(response, "erros")


def test_preencher_todos_campos_obrigatorios_docentes():
    response = client.post("/solicitar", json=_base_docentes())
    assert _ok(response)
