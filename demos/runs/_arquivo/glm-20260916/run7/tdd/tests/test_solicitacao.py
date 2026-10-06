OFICIO = [
    'Interessada(o): Maria de Souza Silva - 1234567',
    'E-mail: maria.silva@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou na data de hoje,',
    'a solicitação de auxílio financeiro para a',
    'interessada(o) acima, conforme segue:',
    'Dados do evento',
    'Evento: SBBD',
    'Período: 30/09/2025 a 03/10/2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://sbbd.org.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Inscrição e passagem aérea.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 155',
    'Complemento: Sala 101',
    'CEP: 05508-090',
    'Butantã, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 12345-6',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


def test_oficio_de_aluno(montar, enviar):
    conteudo = enviar(montar('alunos'), 'Interessada(o): Maria de Souza Silva - 1234567')
    posicoes = []
    for linha in OFICIO:
        posicao = conteudo.find(linha)
        assert posicao != -1, f'linha ausente do ofício: {linha}'
        posicoes.append(posicao)
    assert posicoes == sorted(posicoes)
    assert '<<' not in conteudo
    assert '>>' not in conteudo


def test_oficio_de_docente(montar, enviar):
    assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
    conteudo = enviar(montar('docentes'), assunto)
    if assunto not in conteudo:
        conteudo = enviar(montar('docentes', nivel='', tipo_auxilio=''), assunto)
    assert assunto in conteudo
    assert 'Programa: Ciência da Computação' in conteudo
    assert 'Mestrado' not in conteudo
    assert 'Participação em evento' not in conteudo
    assert 'Interessada(o): Maria de Souza Silva - 1234567' in conteudo
    assert 'Valor solicitado: R$ 1.500,00' in conteudo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in conteudo


def test_opcionais_vazios_saem_do_oficio(montar, enviar):
    conteudo = enviar(
        montar('alunos', link='', complemento=''),
        'Interessada(o): Maria de Souza Silva - 1234567',
    )
    assert 'Link do evento' not in conteudo
    assert 'Complemento' not in conteudo
    assert 'CEP: 05508-090' in conteudo
    assert 'Período: 30/09/2025 a 03/10/2025' in conteudo


def _recusa(montar, enviar, mensagem, **alteracoes):
    conteudo = enviar(montar('alunos', **alteracoes), mensagem)
    assert mensagem in conteudo, f'esperado {mensagem} na resposta: {conteudo[:300]}'
    assert 'Interessada(o):' not in conteudo


def test_campo_obrigatorio_vazio_uma_unica_vez(montar, enviar):
    conteudo = enviar(montar('alunos', nome='', programa='', banco=''), 'Preencha todos os campos')
    assert conteudo.count('Preencha todos os campos') == 1
    assert 'Interessada(o):' not in conteudo


def test_n_usp_so_numeros(montar, enviar):
    _recusa(montar, enviar, 'N. USP deve conter apenas números', n_usp='abc123')


def test_agencia_so_numeros(montar, enviar):
    _recusa(montar, enviar, 'Número da agência deve conter apenas números', agencia='12a4')


def test_valor_maior_que_zero(montar, enviar):
    _recusa(montar, enviar, 'Valor solicitado deve ser maior que 0', valor='0')


def test_email_invalido(montar, enviar):
    _recusa(montar, enviar, 'E-mail inválido', email='maria.silva.usp.br')


def test_cpf_fora_do_formato(montar, enviar):
    _recusa(montar, enviar, 'CPF deve estar no formato 000.000.000-00', cpf='12345678')


def test_cpf_com_dv_errado(montar, enviar):
    _recusa(montar, enviar, 'CPF inválido', cpf='123.456.789-10')


def test_cep_fora_do_formato(montar, enviar):
    _recusa(montar, enviar, 'CEP deve estar no formato 00000-000', cep='0550809')


def test_data_fora_do_formato(montar, enviar):
    _recusa(montar, enviar, 'Data de nascimento deve estar no formato dd/mm/aaaa', nascimento='1/2/1980')


def test_data_inexistente(montar, enviar):
    _recusa(montar, enviar, 'Data de nascimento inválida', nascimento='31/02/1980')


def test_todas_as_mensagens_de_uma_vez(montar, enviar):
    conteudo = enviar(
        montar(
            'alunos',
            n_usp='abc123',
            agencia='12a4',
            email='maria.silva.usp.br',
            cpf='12345678',
            cep='0550809',
            nascimento='1/2/1980',
            valor='0',
        ),
        'N. USP deve conter apenas números',
    )
    for mensagem in (
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF deve estar no formato 000.000.000-00',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento deve estar no formato dd/mm/aaaa',
    ):
        assert mensagem in conteudo, f'mensagem ausente: {mensagem}'
    assert 'Preencha todos os campos' not in conteudo
    assert 'Interessada(o):' not in conteudo
