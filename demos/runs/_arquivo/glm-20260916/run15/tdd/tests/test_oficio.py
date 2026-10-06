LINHAS_DO_OFICIO = [
    "Interessada(o): Maria da Silva - 1234567",
    "E-mail: maria@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Doutorado",
    "A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro",
    "interessada(o) acima, conforme segue:",
    "Dados do evento",
    "Evento: SBBD",
    "Período: 20 a 23 de outubro de 2025",
    "Local: São Paulo - SP - Brasil",
    "Link do evento: sbbd.org.br",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Passagem aérea e inscrição",
    "Endereço da(o) interessada(o)",
    "Rua do Anfiteatro, 181",
    "Complemento: Sala 224",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 0001",
    "Conta: 12345-6",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def test_oficio_da_aba_alunos_com_tudo_preenchido(enviar_alunos):
    texto = enviar_alunos()
    for linha in LINHAS_DO_OFICIO:
        assert linha in texto, f"não apareceu no ofício: {linha}"
    assert "Interessada(o): Maria da Silva - 1234567\nE-mail: maria@usp.br" in texto
    marcos = [
        "Assunto:",
        "aprovou na data de hoje",
        "Dados do evento",
        "Endereço da(o) interessada(o)",
        "Dados para pagamento",
        "Encaminhe-se ao Serviço Financeiro",
    ]
    posicoes = [texto.index(marco) for marco in marcos]
    assert posicoes == sorted(posicoes)


def test_campos_opcionais_vazios_saem_do_oficio(enviar_alunos):
    texto = enviar_alunos(
        {
            "LINK DO EVENTO, EXAME OU DEFESA": "",
            "COMPLEMENTO": "",
        }
    )
    assert "Evento: SBBD" in texto
    assert "Link do evento" not in texto
    assert "Complemento" not in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto


def test_oficio_da_aba_docentes_usa_verba_do_programa(enviar_docentes):
    texto = enviar_docentes()
    assert "Interessada(o): Maria da Silva - 1234567" in texto
    assert "Assunto: Solicitação de Auxílio Financeiro - Verba do programa" in texto
    assert "Programa: Ciência da Computação" in texto
    assert "Programa: Ciência da Computação - " not in texto
    assert "Encaminhe-se ao Serviço Financeiro para providências." in texto
