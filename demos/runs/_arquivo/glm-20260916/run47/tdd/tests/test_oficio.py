from conftest import campos

LINHAS = [
    'Interessada(o): Maria de Souza Silva - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'CCP-Ciência da Computação aprovou na data de hoje',
    'Evento: Simpósio Brasileiro de Computação',
    'Período: 10 a 15 de março de 2025',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://sbc.org.br/evento',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento',
    'Rua do Anfiteatro, 181',
    'Complemento: Sala 12',
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


def test_oficio_da_aba_alunos(post_solicitacao):
    resposta = post_solicitacao(campos(), LINHAS[0])
    for linha in LINHAS:
        assert linha in resposta.text, f'linha ausente do ofício: {linha}'


def test_oficio_da_aba_docentes(post_solicitacao):
    resposta = post_solicitacao(campos('docentes'), 'Verba do programa')
    texto = resposta.text
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'Programa: Ciência da Computação - Mestrado' not in texto
    assert LINHAS[0] in texto
    assert LINHAS[-1] in texto


def test_linhas_opcionais_saem_do_oficio_quando_vazias(post_solicitacao):
    resposta = post_solicitacao(
        campos(vazios=('link_evento', 'complemento')),
        'Encaminhe-se ao Serviço Financeiro',
    )
    texto = resposta.text
    assert 'Link do evento' not in texto
    assert 'Complemento' not in texto
    assert LINHAS[0] in texto


def test_confirmacao_mostra_solicitacao_registrada(post_solicitacao, html, js):
    resposta = post_solicitacao(campos(), 'Solicitação registrada')
    assert 'Solicitação registrada' in resposta.text + html + js
