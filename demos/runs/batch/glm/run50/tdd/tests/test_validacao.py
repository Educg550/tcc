from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def post(aba, **alteracoes):
    dados = formulario_valido()
    dados.update(alteracoes)
    return client.post("/api/solicitacao/" + aba, json=dados)


def formulario_valido():
    return {
        "aba": "alunos",
        "nome": "Maria da Silva",
        "n_usp": "12345678",
        "programa": "Matemática",
        "nivel": "Mestrado",
        "tipo_auxilio": "Participação em evento",
        "email": "maria@ime.usp.br",
        "evento": "Congresso Nacional",
        "periodo": "10 a 12 de outubro de 2025",
        "cidade": "São Paulo",
        "estado": "SP",
        "pais": "Brasil",
        "link": "https://exemplo.com",
        "valor": "R$ 1.500,00",
        "detalhamento": "Inscrição e hospedagem",
        "apresentacao": "Pôster",
        "data_nascimento": "01/02/1980",
        "logradouro": "Rua Teste",
        "numero": "100",
        "complemento": "",
        "bairro": "Centro",
        "cep": "05508-090",
        "cidade_end": "São Paulo",
        "estado_end": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "12345-6",
    }


def test_valido_gera_oficio():
    r = post("alunos")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["ok"] is True
    oficio = corpo["oficio"]

    esperado = [
        "Interessada(o): Maria da Silva - 12345678",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: Congresso Nacional",
        "Período: 10 a 12 de outubro de 2025",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://exemplo.com",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 1.500,00",
        "Detalhamento: Inscrição e hospedagem",
        "",
        "Endereço da(o) interessada(o)",
        "Rua Teste, 100",
        "Complemento: ",
        "CEP: 05508-090",
        "Centro, São Paulo - SP",
        "",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 12345-6",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    assert oficio.split("\n") == esperado


def test_docentes_oficio_sem_nivel_e_tipo():
    dados = formulario_valido()
    dados.pop("nivel")
    dados.pop("tipo_auxilio")
    r = post("docentes", **dados)
    assert r.status_code == 200
    oficio = r.json()["oficio"]
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa\n" in oficio
    assert "Programa: Matemática\n" in oficio
    assert "- Mestrado" not in oficio


def test_campos_vazios():
    dados = formulario_valido()
    for chave in dados:
        if chave != "aba":
            if chave in ("link", "complemento"):
                continue
            dados[chave] = ""
    r = client.post("/api/solicitacao/alunos", json=dados)
    assert r.status_code == 422
    corpo = r.json()
    assert "Preencha todos os campos" in corpo["erros"]
    assert corpo["ok"] is False


def test_n_usp_letras():
    r = post("alunos", n_usp="12a3")
    assert r.status_code == 422
    assert "N. USP deve conter apenas números" in r.json()["erros"]


def test_agencia_letras():
    r = post("alunos", agencia="12a")
    assert r.status_code == 422
    assert "Número da agência deve conter apenas números" in r.json()["erros"]


def test_valor_zero():
    r = post("alunos", valor="R$ 0,00")
    assert r.status_code == 422
    assert "Valor solicitado deve ser maior que 0" in r.json()["erros"]


def test_email_invalido():
    r = post("alunos", email="maria")
    assert r.status_code == 422
    assert "E-mail inválido" in r.json()["erros"]


def test_cpf_formato_errado():
    r = post("alunos", cpf="12345678909")
    assert r.status_code == 422
    assert "CPF deve estar no formato 000.000.000-00" in r.json()["erros"]


def test_cep_formato_errado():
    r = post("alunos", cep="05508 090")
    assert r.status_code == 422
    assert "CEP deve estar no formato 00000-000" in r.json()["erros"]


def test_data_formato_errado():
    r = post("alunos", data_nascimento="01021980")
    assert r.status_code == 422
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in r.json()["erros"]


def test_cpf_dvs_errados():
    r = post("alunos", cpf="123.456.789-00")
    assert r.status_code == 422
    assert "CPF inválido" in r.json()["erros"]


def test_data_inexistente():
    r = post("alunos", data_nascimento="31/02/1980")
    assert r.status_code == 422
    assert "Data de nascimento inválida" in r.json()["erros"]


def test_todos_os_erros():
    dados = {
        "aba": "alunos",
        "nome": "",
        "n_usp": "12a",
        "programa": "",
        "nivel": "Mestrado",
        "tipo_auxilio": "",
        "email": "sem-arroba",
        "evento": "",
        "periodo": "",
        "cidade": "",
        "estado": "",
        "pais": "",
        "link": "",
        "valor": "R$ 0,00",
        "detalhamento": "",
        "apresentacao": "",
        "data_nascimento": "99/99/9999",
        "logradouro": "",
        "numero": "",
        "complemento": "",
        "bairro": "",
        "cep": "12345",
        "cidade_end": "",
        "estado_end": "",
        "cpf": "12345678909",
        "rg": "",
        "banco": "",
        "agencia": "12a",
        "conta": "",
    }
    r = client.post("/api/solicitacao/alunos", json=dados)
    assert r.status_code == 422
    erros = r.json()["erros"]
    for esperado in (
        "Preencha todos os campos",
        "N. USP deve conter apenas números",
        "Número da agência deve conter apenas números",
        "Valor solicitado deve ser maior que 0",
        "E-mail inválido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert esperado in erros


def test_data_formato_certo_mas_inexistente():
    r = post("alunos", data_nascimento="01/13/1980")
    assert r.status_code == 422
    assert "Data de nascimento inválida" in r.json()["erros"]
