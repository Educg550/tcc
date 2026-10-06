MSG_VAZIO = 'Preencha todos os campos'
MSG_N_USP = 'N. USP deve conter apenas números'
MSG_AGENCIA = 'Número da agência deve conter apenas números'
MSG_VALOR = 'Valor solicitado deve ser maior que 0'
MSG_EMAIL = 'E-mail inválido'
MSG_CPF_FORMATO = 'CPF deve estar no formato 000.000.000-00'
MSG_CEP_FORMATO = 'CEP deve estar no formato 00000-000'
MSG_DATA_FORMATO = 'Data de nascimento deve estar no formato dd/mm/aaaa'
MSG_CPF_DIGITO = 'CPF inválido'
MSG_DATA_INVALIDA = 'Data de nascimento inválida'


def test_campos_obrigatorios_vazios_geram_uma_unica_mensagem(enviar, textos):
    resposta = enviar('alunos', nome='', n_usp='', programa='', email='')
    total = sum(texto.count(MSG_VAZIO) for texto in textos(resposta))
    assert total == 1


def test_n_usp_deve_conter_apenas_numeros(enviar, contem):
    assert contem(enviar('alunos', n_usp='12a45'), MSG_N_USP)


def test_numero_da_agencia_deve_conter_apenas_numeros(enviar, contem):
    assert contem(enviar('alunos', agencia='12a4'), MSG_AGENCIA)


def test_valor_solicitado_deve_ser_maior_que_zero(enviar, contem):
    assert contem(enviar('alunos', valor='R$ 0,00'), MSG_VALOR)


def test_email_sem_arroba_e_invalido(enviar, contem):
    assert contem(enviar('alunos', email='maria.oliveira.usp.br'), MSG_EMAIL)


def test_email_sem_dominio_e_invalido(enviar, contem):
    assert contem(enviar('alunos', email='maria@'), MSG_EMAIL)


def test_cpf_fora_do_formato(enviar, contem):
    assert contem(enviar('alunos', cpf='12345678909'), MSG_CPF_FORMATO)


def test_cep_fora_do_formato(enviar, contem):
    assert contem(enviar('alunos', cep='0550809'), MSG_CEP_FORMATO)


def test_data_de_nascimento_fora_do_formato(enviar, contem):
    assert contem(enviar('alunos', data_nascimento='01021980'), MSG_DATA_FORMATO)


def test_cpf_com_digito_verificador_errado(enviar, contem):
    assert contem(enviar('alunos', cpf='123.456.789-00'), MSG_CPF_DIGITO)


def test_data_que_nao_existe_e_invalida(enviar, contem):
    assert contem(enviar('alunos', data_nascimento='31/02/1980'), MSG_DATA_INVALIDA)


def test_data_com_mes_fora_do_intervalo_e_invalida(enviar, contem):
    assert contem(enviar('alunos', data_nascimento='15/13/1980'), MSG_DATA_INVALIDA)


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(enviar, contem):
    resposta = enviar(
        'alunos',
        n_usp='12a45',
        agencia='12a4',
        valor='R$ 0,00',
        email='maria@',
        cpf='123.456.789-00',
        cep='0550809',
        data_nascimento='31/02/1980',
    )
    for mensagem in (
        MSG_N_USP,
        MSG_AGENCIA,
        MSG_VALOR,
        MSG_EMAIL,
        MSG_CPF_DIGITO,
        MSG_CEP_FORMATO,
        MSG_DATA_INVALIDA,
    ):
        assert contem(resposta, mensagem), mensagem


def test_com_erro_o_oficio_nao_e_gerado(enviar, contem):
    resposta = enviar('alunos', email='maria@')
    assert not contem(resposta, 'Encaminhe-se ao Serviço Financeiro')
