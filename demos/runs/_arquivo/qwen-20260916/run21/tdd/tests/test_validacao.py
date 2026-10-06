from conftest import _cliente


BASE = {
    "aba": "alunos",
    "nome": "Maria Silva",
    "nusp": "1234567",
    "programa": "Matemática",
    "nivel": "Doutorado",
    "tipo_auxilio": "Participação em evento",
    "email": "maria@ime.usp.br",
    "nome_evento": "Congresso",
    "periodo": "01/05 a 05/05",
    "cidade_evento": "São Paulo",
    "estado_evento": "SP",
    "pais_evento": "Brasil",
    "link_evento": "",
    "valor": 150000,
    "detalhamento": "Detalhes",
    "apresenta": "Pôster",
    "nascimento": "01/02/1980",
    "logradouro": "Rua A",
    "numero": "100",
    "complemento": "",
    "bairro": "Centro",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "123.456.789-09",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "56789-0",
}

CPF_VALIDO = "111.444.777-35"


def _erro(campo, valor, aba="alunos"):
    dados = dict(BASE, aba=aba, **{campo: valor})
    resp = _cliente().post("/solicitacao", json=dados)
    assert resp.status_code == 200
    erros = resp.json().get("erros", [])
    assert "oficio" not in resp.json()
    return erros


def teste_vazio():
    assert "Preencha todos os campos" in _erro("nome", "")


def teste_nusp_letras():
    assert "N. USP deve conter apenas números" in _erro("nusp", "abc")


def teste_agencia_letras():
    assert "Número da agência deve conter apenas números" in _erro("agencia", "abc")


def teste_valor_zero():
    assert "Valor solicitado deve ser maior que 0" in _erro("valor", 0)


def teste_valor_negativo():
    assert "Valor solicitado deve ser maior que 0" in _erro("valor", -5)


def teste_email_invalido():
    assert "E-mail inválido" in _erro("email", "maria@")


def teste_email_sem_arroba():
    assert "E-mail inválido" in _erro("email", "mariame.usp.br")


def teste_cpf_formato():
    assert "CPF deve estar no formato 000.000.000-00" in _erro("cpf", "12345678909")


def teste_cep_formato():
    assert "CEP deve estar no formato 00000-000" in _erro("cep", "05508090")


def teste_data_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in _erro("nascimento", "1-2-1980")


def teste_cpf_digitos():
    assert "CPF inválido" in _erro("cpf", "123.456.789-09")


def teste_data_inexistente():
    assert "Data de nascimento inválida" in _erro("nascimento", "31/02/1980")


def teste_mes_invalido():
    assert "Data de nascimento inválida" in _erro("nascimento", "01/13/1980")


def teste_validos_sem_erros():
    resp = _cliente().post("/solicitacao", json=dict(BASE, cpf=CPF_VALIDO))
    assert resp.json().get("erros") in ([], None)
    assert "oficio" in resp.json()
