from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

POST = {"aba": "alunos", "nome": "Fulana da Silva", "numero_usp": "1234567",
        "programa": "Matemática", "nivel": "Mestrado", "tipo_auxilio": "Participação em evento",
        "email": "fulana@ime.usp.br", "evento": "Congresso de Matemática", "periodo": "10 a 12 de maio",
        "cidade": "São Paulo", "estado_evento": "SP", "pais": "Brasil", "link": "",
        "valor_centavos": 150000, "detalhamento": "Inscrição", "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980", "logradouro": "Rua do Matão", "numero": "1010",
        "complemento": "", "bairro": "Butantã", "cep": "05508-090", "cidade_endereco": "São Paulo",
        "estado_endereco": "SP", "cpf": "153.509.460-56", "rg": "12.345.678-9",
        "banco": "Banco do Brasil", "agencia": "1234", "conta": "12345-6"}

R = client.post("/solicitacao", json=POST)
assert R.status_code == 200, R.text
OFICIO = R.json()["oficio"]


def test_titulo_confirmacao_e_cabecalho():
    pagina = client.get("/confirmacao?ref=abc123").text
    assert "Solicitação registrada" in pagina
    assert "usp-logo.png" in pagina
    assert "Universidade de São Paulo" in pagina


def test_linhas_do_oficio_aluno():
    assert "Interessada(o): Fulana da Silva - 1234567" in OFICIO
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in OFICIO
    assert "Programa: Matemática - Mestrado" in OFICIO
    assert "Evento: Congresso de Matemática" in OFICIO
    assert "Local: São Paulo - SP - Brasil" in OFICIO
    assert "Apresentação de trabalho: Pôster" in OFICIO
    assert "Valor solicitado: R$ 1.500,00" in OFICIO
    assert "CEP: 05508-090" in OFICIO
    assert "CPF: 153.509.460-56" in OFICIO
    assert "Data de nascimento: 01/02/1980" in OFICIO
    assert "Encaminhe-se ao Serviço Financeiro para providências." in OFICIO


def test_linhas_opcionais_omitidas():
    assert "Link do evento" not in OFICIO
    assert "Complemento" not in OFICIO


def test_oficio_docente():
    dados = POST | {"aba": "docentes"}
    r = client.post("/solicitacao", json=dados)
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Mestrado" not in oficio


def test_linhas_opcionais_presentes():
    dados = POST | {"link": "http://site", "complemento": "Sala 10"}
    r = client.post("/solicitacao", json=dados)
    oficio = r.json()["oficio"]
    assert "Link do evento: http://site" in oficio
    assert "Complemento: Sala 10" in oficio


def test_linhas_do_oficio_na_ordem():
    esperado = ["Interessada(o): Fulana da Silva - 1234567",
                "E-mail: fulana@ime.usp.br",
                "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
                "Programa: Matemática - Mestrado",
                "Dados do evento",
                "Endereço da(o) interessada(o)",
                "Dados para pagamento",
                "Encaminhe-se ao Serviço Financeiro para providências."]
    for linha in esperado:
        assert linha in OFICIO
    indice = [OFICIO.index(linha) for linha in esperado]
    assert indice == sorted(indice)


def test_valor_grande_formatado():
    dados = POST | {"valor_centavos": 150000000}
    oficio = client.post("/solicitacao", json=dados).json()["oficio"]
    assert "Valor solicitado: R$ 1.500.000,00" in oficio


def test_quebras_de_linha_preservadas_na_pagina():
    pagina = client.get("/confirmacao?ref=abc123").text
    for linha in OFICIO.strip().splitlines():
        assert pagina.count(linha.strip()) >= 1, linha
