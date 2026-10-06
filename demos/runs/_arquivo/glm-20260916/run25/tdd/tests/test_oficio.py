LINHAS_ALUNOS = [
    "Interessada(o): Maria de Souza - 8765432",
    "E-mail: maria.souza@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "CCP-Ciência da Computação aprovou na data de hoje",
    "Dados do evento",
    "Evento: SBES 2025",
    "Período: 20 a 24 de outubro de 2025",
    "Local: Salvador - BA - Brasil",
    "Link do evento: https://sbes2025.example.br",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição e passagens para o evento.",
    "Endereço da(o) interessada(o)",
    "Rua do Anfiteatro, 181",
    "Complemento: Sala 5",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1990",
    "CPF: 111.444.777-35",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 98765-4",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def test_oficio_da_aba_alunos(solicitar, contem):
    oficio, erros = solicitar()
    assert erros in (None, [])
    assert oficio
    for linha in LINHAS_ALUNOS:
        assert contem(oficio, linha), f"não encontrei no ofício: {linha}"


def test_oficio_da_aba_docentes(solicitar, contem):
    oficio, erros = solicitar(aba="DOCENTES")
    assert erros in (None, [])
    assert oficio
    assert contem(oficio, "Interessada(o): Maria de Souza - 8765432")
    assert contem(oficio, "Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
    assert contem(oficio, "Programa: Ciência da Computação")
    assert contem(oficio, "Encaminhe-se ao Serviço Financeiro para providências.")
    assert not contem(oficio, "Mestrado")
    assert not contem(oficio, "Participação em evento")


def test_linhas_opcionais_saem_quando_vazias(solicitar, contem):
    oficio, erros = solicitar(trocas={"link": "", "complemento": ""})
    assert erros in (None, [])
    assert oficio
    assert not contem(oficio, "Link do evento:")
    assert not contem(oficio, "Complemento:")
    assert contem(oficio, "CEP: 05508-090")
    assert contem(oficio, "Butantã, São Paulo - SP")
