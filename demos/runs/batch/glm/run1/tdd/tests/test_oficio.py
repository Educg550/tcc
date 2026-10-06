ROTA = "/solicitacao"

ESPERADO_ALUNOS = [
    "Interessada(o): Maria da Silva Souza - 12345678",
    "E-mail: maria@ime.usp.br",
    "Assunto: Solicitação de Auxílio Financeiro - Participação em evento",
    "Programa: Matemática - Mestrado",
    "",
    "A CCP-Matemática aprovou na data de hoje, a solicitação de auxílio financeiro para a",
    "interessada(o) acima, conforme segue:",
    "",
    "Dados do evento",
    "Evento: Congresso Brasileiro de Matemática",
    "Período: 10 a 14 de julho de 2025",
    "Local: Porto Alegre - RS - Brasil",
    "Link do evento: https://cbm.exemplo.br",
    "Apresentação de trabalho: Pôster",
    "Valor solicitado: R$ 1.500,00",
    "Detalhamento: Inscrição no evento e passagens aéreas.",
    "",
    "Endereço da(o) interessada(o)",
    "Rua do Matão, 1010",
    "Complemento: Apto 21",
    "CEP: 05508-090",
    "Butantã, São Paulo - SP",
    "",
    "Dados para pagamento",
    "Data de nascimento: 01/02/1980",
    "CPF: 123.456.789-09",
    "RG / RNM: 12.345.678-9",
    "Banco: Banco do Brasil",
    "Agência: 1234",
    "Conta: 56789-0",
    "",
    "Encaminhe-se ao Serviço Financeiro para providências.",
]

ESPERADO_DOCENTES = [
    *ESPERADO_ALUNOS[:2],
    "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
    "Programa: Matemática",
    *ESPERADO_ALUNOS[4:],
]

ESPERADO_SEM_OPCIONAIS = [
    linha
    for linha in ESPERADO_ALUNOS
    if not linha.startswith(("Link do evento", "Complemento:"))
]


def _oficio(client, form):
    resposta = client.post(ROTA, json=form)
    assert resposta.status_code == 200
    return resposta.json()["oficio"]


def test_oficio_da_aba_alunos(client, form_alunos):
    oficio = _oficio(client, form_alunos)
    assert oficio.strip("\n").splitlines() == ESPERADO_ALUNOS


def test_oficio_da_aba_docentes(client, form_docentes):
    oficio = _oficio(client, form_docentes)
    assert oficio.strip("\n").splitlines() == ESPERADO_DOCENTES


def test_linhas_opcionais_vazias_somem_do_oficio(client, form_alunos):
    form_alunos["link"] = ""
    form_alunos["complemento"] = ""
    oficio = _oficio(client, form_alunos)
    assert oficio.strip("\n").splitlines() == ESPERADO_SEM_OPCIONAIS
