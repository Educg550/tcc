import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)


DADOS_ALUNO = {
    "nome_completo": "Maria da Silva Souza",
    "numero_usp": "12345678",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "Congresso Nacional de Matemática",
    "periodo_evento": "10 a 12 de outubro de 2024",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor_solicitado": "150000",
    "detalhamento": "Inscrição no congresso e passagem aérea.",
    "apresentacao_trabalho": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg_rnm": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}


def _oficio(resposta):
    assert resposta.status_code == 200
    return resposta.json()


def test_envio_valido_aluno(client):
    r = client.post("/solicitacao/alunos", json=DADOS_ALUNO)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["oficio"].startswith("Interessada(o): Maria da Silva Souza - 12345678")
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in corpo["oficio"]
    assert "Programa: Matemática - Mestrado" in corpo["oficio"]
    assert "Evento: Congresso Nacional de Matemática" in corpo["oficio"]
    assert "Local: São Paulo - SP - Brasil" in corpo["oficio"]
    assert "Valor solicitado: R$ 1.500,00" in corpo["oficio"]
    assert "CPF: 123.456.789-09" in corpo["oficio"]


def test_envio_valido_docente(client):
    dados = {k: v for k, v in DADOS_ALUNO.items() if k not in ("nivel", "tipo_auxilio")}
    r = client.post("/solicitacao/docentes", json=dados)
    assert r.status_code == 200
    corpo = r.json()
    oficio = corpo["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in oficio
    assert "Programa: Matemática" in oficio
    assert "Mestrado" not in oficio


def test_campo_vazio_exige_preenchimento(client):
    dados = dict(DADOS_ALUNO)
    dados["nome_completo"] = ""
    r = client.post("/solicitacao/alunos", json=dados)
    assert r.status_code == 422 or "erros" in r.json()


def test_campo_vazio_retorna_mensagem_exata(client):
    dados = dict(DADOS_ALUNO)
    dados["nome_completo"] = ""
    r = client.post("/solicitacao/alunos", json=dados)
    corpo = r.json()
    mensagens = corpo.get("erros", [])
    assert "Preencha todos os campos" in mensagens


def test_campos_vazios_mensagem_unica(client):
    dados = dict(DADOS_ALUNO)
    dados["nome_completo"] = ""
    dados["bairro"] = ""
    r = client.post("/solicitacao/alunos", json=dados)
    corpo = r.json()
    mensagens = corpo.get("erros", [])
    assert mensagens.count("Preencha todos os campos") == 1


def test_numero_usp_invalido(client):
    dados = dict(DADOS_ALUNO)
    dados["numero_usp"] = "12a45678"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "N. USP deve conter apenas números" in mensagens


def test_agencia_invalida(client):
    dados = dict(DADOS_ALUNO)
    dados["agencia"] = "12a4"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "Número da agência deve conter apenas números" in mensagens


def test_valor_zero_ou_negativo(client):
    dados = dict(DADOS_ALUNO)
    dados["valor_solicitado"] = "0"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "Valor solicitado deve ser maior que 0" in mensagens


def test_email_invalido(client):
    dados = dict(DADOS_ALUNO)
    dados["email"] = "maria@ime"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "E-mail inválido" in mensagens


def test_cpf_formato_invalido(client):
    dados = dict(DADOS_ALUNO)
    dados["cpf"] = "123.456.789-0"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "CPF deve estar no formato 000.000.000-00" in mensagens


def test_cpf_digitos_verificadores_invalidos(client):
    dados = dict(DADOS_ALUNO)
    dados["cpf"] = "123.456.789-00"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "CPF inválido" in mensagens


def test_cep_invalido(client):
    dados = dict(DADOS_ALUNO)
    dados["cep"] = "05508090"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "CEP deve estar no formato 00000-000" in mensagens


def test_data_formato_invalido(client):
    dados = dict(DADOS_ALUNO)
    dados["data_nascimento"] = "01021980"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in mensagens


def test_data_inexistente(client):
    dados = dict(DADOS_ALUNO)
    dados["data_nascimento"] = "31/02/1980"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    assert "Data de nascimento inválida" in mensagens


def test_mesma_validacao_em_docentes(client):
    dados = {k: v for k, v in DADOS_ALUNO.items() if k not in ("nivel", "tipo_auxilio")}
    dados["cpf"] = "111.111.111-11"
    r = client.post("/solicitacao/docentes", json=dados)
    mensagens = r.json().get("erros", [])
    assert "CPF inválido" in mensagens


def test_multiplos_erros_todos_presentes(client):
    dados = dict(DADOS_ALUNO)
    dados["email"] = "sem-arroba"
    dados["cep"] = "12345-678"
    dados["cpf"] = "12345678909"
    dados["data_nascimento"] = "1980-02-01"
    r = client.post("/solicitacao/alunos", json=dados)
    mensagens = r.json().get("erros", [])
    for esperada in (
        "E-mail inválido",
        "CEP deve estar no formato 00000-000",
        "CPF deve estar no formato 000.000.000-00",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert esperada in mensagens


def test_linhas_opcionais_omissas(client):
    dados = dict(DADOS_ALUNO)
    dados["link_evento"] = ""
    dados["complemento"] = ""
    r = client.post("/solicitacao/alunos", json=dados)
    oficio = r.json()["oficio"]
    assert "Link do evento:" not in oficio
    assert "Complemento:" not in oficio


def test_linhas_opcionais_presentes(client):
    dados = dict(DADOS_ALUNO)
    dados["link_evento"] = "https://exemplo.org"
    dados["complemento"] = "Bloco A"
    r = client.post("/solicitacao/alunos", json=dados)
    oficio = r.json()["oficio"]
    assert "Link do evento: https://exemplo.org" in oficio
    assert "Complemento: Bloco A" in oficio


def test_rodape_do_oficio(client):
    r = client.post("/solicitacao/alunos", json=DADOS_ALUNO)
    oficio = r.json()["oficio"]
    assert "Encaminhe-se ao Serviço Financeiro para providências." in oficio


def test_valor_formatado_no_oficio(client):
    dados = dict(DADOS_ALUNO)
    dados["valor_solicitado"] = "1500"
    r = client.post("/solicitacao/alunos", json=dados)
    assert "Valor solicitado: R$ 15,00" in r.json()["oficio"]


def test_arquivos_estaticos_servidos(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "ENVIAR SOLICITAÇÃO" in r.text.upper()
    r2 = client.get("/app.js")
    assert r2.status_code == 200
    r3 = client.get("/style.css")
    assert r3.status_code == 200
    r4 = client.get("/assets/usp-logo.png")
    assert r4.status_code == 200
