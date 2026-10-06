TRECHOS_ALUNOS = [
    'Interessada(o): Maria Antonieta da Silva - 8765432',
    'E-mail: maria.antonieta@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'interessada(o) acima, conforme segue:',
    'Dados do evento',
    'Evento: Simpósio Internacional de Banco de Dados',
    'Período: 10/03/2026 a 14/03/2026',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://simposio.example.org',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 101',
    'Complemento: Sala 12',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]

TRECHOS_DOCENTES = [
    'Interessada(o): Maria Antonieta da Silva - 8765432',
    'E-mail: maria.antonieta@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
    'Programa: Ciência da Computação',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'interessada(o) acima, conforme segue:',
    'Dados do evento',
    'Evento: Simpósio Internacional de Banco de Dados',
    'Período: 10/03/2026 a 14/03/2026',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://simposio.example.org',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 101',
    'Complemento: Sala 12',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]

TRECHOS_SEM_OPCIONAIS = [
    trecho
    for trecho in TRECHOS_ALUNOS
    if trecho not in (
        'Link do evento: https://simposio.example.org',
        'Complemento: Sala 12',
    )
]


def verificar_em_ordem(texto, trechos):
    posicao = 0
    for trecho in trechos:
        indice = texto.find(trecho, posicao)
        assert indice != -1, f'trecho ausente ou fora de ordem no ofício: {trecho!r}'
        posicao = indice + len(trecho)


def test_oficio_da_aba_alunos(enviar, payload_alunos, oficio):
    resposta = enviar(payload_alunos)
    assert 200 <= resposta.status_code < 300
    verificar_em_ordem(oficio(resposta), TRECHOS_ALUNOS)


def test_oficio_da_aba_docentes(enviar, payload_docentes, oficio):
    resposta = enviar(payload_docentes)
    assert 200 <= resposta.status_code < 300
    texto = oficio(resposta)
    verificar_em_ordem(texto, TRECHOS_DOCENTES)
    assert 'Mestrado' not in texto
    assert 'Doutorado' not in texto
    assert 'Participação em evento' not in texto


def test_linhas_de_opcionais_vazios_saem_do_oficio(enviar, payload_alunos, oficio):
    payload_alunos['link_evento'] = ''
    payload_alunos['complemento'] = ''
    texto = oficio(enviar(payload_alunos))
    assert 'Link do evento' not in texto
    assert 'Complemento' not in texto
    verificar_em_ordem(texto, TRECHOS_SEM_OPCIONAIS)
