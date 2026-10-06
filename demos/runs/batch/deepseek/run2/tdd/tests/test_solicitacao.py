import re
import difflib
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app import app
    return TestClient(app)

@pytest.fixture
def openapi(client):
    return client.get("/openapi.json").json()

@pytest.fixture
def solicitar_url(openapi):
    for path, methods in openapi.get("paths", {}).items():
        if "post" in methods:
            if path in ["/docs", "/openapi.json", "/token"]:
                continue
            return path
    pytest.fail("Nenhum endpoint POST encontrado")

@pytest.fixture
def schema_props(openapi, solicitar_url):
    post = openapi["paths"][solicitar_url]["post"]
    request_body = post.get("requestBody", {})
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    if "$ref" in schema:
        ref = schema["$ref"]
        model_name = ref.split("/")[-1]
        schema = openapi["components"]["schemas"][model_name]
    return schema.get("properties", {})

def normalize(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def map_payload(canonical_payload, schema_props):
    mapped = {}
    for ckey, cval in canonical_payload.items():
        cnorm = normalize(ckey)
        best_key = None
        best_ratio = 0
        for pkey in schema_props:
            pnorm = normalize(pkey)
            ratio = difflib.SequenceMatcher(None, cnorm, pnorm).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_key = pkey
        if best_key and best_ratio > 0.6:
            mapped[best_key] = cval
        else:
            mapped[ckey] = cval
    return mapped

def post_solicitacao(client, payload, solicitar_url, schema_props):
    mapped = map_payload(payload, schema_props)
    return client.post(solicitar_url, json=mapped)

@pytest.fixture
def valid_aluno_payload():
    return {
        "nome_completo": "Fulano de Tal",
        "n_usp": "12345678",
        "programa": "Ciência da Computação",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "fulano@ime.usp.br",
        "nome_evento": "Conferência de Testes",
        "periodo_evento": "01/01/2024 a 05/01/2024",
        "cidade_evento": "São Paulo",
        "estado_evento": "SP",
        "pais_evento": "Brasil",
        "link_evento": "http://evento.com",
        "valor_solicitado": "R$ 1.500,00",
        "detalhamento_pedido": "Detalhamento do pedido",
        "apresentacao_trabalho": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua Exemplo",
        "numero": "123",
        "complemento": "Apto 45",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade": "São Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg_rnm": "12.345.678-9",
        "nome_banco": "Banco do Brasil",
        "numero_agencia": "1234",
        "numero_conta": "12345-6"
    }

@pytest.fixture
def valid_docente_payload(valid_aluno_payload):
    payload = valid_aluno_payload.copy()
    payload.pop("nivel", None)
    payload.pop("tipo_auxilio", None)
    return payload

def test_pagina_inicial_contem_abas_e_blocos(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert "SOLICITANTE E EVENTO" in html
    assert "ENDEREÇO DO SOLICITANTE" in html
    assert "INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO" in html
    assert "Enviar solicitação" in html
    assert "Universidade de São Paulo" in html
    assert "assets/usp-logo.png" in html

def test_campos_obrigatorios_vazios(client, solicitar_url, schema_props, valid_aluno_payload):
    payload = {k: "" for k in valid_aluno_payload}
    response = post_solicitacao(client, payload, solicitar_url, schema_props)
    assert "Preencha todos os campos" in response.text
    assert response.text.count("Preencha todos os campos") == 1

def test_n_usp_invalido(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["n_usp"] = "abc"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "N. USP deve conter apenas números" in response.text

def test_agencia_invalida(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["numero_agencia"] = "abc"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Número da agência deve conter apenas números" in response.text

def test_valor_solicitado_invalido(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["valor_solicitado"] = "R$ 0,00"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Valor solicitado deve ser maior que 0" in response.text

def test_email_invalido(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["email"] = "invalido"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "E-mail inválido" in response.text

def test_cpf_formato_invalido(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["cpf"] = "123"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "CPF deve estar no formato 000.000.000-00" in response.text

def test_cep_formato_invalido(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["cep"] = "123"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "CEP deve estar no formato 00000-000" in response.text

def test_data_nascimento_formato_invalido(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["data_nascimento"] = "123"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in response.text

def test_cpf_digitos_invalidos(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["cpf"] = "123.456.789-00"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "CPF inválido" in response.text

def test_data_nascimento_invalida(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["data_nascimento"] = "31/02/2020"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Data de nascimento inválida" in response.text

def test_multiplos_erros(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["n_usp"] = "abc"
    valid_aluno_payload["email"] = "invalido"
    valid_aluno_payload["cpf"] = "123"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "N. USP deve conter apenas números" in response.text
    assert "E-mail inválido" in response.text
    assert "CPF deve estar no formato 000.000.000-00" in response.text

def test_envio_valido_alunos_retorna_oficio(client, solicitar_url, schema_props, valid_aluno_payload):
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    text = response.text
    assert "Interessada(o): Fulano de Tal - 12345678" in text
    assert "E-mail: fulano@ime.usp.br" in text
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in text
    assert "Programa: Ciência da Computação - Mestrado" in text
    assert "Evento: Conferência de Testes" in text
    assert "Período: 01/01/2024 a 05/01/2024" in text
    assert "Local: São Paulo - SP - Brasil" in text
    assert "Link do evento: http://evento.com" in text
    assert "Apresentação de trabalho: Pôster" in text
    assert "Valor solicitado: R$ 1.500,00" in text
    assert "Detalhamento: Detalhamento do pedido" in text
    assert "Rua Exemplo, 123" in text
    assert "Complemento: Apto 45" in text
    assert "CEP: 05508-090" in text
    assert "Centro, São Paulo - SP" in text
    assert "Data de nascimento: 01/02/1980" in text
    assert "CPF: 123.456.789-09" in text
    assert "RG / RNM: 12.345.678-9" in text
    assert "Banco: Banco do Brasil" in text
    assert "Agência: 1234" in text
    assert "Conta: 12345-6" in text
    assert "Encaminhe-se ao Serviço Financeiro para providências." in text

def test_envio_valido_docentes_retorna_oficio(client, solicitar_url, schema_props, valid_docente_payload):
    response = post_solicitacao(client, valid_docente_payload, solicitar_url, schema_props)
    text = response.text
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in text
    assert "Programa: Ciência da Computação" in text
    assert "Programa: Ciência da Computação - Mestrado" not in text

def test_link_evento_vazio_remove_linha(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["link_evento"] = ""
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Link do evento:" not in response.text

def test_complemento_vazio_remove_linha(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["complemento"] = ""
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Complemento:" not in response.text

def test_erros_nao_geram_oficio(client, solicitar_url, schema_props, valid_aluno_payload):
    valid_aluno_payload["n_usp"] = "abc"
    response = post_solicitacao(client, valid_aluno_payload, solicitar_url, schema_props)
    assert "Interessada(o):" not in response.text
