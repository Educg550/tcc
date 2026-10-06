from conftest import enviar, payload_de_aluno

TRECHOS_DO_OFICIO = [
    'Interessada(o): Maria da Silva - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou',
    'Evento: Congresso Brasileiro de Computação',
    'Período: 1 a 5 de julho de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://evento.usp.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Rua do Anfiteatro, 123',
    'Complemento: Sala 5',
    'CEP: 05508-090',
    'Butantã, São Paulo - SP',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


def test_envio_valido_de_aluno_gera_oficio(client, nomes):
    resposta = enviar(client, payload_de_aluno(nomes))
    assert resposta.status_code < 300
    for trecho in TRECHOS_DO_OFICIO:
        assert trecho in resposta.text, trecho


def test_envio_valido_de_docente_gera_oficio(client, nomes):
    payload = payload_de_aluno(nomes)
    del payload[nomes['NÍVEL']]
    del payload[nomes['TIPO DE AUXÍLIO']]
    resposta = enviar(client, payload)
    assert resposta.status_code < 300
    texto = resposta.text
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'Programa: Ciência da Computação - Mestrado' not in texto
    assert 'Interessada(o): Maria da Silva - 1234567' in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto


def test_campos_opcionais_vazios_nao_aparecem_no_oficio(client, nomes):
    payload = payload_de_aluno(nomes)
    payload[nomes['LINK DO EVENTO, EXAME OU DEFESA']] = ''
    payload[nomes['COMPLEMENTO']] = ''
    texto = enviar(client, payload).text
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto
    assert 'Valor solicitado: R$ 1.500,00' in texto
    assert 'CEP: 05508-090' in texto
