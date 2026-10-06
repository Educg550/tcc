from conftest import ALUNOS_VALIDOS, DOCENTES_VALIDOS, assert_oficio


TRECHOS_DO_OFICIO = [
    "Interessada(o): Maria da Silva - 1234567",
    "E-mail: maria.silva@usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Ciência da Computação - Mestrado",
    "A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:",
    "Dados do evento",
    "Evento: Congresso Brasileiro de Computação",
    "Período: 10/09/2025 a 15/09/2025",
    "Local: Rio de Janeiro - RJ - Brasil",
    "Link do evento: https://evento.exemplo.org/2025",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Passagens aéreas e inscrição no evento.",
    "Endereço da(o) interessada(o)",
    "Rua do Anfiteatro, 181",
    "Complemento: Biomédicas 4",
    "CEP: 05508-090",
    "Cidade Universitária, São Paulo - SP",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 98765-4",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]


def test_oficio_do_aluno(enviar):
    assert_oficio(enviar(ALUNOS_VALIDOS), TRECHOS_DO_OFICIO)


def test_oficio_do_docente(enviar):
    trechos = [
        trecho.replace(
            "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
        ).replace(
            "Programa: Ciência da Computação - Mestrado",
            "Programa: Ciência da Computação",
        )
        for trecho in TRECHOS_DO_OFICIO
    ]
    texto = assert_oficio(enviar(DOCENTES_VALIDOS), trechos)
    assert "Mestrado" not in texto
    assert "Participação em evento" not in texto


def test_linhas_de_campos_opcionais_vazias_saem_do_oficio(enviar):
    payload = {
        **ALUNOS_VALIDOS,
        "LINK DO EVENTO, EXAME OU DEFESA": "",
        "COMPLEMENTO": "",
    }
    texto = assert_oficio(enviar(payload), [
        "Local: Rio de Janeiro - RJ - Brasil",
        "Rua do Anfiteatro, 181",
        "CEP: 05508-090",
        "Cidade Universitária, São Paulo - SP",
    ])
    assert "Link do evento:" not in texto
    assert "Complemento:" not in texto


def test_valor_solicitado_aparece_formatado_no_oficio(enviar):
    payload = {**ALUNOS_VALIDOS, "VALOR SOLICITADO (R$)": "R$ 12.345,67"}
    assert_oficio(enviar(payload), ["Valor solicitado: R$ 12.345,67"])
