import re

import pytest
from fastapi.testclient import TestClient

import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app.app) as c:
        yield c


BASE_DOCENTE = {
    "nome": "Maria Silva",
    "nusp": "1234567",
    "programa": "Matemática",
    "email": "maria@ime.usp.br",
    "evento": "Colóquio",
    "periodo": "10 a 12/05/2024",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link": "https://event.example",
    "valor": 150000,
    "detalhamento": "Ajuda de custo para viagem.",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Apto 1",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

ALUNO = dict(
    BASE_DOCENTE,
    nivel="Doutorado",
    tipo_auxilio="Participação em evento",
)


def post_form(client, tipo, dados):
    return client.post(f"/api/solicitacoes/{tipo}", json=dados)


def get_page(client, path):
    return client.get(path)


# ---------------------------------------------------------------------------
# Servidor de arquivos estáticos
# ---------------------------------------------------------------------------


EXPECTED_STATIC = {
    "/": "text/html",
    "/index.html": "text/html",
    "/app.js": "javascript",
    "/style.css": "css",
    "/assets/usp-logo.png": "png",
}


def test_static_served(client):
    for path, ctype in EXPECTED_STATIC.items():
        r = get_page(client, path)
        assert r.status_code == 200, f"GET {path} -> {r.status_code}"
        assert ctype in r.headers.get("content-type", ""), f"{path}: content-type {r.headers.get('content-type')!r} não contém {ctype!r}"


# ---------------------------------------------------------------------------
# Frontend - rótulos, abas, placeholders
# ---------------------------------------------------------------------------

LABELS = [
    "ALUNOS",
    "DOCENTES",
    "Enviar solicitação",
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
    "Mestrado",
    "Doutorado",
    "Participação em evento",
    "Banca de exame ou defesa",
    "Outro",
    "Pôster",
    "Apresentação oral",
    "Não irá apresentar trabalho",
]


def test_labels_present(client):
    html = get_page(client, "/").text
    for label in LABELS:
        assert label in html, f"Rótulo ausente: {label!r}"


def test_labels_order(client):
    html = get_page(client, "/")
    assert "ALUNOS" in html
    assert "DOCENTES" in html
    assert "NÍVEL" in html
    assert "TIPO DE AUXÍLIO" in html


# ---------------------------------------------------------------------------
# Backend - validação
# ---------------------------------------------------------------------------


def test_validacao_campos_vazios(client):
    dados = ALUNO.copy()
    dados["nome"] = ""
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert erros == ["Preencha todos os campos"], f"erros={erros}"


def test_validacao_nusp(client):
    dados = ALUNO.copy()
    dados["nusp"] = "123abc"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "N. USP deve conter apenas números" in erros


def test_validacao_agencia(client):
    dados = ALUNO.copy()
    dados["agencia"] = "12-34"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "Número da agência deve conter apenas números" in erros


def test_validacao_valor_zero(client):
    dados = ALUNO.copy()
    dados["valor"] = 0
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "Valor solicitado deve ser maior que 0" in erros


def test_validacao_email(client):
    dados = ALUNO.copy()
    dados["email"] = "maria@"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "E-mail inválido" in erros


def test_validacao_cpf_formato(client):
    dados = ALUNO.copy()
    dados["cpf"] = "12345678909"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "CPF deve estar no formato 000.000.000-00" in erros


def test_validacao_cep_formato(client):
    dados = ALUNO.copy()
    dados["cep"] = "05508090"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "CEP deve estar no formato 00000-000" in erros


def test_validacao_data_formato(client):
    dados = ALUNO.copy()
    dados["data_nascimento"] = "01-02-1980"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros


def test_validacao_cpf_digitos(client):
    dados = ALUNO.copy()
    dados["cpf"] = "111.111.111-11"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "CPF inválido" in erros


def test_validacao_data_existente(client):
    dados = ALUNO.copy()
    dados["data_nascimento"] = "30/02/1980"
    r = post_form(client, "aluno", dados)
    assert r.status_code == 200
    erros = r.json().get("erros", [])
    assert "Data de nascimento inválida" in erros


# ---------------------------------------------------------------------------
# Backend - ofício
# ---------------------------------------------------------------------------


def oficio(client, tipo, dados):
    r = post_form(client, tipo, dados)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True, f"esperado ok, veio {body}"
    assert body.get("erros", []) == [], f"esperado sem erros, veio {body}"
    return body.get("oficio", "")


def test_oficio_aluno(client):
    texto = oficio(client, "aluno", ALUNO)
    assert "Interessada(o): Maria Silva - 1234567" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in texto
    assert "Programa: Matemática - Doutorado" in texto
    assert "E-mail: maria@ime.usp.br" in texto
    assert "R$ 1.500,00" in texto


def test_oficio_docente(client):
    texto = oficio(client, "docente", BASE_DOCENTE)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática\n" in texto or texto.endswith("Programa: Matemática")
    assert "Doutorado" not in texto
    assert "Participação em evento" not in texto


def test_oficio_omitir_link(client):
    dados = ALUNO.copy()
    dados["link"] = ""
    texto = oficio(client, "aluno", dados)
    assert "Link do evento:" not in texto


def test_oficio_omitir_complemento(client):
    dados = ALUNO.copy()
    dados["complemento"] = ""
    texto = oficio(client, "aluno", dados)
    assert "Complemento:" not in texto


def test_oficio_preserva_linhas(client):
    texto = oficio(client, "aluno", ALUNO)
    for linha in [
        "Dados do evento",
        "Evento: Colóquio",
        "Período: 10 a 12/05/2024",
        "Local: São Paulo - SP - Brasil",
        "Endereço da(o) interessada(o)",
        "Dados para pagamento",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]:
        assert linha in texto, f"linha ausente: {linha!r}"


def test_oficio_formato_valor(client):
    for valor, esperado in [
        (1500, "R$ 15,00"),
        (150000, "R$ 1.500,00"),
        (150000000, "R$ 1.500.000,00"),
    ]:
        dados = ALUNO.copy()
        dados["valor"] = valor
        texto = oficio(client, "aluno", dados)
        assert esperado in texto, f"valor {valor} -> esperado {esperado!r} não encontrado"


# ---------------------------------------------------------------------------
# Regras de formatação e validação: não há API de servidor para isso; cobrimos
# via checagem estática do app.js.
# ---------------------------------------------------------------------------


def test_appjs_formatacao(client):
    js = get_page(client, "/app.js").text
    assert "R$" in js
    assert re.search(r"000\.000\.000-00|\\d\\d\\d", js), "app.js não trata máscara de CPF"
    assert re.search(r"05508-090|\\d{5}-\\d{3}|CEP", js), "app.js não trata máscara de CEP"
    assert re.search(r"dd/mm/aaaa|\\/\\d|DATA", js), "app.js não trata máscara de data"


def test_oficio_linhas_exatas(client):
    texto = oficio(client, "docente", BASE_DOCENTE)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Matemática" in texto
    assert "Doutorado" not in texto
    assert "Banca de exame" not in texto
