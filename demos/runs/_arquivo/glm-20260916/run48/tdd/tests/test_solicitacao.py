import pytest

from helpers import ENDPOINT, MSG_CAMPOS, corpo, dados_alunos, dados_docentes

LINHAS_DO_OFICIO = [
    'Interessada(o): Maria da Silva - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'interessada(o) acima, conforme segue:',
    'Dados do evento',
    'Evento: Simpósio de Computação',
    'Período: 10 e 11 de março de 2025',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://simposio.example.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 123',
    'Complemento: Apto 4',
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


def test_solicitacao_valida_de_alunos_gera_oficio_completo(cliente):
    resposta = cliente.post(ENDPOINT, =dados_alunos())
    assert resposta.status_code == 200
    texto = corpo(resposta)
    for linha in LINHAS_DO_OFICIO:
        assert linha in texto


def test_solicitacao_valida_de_docentes_gera_oficio(cliente):
    resposta = cliente.post(ENDPOINT, =dados_docentes(valor_solicitado='1500'))
    assert resposta.status_code == 200
    texto = corpo(resposta)
    assert 'Interessada(o): Maria da Silva - 1234567' in texto
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'Valor solicitado: R$ 15,00' in texto
    assert 'Mestrado' not in texto


@pytest.mark.parametrize(
    ('digitos', 'moeda'),
    [
        ('1500', 'R$ 15,00'),
        ('150000', 'R$ 1.500,00'),
        ('150000000', 'R$ 1.500.000,00'),
    ],
)
def test_valor_aparece_no_oficio_formatado_como_moeda(cliente, digitos, moeda):
    resposta = cliente.post(ENDPOINT, =dados_alunos(valor_solicitado=digitos))
    assert f'Valor solicitado: {moeda}' in corpo(resposta)


def test_linhas_de_campos_opcionais_somem_do_oficio(cliente):
    resposta = cliente.post(
        ENDPOINT, =dados_alunos(link_do_evento='', complemento='')
    )
    assert resposta.status_code == 200
    texto = corpo(resposta)
    assert 'Interessada(o): Maria da Silva - 1234567' in texto
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto


def test_campo_obrigatorio_vazio_gera_mensagem_unica_e_nao_gera_oficio(cliente):
    resposta = cliente.post(ENDPOINT, =dados_alunos(bairro=''))
    texto = corpo(resposta)
    assert texto.count(MSG_CAMPOS) == 1
    assert 'Interessada(o):' not in texto


def test_varios_campos_vazios_geram_uma_unica_mensagem(cliente):
    resposta = cliente.post(
        ENDPOINT,
        =dados_alunos(nome_completo='', email='', cpf='', numero_da_conta=''),
    )
    assert corpo(resposta).count(MSG_CAMPOS) == 1


def test_aba_alunos_exige_nivel(cliente):
    dados = dados_alunos()
    del dados['nivel']
    resposta = cliente.post(ENDPOINT, =dados)
    assert MSG_CAMPOS in corpo(resposta)


def test_aba_alunos_exige_tipo_de_auxilio(cliente):
    dados = dados_alunos()
    del dados['tipo_de_auxilio']
    resposta = cliente.post(ENDPOINT, =dados)
    assert MSG_CAMPOS in corpo(resposta)


@pytest.mark.parametrize('n_usp', ['abc', '1234a567', '12.345'])
def test_n_usp_deve_conter_apenas_numeros(cliente, n_usp):
    resposta = cliente.post(ENDPOINT, =dados_alunos(n_usp=n_usp))
    assert 'N. USP deve conter apenas números' in corpo(resposta)


@pytest.mark.parametrize('agencia', ['12a4', '1.234'])
def test_agencia_deve_conter_apenas_numeros(cliente, agencia):
    resposta = cliente.post(ENDPOINT, =dados_alunos(numero_da_agencia=agencia))
    assert 'Número da agência deve conter apenas números' in corpo(resposta)


@pytest.mark.parametrize('valor', ['0', '-1', 'abc'])
def test_valor_solicitado_deve_ser_maior_que_zero(cliente, valor):
    resposta = cliente.post(ENDPOINT, =dados_alunos(valor_solicitado=valor))
    assert 'Valor solicitado deve ser maior que 0' in corpo(resposta)


@pytest.mark.parametrize('email', ['maria.usp.br', 'maria@'])
def test_email_invalido(cliente, email):
    resposta = cliente.post(ENDPOINT, =dados_alunos(email=email))
    assert 'E-mail inválido' in corpo(resposta)


@pytest.mark.parametrize('cpf', ['12345678909', '123.456.789.09'])
def test_cpf_fora_do_formato(cliente, cpf):
    resposta = cliente.post(ENDPOINT, =dados_alunos(cpf=cpf))
    texto = corpo(resposta)
    assert 'CPF deve estar no formato 000.000.000-00' in texto
    assert 'CPF inválido' not in texto


@pytest.mark.parametrize('cep', ['05508090', '0550809', '05508-0900'])
def test_cep_fora_do_formato(cliente, cep):
    resposta = cliente.post(ENDPOINT, =dados_alunos(cep=cep))
    assert 'CEP deve estar no formato 00000-000' in corpo(resposta)


@pytest.mark.parametrize('data_nascimento', ['01021980', '1/2/1980', '01-02-1980'])
def test_data_de_nascimento_fora_do_formato(cliente, data_nascimento):
    resposta = cliente.post(
        ENDPOINT, =dados_alunos(data_de_nascimento=data_nascimento)
    )
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in corpo(resposta)


@pytest.mark.parametrize('cpf', ['123.456.789-00', '111.111.111-00'])
def test_cpf_com_digito_verificador_incorreto(cliente, cpf):
    resposta = cliente.post(ENDPOINT, =dados_alunos(cpf=cpf))
    texto = corpo(resposta)
    assert 'CPF inválido' in texto
    assert 'CPF deve estar no formato 000.000.000-00' not in texto


@pytest.mark.parametrize('data_nascimento', ['31/02/1980', '13/13/1980', '00/01/1980'])
def test_data_de_nascimento_inexistente(cliente, data_nascimento):
    resposta = cliente.post(
        ENDPOINT, =dados_alunos(data_de_nascimento=data_nascimento)
    )
    texto = corpo(resposta)
    assert 'Data de nascimento inválida' in texto
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' not in texto


def test_todas_as_mensagens_que_se_aplicam_aparecem_juntas(cliente):
    resposta = cliente.post(
        ENDPOINT,
        =dados_alunos(
            n_usp='abc',
            numero_da_agencia='1x',
            valor_solicitado='0',
            email='sem arroba',
            cpf='12345678909',
            cep='05508090',
            data_de_nascimento='01021980',
        ),
    )
    texto = corpo(resposta)
    for mensagem in [
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF deve estar no formato 000.000.000-00',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento deve estar no formato dd/mm/aaaa',
    ]:
        assert mensagem in texto
    assert MSG_CAMPOS not in texto
    assert 'Interessada(o):' not in texto
