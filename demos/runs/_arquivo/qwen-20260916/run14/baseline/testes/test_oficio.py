from cartorio import Oficio, valida, oficio_docente, oficio_aluno, _moeda


BASE = {
    "nome": "Maria Aparecida da Silva",
    "nusp": "12345678",
    "programa": "Ciência da Computação",
    "email": "maria@usp.br",
    "evento_nome": "SBIA 2024",
    "evento_periodo": "15 a 19/07/2024",
    "evento_cidade": "Belo Horizonte",
    "evento_estado": "MG",
    "evento_pais": "Brasil",
    "valor": "150000",
    "detalhamento": "Participar do curso",
    "apresentacao": "Pôster",
    "nascimento": "01/02/1980",
    "logradouro": "Avenida Prof. Luciano Gualberto",
    "numero": "100",
    "bairro": "Butantã",
    "cep": "05508-090",
    "cidade": "São Paulo",
    "estado": "SP",
    "cpf": "529.982.247-25",
    "rg": "12.345.678-9",
    "banco": "Banco do Brasil",
    "agencia": "1234",
    "conta": "12345-6",
}


def aluno(**extra):
    dados = {"aba": "ALUNOS", "nivel": "Mestrado", "tipo_auxilio": "Participação em evento", **BASE, **extra}
    return Oficio(**dados)


def docente(**extra):
    dados = {"aba": "DOCENTES", **BASE, **extra}
    return Oficio(**dados)


def test_valido():
    assert valida(aluno()) == []
    assert valida(docente()) == []


def test_moeda():
    assert _moeda("1500") == "R$ 15,00"
    assert _moeda("150000") == "R$ 1.500,00"
    assert _moeda("150000000") == "R$ 1.500.000,00"


def test_campos_vazios():
    erros = valida(aluno(nome="", email="", programa=""))
    assert erros == ["Preencha todos os campos"]


def test_nusp_letras():
    assert "N. USP deve conter apenas números" in valida(aluno(nusp="12a34"))


def test_agencia_letras():
    assert "Número da agência deve conter apenas números" in valida(aluno(agencia="1a2"))


def test_valor_invalido():
    assert "Valor solicitado deve ser maior que 0" in valida(aluno(valor="0"))
    assert "Valor solicitado deve ser maior que 0" in valida(aluno(valor="R$ 15,00"))


def test_email_invalido():
    assert "E-mail inválido" in valida(aluno(email="maria@usp"))


def test_cpf_formato():
    assert "CPF deve estar no formato 000.000.000-00" in valida(aluno(cpf="52998224725"))


def test_cpf_digitos():
    assert "CPF inválido" in valida(aluno(cpf="529.982.247-26"))


def test_cep_formato():
    assert "CEP deve estar no formato 00000-000" in valida(aluno(cep="05508090"))


def test_data_formato():
    assert "Data de nascimento deve estar no formato dd/mm/aaaa" in valida(aluno(nascimento="1980-02-01"))


def test_data_inexistente():
    assert "Data de nascimento inválida" in valida(aluno(nascimento="29/02/2019"))


def test_oficio_docente():
    corpo = oficio_docente(docente())
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in corpo
    assert "Programa: Ciência da Computação\n" in corpo


def test_oficio_aluno():
    corpo = oficio_aluno(aluno())
    assert "Assunto: Solicitação de Auxílio Financeiro - Participação em evento" in corpo
    assert "Programa: Ciência da Computação - Mestrado\n" in corpo
    assert "Valor solicitado: R$ 1.500,00" in corpo


def test_linha_vazia_fora():
    corpo = oficio_docente(docente(complemento="", evento_link=""))
    assert "Link do evento:" not in corpo
    assert "Complemento:" not in corpo


def test_linha_cheia_dentro():
    corpo = oficio_docente(docente(complemento="Sala 5", evento_link="https://x.org"))
    assert "Complemento: Sala 5" in corpo
    assert "Link do evento: https://x.org" in corpo
