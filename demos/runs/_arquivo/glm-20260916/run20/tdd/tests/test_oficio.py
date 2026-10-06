from conftest import texto_da_resposta

LINHAS_DO_OFICIO = [
    'Interessada(o): Maria da Silva - 9876543',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'aprovou na data de hoje',
    'Dados do evento',
    'Evento: Simpósio Brasileiro de Banco de Dados',
    'Período: 23 a 26 de setembro de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://sbbd.org.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Letra D',
    'CEP: 05508-090',
    'Butantã, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


def _escolher(respostas, com_verba):
    corpos = []
    for resposta in respostas:
        corpo = texto_da_resposta(resposta)
        if 'Interessada(o):' in corpo and ('Verba do programa' in corpo) == com_verba:
            corpos.append(corpo)
    return corpos


def test_oficio_do_aluno(enviar):
    respostas = enviar()
    corpos = _escolher(respostas, com_verba=False)
    assert corpos, 'envio válido de aluno não gerou ofício: %r' % [
        texto_da_resposta(r)[:300] for r in respostas]
    corpo = corpos[0]
    posicao = 0
    for linha in LINHAS_DO_OFICIO:
        achou = corpo.find(linha, posicao)
        assert achou != -1, 'linha ausente ou fora de ordem no ofício: %r' % linha
        posicao = achou + 1


def test_linhas_opcionais_saem_do_oficio_quando_vazias(enviar):
    respostas = enviar({'link': '', 'complemento': ''})
    corpos = _escolher(respostas, com_verba=False)
    assert corpos, 'envio válido sem opcionais não gerou ofício'
    corpo = corpos[0]
    assert 'Link do evento:' not in corpo
    assert 'Complemento:' not in corpo
    assert 'CEP: 05508-090' in corpo
    assert 'Valor solicitado: R$ 1.500,00' in corpo


def test_oficio_do_docente(enviar):
    respostas = enviar(aba='DOCENTES')
    corpos = _escolher(respostas, com_verba=True)
    assert corpos, 'envio válido de docente não gerou ofício: %r' % [
        texto_da_resposta(r)[:300] for r in respostas]
    corpo = corpos[0]
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in corpo
    assert 'Programa: Ciência da Computação' in corpo
    assert 'Mestrado' not in corpo
    assert 'Participação em evento' not in corpo
