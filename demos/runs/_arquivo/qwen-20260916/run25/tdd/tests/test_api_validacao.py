from conftest import client


def alunos(**campos):
    corpo = {
        "nome": "Maria Silva Souza",
        "nusp": "1234567",
        "programa": "Ci\u00eancia da Computa\u00e7\u00e3o",
        "nivel": "Doutorado",
        "tipo_auxilio": "Participa\u00e7\u00e3o em evento",
        "email": "maria@ime.usp.br",
        "evento": "XVII SBC",
        "periodo": "10 a 14 de julho de 2025",
        "cidade_evento": "Belo Horizonte",
        "estado_evento": "MG",
        "pais_evento": "Brasil",
        "link": "https://sbc.org.br",
        "valor": "150000",
        "detalhamento": "Participa\u00e7\u00e3o com apresenta\u00e7\u00e3o de trabalho.",
        "apresentacao": "P\u00f4ster",
        "nascimento": "01/02/1980",
        "logradouro": "Rua do Mat\u00e3o",
        "numero": "1010",
        "complemento": "Bloco C",
        "bairro": "Cidade Universit\u00e1ria",
        "cep": "05508-090",
        "cidade": "S\u00e3o Paulo",
        "estado": "SP",
        "cpf": "123.456.789-09",
        "rg": "12.345.678-9",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
    }
    corpo.update(campos)
    return corpo


def docentes(**campos):
    corpo = alunos(nivel=None, tipo_auxilio=None)
    corpo.update(campos)
    return corpo


def erros(resposta):
    return resposta.json()["erros"]


def test_campos_de_alunos_sao_lidos_pelo_backend():
    resposta = client().post("/solicitacao", json=alunos())
    assert resposta.status_code == 200
    assert resposta.json()["erros"] == []


def test_campos_de_docentes_sao_lidos_pelo_backend():
    resposta = client().post("/solicitacao", json=docentes())
    assert resposta.status_code == 200
    assert resposta.json()["erros"] == []


def test_obrigatorio_vazio_mostra_mensagem_unica():
    resposta = client().post("/solicitacao", json=alunos(nome="", bairro=""))
    assert erros(resposta) == ["Preencha todos os campos"]


def test_nusp_so_digitos():
    resposta = client().post("/solicitacao", json=alunos(nusp="12a3"))
    assert "N. USP deve conter apenas n\u00fameros" in erros(resposta)


def test_agencia_so_digitos():
    resposta = client().post("/solicitacao", json=alunos(agencia="12-3"))
    assert "N\u00famero da ag\u00eancia deve conter apenas n\u00fameros" in erros(resposta)


def test_valor_deve_ser_natural_maior_que_zero():
    assert "Valor solicitado deve ser maior que 0" in erros(
        client().post("/solicitacao", json=alunos(valor="0"))
    )
    assert "Valor solicitado deve ser maior que 0" in erros(
        client().post("/solicitacao", json=alunos(valor="-1500"))
    )
    assert "Valor solicitado deve ser maior que 0" in erros(
        client().post("/solicitacao", json=alunos(valor="15,5"))
    )


def test_email_sem_arroba_ou_sem_dominio():
    assert "E-mail inv\u00e1lido" in erros(client().post("/solicitacao", json=alunos(email="maria@")))
    assert "E-mail inv\u00e1lido" in erros(client().post("/solicitacao", json=alunos(email="maria.usp.br")))


def test_cpf_formato():
    assert "CPF deve estar no formato 000.000.000-00" in erros(
        client().post("/solicitacao", json=alunos(cpf="12345678909"))
    )


def test_cep_formato():
    assert "CEP deve estar no formato 00000-000" in erros(
        client().post("/solicitacao", json=alunos(cep="05508090"))
    )


def test_data_nascimento_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in erros(
        client().post("/solicitacao", json=alunos(nascimento="01-02-1980"))
    )


def test_digito_verificador_de_cpf():
    assert "CPF inv\u00e1lido" in erros(
        client().post("/solicitacao", json=alunos(cpf="123.456.789-00"))
    )


def test_data_nascimento_inexistente():
    assert "Data de nascimento inv\u00e1lida" in erros(
        client().post("/solicitacao", json=alunos(nascimento="31/02/1980"))
    )
    assert "Data de nascimento inv\u00e1lida" in erros(
        client().post("/solicitacao", json=alunos(nascimento="13/01/1980"))
    )


def test_todas_as_mensagens_aparecem_juntas():
    resposta = client().post(
        "/solicitacao",
        json=alunos(nusp="a", email="x", cpf="000.000.000-00", cep="1", nascimento="99/99/9999"),
    )
    for mensagem in (
        "N. USP deve conter apenas n\u00fameros",
        "E-mail inv\u00e1lido",
        "CPF deve estar no formato 000.000.000-00",
        "CEP deve estar no formato 00000-000",
        "Data de nascimento deve estar no formato dd/mm/aaaa",
    ):
        assert mensagem in erros(resposta)


def test_sem_erros_devolve_oficio():
    resposta = client().post("/solicitacao", json=alunos())
    assert resposta.json()["erros"] == []
    assert "oficio" in resposta.json()
