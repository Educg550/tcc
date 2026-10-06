LINHAS_DO_OFICIO = [
    'Interessada(o): Maria Aparecida de Souza Oliveira - 1234567',
    'E-mail: maria.oliveira@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'interessada(o) acima, conforme segue:',
    'Dados do evento',
    'Evento: Congresso Brasileiro de Computação',
    'Período: 10/06/2025 a 14/06/2025',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://congresso.example.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Inscrição no evento e passagem aérea de ida e volta.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 375',
    'Complemento: Sala 12',
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


def test_oficio_da_aba_alunos(enviar, contem):
    resposta = enviar('alunos')
    for linha in LINHAS_DO_OFICIO:
        assert contem(resposta, linha), f'não apareceu no ofício: {linha}'


def test_oficio_da_aba_docentes(enviar, contem, textos):
    resposta = enviar('docentes')
    assert contem(resposta, 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
    assert contem(resposta, 'Programa: Ciência da Computação')
    assert not any('Programa: Ciência da Computação -' in texto for texto in textos(resposta))
    assert contem(resposta, 'Valor solicitado: R$ 1.500,00')
    assert contem(resposta, 'Interessada(o): Maria Aparecida de Souza Oliveira - 1234567')
    assert contem(resposta, 'Encaminhe-se ao Serviço Financeiro para providências.')


def test_a_confirmacao_tem_o_titulo(enviar, cliente, pagina, js):
    resposta = enviar('alunos')
    candidatos = [pagina, js, resposta.text]
    assert any('Solicitação registrada' in candidato for candidato in candidatos)


def test_campos_opcionais_vazios_sao_aceitos_e_suas_linhas_saem_do_oficio(enviar, contem, textos):
    resposta = enviar('alunos', link_evento='', complemento='')
    assert contem(resposta, 'Encaminhe-se ao Serviço Financeiro para providências.')
    unido = ' '.join(textos(resposta))
    assert 'Link do evento' not in unido
    assert 'Complemento' not in unido


def test_a_validacao_vale_tambem_na_aba_docentes(enviar, contem):
    assert contem(enviar('docentes', cpf='123.456.789-00'), 'CPF inválido')
