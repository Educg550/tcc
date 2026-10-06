LINHAS_DO_OFICIO_DE_ALUNOS = [
    'Interessada(o): Maria de Souza Silva - 1234567',
    'E-mail: maria.ss@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Doutorado',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'Evento: Simpósio Brasileiro de Computação',
    'Período: 10 a 15 de agosto de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://eventos.usp.br/simposio',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Inscrição no evento e passagem aérea',
    'Rua do Anfiteatro, 181',
    'Complemento: Bloco A',
    'CEP: 05508-090',
    'Butantã, São Paulo - SP',
    'Data de nascimento: 01/02/1990',
    'CPF: 111.444.777-35',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


def test_solicitacao_valida_de_aluno_gera_oficio(submeter, dados_alunos):
    corpo = submeter(dados_alunos())
    for linha in LINHAS_DO_OFICIO_DE_ALUNOS:
        assert linha in corpo, f'linha ausente no ofício: {linha}'
    assert '<<' not in corpo and '>>' not in corpo
    assert 'Preencha todos os campos' not in corpo


def test_solicitacao_valida_de_docente_gera_oficio(submeter, dados_docentes):
    corpo = submeter(dados_docentes())
    assert 'Interessada(o): Maria de Souza Silva - 1234567' in corpo
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in corpo
    assert 'Programa: Ciência da Computação' in corpo
    assert 'Doutorado' not in corpo
    assert 'Valor solicitado: R$ 1.500,00' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo
    assert '<<' not in corpo and '>>' not in corpo


def test_linhas_de_campos_opcionais_vazios_saem_do_oficio(submeter, dados_alunos):
    corpo = submeter(
        dados_alunos(**{'LINK DO EVENTO, EXAME OU DEFESA': '', 'COMPLEMENTO': ''})
    )
    assert 'Link do evento' not in corpo
    assert 'Complemento' not in corpo
    assert 'Rua do Anfiteatro, 181' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo


def test_todos_os_campos_vazios_pede_preenchimento_uma_vez(submeter, dados_alunos):
    vazios = {campo: '' for campo in dados_alunos()}
    corpo = submeter(vazios)
    assert corpo.count('Preencha todos os campos') == 1
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_n_usp_deve_conter_apenas_numeros(submeter, dados_alunos):
    corpo = submeter(dados_alunos(**{'N. USP': '12A4567'}))
    assert 'N. USP deve conter apenas números' in corpo
    assert 'Preencha todos os campos' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_numero_da_agencia_deve_conter_apenas_numeros(submeter, dados_alunos):
    corpo = submeter(dados_alunos(**{'NÚMERO DA AGÊNCIA': '12A4'}))
    assert 'Número da agência deve conter apenas números' in corpo
    assert 'Preencha todos os campos' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_valor_solicitado_deve_ser_maior_que_zero(submeter, dados_alunos):
    corpo = submeter(dados_alunos(**{'VALOR SOLICITADO (R$)': 'R$ 0,00'}))
    assert 'Valor solicitado deve ser maior que 0' in corpo
    assert 'Preencha todos os campos' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_email_invalido(submeter, dados_alunos):
    for email in ('maria.ss.usp.br', 'maria.ss@'):
        corpo = submeter(dados_alunos(**{'E-MAIL': email}))
        assert 'E-mail inválido' in corpo


def test_cpf_fora_do_formato(submeter, dados_alunos):
    corpo = submeter(
        dados_alunos(**{'CPF (SEPARADOS POR PONTOS E TRAÇO)': '11122233344'})
    )
    assert 'CPF deve estar no formato 000.000.000-00' in corpo
    assert 'Preencha todos os campos' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_cpf_com_digitos_verificadores_errados(submeter, dados_alunos):
    corpo = submeter(
        dados_alunos(**{'CPF (SEPARADOS POR PONTOS E TRAÇO)': '111.444.777-34'})
    )
    assert 'CPF inválido' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_cep_fora_do_formato(submeter, dados_alunos):
    corpo = submeter(dados_alunos(**{'CEP': '05508090'}))
    assert 'CEP deve estar no formato 00000-000' in corpo
    assert 'Preencha todos os campos' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_data_de_nascimento_fora_do_formato(submeter, dados_alunos):
    corpo = submeter(dados_alunos(**{'DATA DE NASCIMENTO': '1990-02-01'}))
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_data_de_nascimento_inexistente(submeter, dados_alunos):
    for data in ('31/02/1990', '10/13/1990'):
        corpo = submeter(dados_alunos(**{'DATA DE NASCIMENTO': data}))
        assert 'Data de nascimento inválida' in corpo
        assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_varios_erros_aparecem_juntos(submeter, dados_alunos):
    corpo = submeter(dados_alunos(**{'N. USP': '12A4567', 'CEP': '05508090'}))
    assert 'N. USP deve conter apenas números' in corpo
    assert 'CEP deve estar no formato 00000-000' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_validacao_vale_na_aba_docentes(submeter, dados_docentes):
    corpo = submeter(dados_docentes(**{'CEP': '05508090'}))
    assert 'CEP deve estar no formato 00000-000' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo
