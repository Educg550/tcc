from fastapi.testclient import TestClient

from app import app


client = TestClient(app)

ALUNOS = {
    "aba": "ALUNOS",
    "nome": "Maria da Silva",
    "nuspp": "1234567",
    "programa": "Matemática",
    "nivel": "Mestrado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "evento": "CBM 2024",
    "periodo": "01/07/2024 a 05/07/2024",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://cbm.org",
    "valor": 1500,
    "detalhamento": "Participar das sessões",
    "apresentacao": "Pôster",
    "data_nascimento": "01/02/1980",
    "logradouro": "Rua do Matão",
    "numero": "1010",
    "complemento": "Casa 3",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-X",
}

DOCENTES = {
    "aba": "DOCENTES",
    "nome": "José dos Santos",
    "nuspp": "9876543",
    "programa": "Estatística",
    "email": "jose@ime.usp.br",
    "evento": "Seminário de Estatística",
    "periodo": "10/08/2024",
    "cidade_evento": "Campinas",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "https://seminario.org",
    "valor": 20000,
    "detalhamento": "Ministrar palestra",
    "apresentacao": "Apresentação oral",
    "data_nascimento": "15/03/1975",
    "logradouro": "Avenida Paulista",
    "numero": "1000",
    "complemento": "Apto 2",
    "bairro": "Bela Vista",
    "cep": "01310-100",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "9.876.543-2",
    "banco": "Caixa Econômica Federal",
    "agencia": "5678",
    "conta": "12345-6",
}


def _post(payload):
    resp = client.post("/solicitar", json=payload)
    assert resp.status_code == 200
    return resp.json()


def test_envio_valido_alunos():
    body = _post(ALUNOS)
    assert "Interessada(o): Maria da Silva - 1234567" in body["oficio"]


def test_envio_valido_docentes():
    body = _post(DOCENTES)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in body["oficio"]


def test_valor_formatado_no_oficio():
    body = _post(ALUNOS)
    assert "R$ 15,00" in body["oficio"]


def test_linha_link_ausente_quando_vazio():
    body = _post({**ALUNOS, "link_evento": ""})
    assert "Link do evento:" not in body["oficio"]


def test_linha_complemento_ausente_quando_vazio():
    body = _post({**ALUNOS, "complemento": ""})
    assert "Complemento:" not in body["oficio"]


def test_oficio_contem_todas_linhas():
    body = _post(ALUNOS)
    for trecho in (
        "Interessada(o): Maria da Silva - 1234567",
        "E-mail: maria@ime.usp.br",
        "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
        "Programa: Matemática - Mestrado",
        "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "Dados do evento",
        "Evento: CBM 2024",
        "Período: 01/07/2024 a 05/07/2024",
        "Local: São Paulo - SP - Brasil",
        "Link do evento: https://cbm.org",
        "Apresentação de trabalho: Pôster",
        "Valor solicitado: R$ 15,00",
        "Detalhamento: Participar das sessões",
        "Endereço da(o) interessada(o)",
        "Rua do Matão, 1010",
        "Complemento: Casa 3",
        "CEP: 05508-090",
        "Butantã, São Paulo - SP",
        "Dados para pagamento",
        "Data de nascimento: 01/02/1980",
        "CPF: 123.456.789-09",
        "RG / RNM: 12.345.678-9",
        "Banco: Banco do Brasil",
        "Agência: 1234",
        "Conta: 56789-X",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ):
        assert trecho in body["oficio"]


def test_oficio_docentes_tem_linhas_certas():
    body = _post(DOCENTES)
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in body["oficio"]
    assert "Programa: Estatística" in body["oficio"]
    assert "Programa: Estatística -" not in body["oficio"]
    assert "Nível" not in body["oficio"]
    assert "Valor solicitado: R$ 200,00" in body["oficio"]
    assert "Interessada(o): José dos Santos - 9876543" in body["oficio"]


def _erro_campos(payload, campo, valor, mensagem):
    body = _post({**payload, campo: valor})
    assert mensagem in body["erros"]
    assert body.get("oficio") is None


def _erros(payload, **campos):
    body = _post({**payload, **campos})
    return body["erros"]


def test_erro_campos_vazios():
    assert "Preencha todos os campos" in _erros(ALUNOS, nome="")


def test_erro_campos_vazios_nao_repetido():
    erros = _erros(ALUNOS, nome="", programa="")
    assert erros.count("Preencha todos os campos") == 1


def test_erro_nuspp_com_letras():
    _erro_campos(ALUNOS, "nuspp", "123A", "N. USP deve conter apenas números")


def test_erro_agencia_com_letras():
    _erro_campos(ALUNOS, "agencia", "12A4", "Número da agência deve conter apenas números")


def test_erro_valor_zero():
    _erro_campos(ALUNOS, "valor", 0, "Valor solicitado deve ser maior que 0")


def test_erro_valor_negativo():
    _erro_campos(ALUNOS, "valor", -5, "Valor solicitado deve ser maior que 0")


def test_erro_email_invalido():
    _erro_campos(ALUNOS, "email", "maria", "E-mail inválido")


def test_erro_formato_cpf():
    _erro_campos(ALUNOS, "cpf", "12345678909", "CPF deve estar no formato 000.000.000-00")


def test_erro_formato_cep():
    _erro_campos(ALUNOS, "cep", "05508090", "CEP deve estar no formato 00000-000")


def test_erro_formato_data():
    _erro_campos(ALUNOS, "data_nascimento", "01021980", "Data de nascimento deve estar no formato dd/mm/aaaa")


def test_erro_digito_verificador_cpf():
    _erro_campos(ALUNOS, "cpf", "111.111.111-11", "CPF inválido")


def test_erro_data_inexistente():
    _erro_campos(ALUNOS, "data_nascimento", "30/02/1980", "Data de nascimento inválida")


def test_erros_multiplos_juntos():
    erros = _erros(ALUNOS, cep="", cpf="", valor=0)
    assert "Preencha todos os campos" in erros
    assert "Valor solicitado deve ser maior que 0" in erros


def test_validacao_igual_docentes():
    _erro_campos(DOCENTES, "cep", "", "Preencha todos os campos")
    _erro_campos(DOCENTES, "nuspp", "x", "N. USP deve conter apenas números")


def test_oficio_nao_gerado_com_erro():
    body = _post({**ALUNOS, "cpf": "111.111.111-11"})
    assert "Interessada(o)" not in body.get("oficio", "")
