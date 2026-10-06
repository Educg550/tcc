import pytest

MENSAGENS = {
    'obrigatorias': 'Preencha todos os campos',
    'n_usp': 'N. USP deve conter apenas números',
    'agencia': 'Número da agência deve conter apenas números',
    'valor': 'Valor solicitado deve ser maior que 0',
    'email': 'E-mail inválido',
    'cpf_formato': 'CPF deve estar no formato 000.000.000-00',
    'cep_formato': 'CEP deve estar no formato 00000-000',
    'data_formato': 'Data de nascimento deve estar no formato dd/mm/aaaa',
    'cpf_dv': 'CPF inválido',
    'data_invalida': 'Data de nascimento inválida',
}


def tem(linhas, mensagem):
    return any(mensagem in linha for linha in linhas)


def test_campo_obrigatorio_vazio_aparece_uma_unica_vez(enviar, payload_alunos, mensagens):
    for campo in payload_alunos:
        if campo != 'aba':
            payload_alunos[campo] = ''
    linhas = mensagens(enviar(payload_alunos))
    assert sum(MENSAGENS['obrigatorias'] in linha for linha in linhas) == 1
    for chave in MENSAGENS:
        if chave != 'obrigatorias':
            assert not tem(linhas, MENSAGENS[chave]), (
                f'não deveria apontar {MENSAGENS[chave]!r} para campo vazio'
            )


def test_n_usp_deve_conter_apenas_numeros(enviar, payload_alunos, mensagens):
    payload_alunos['n_usp'] = '12a4567'
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['n_usp'])


def test_agencia_deve_conter_apenas_numeros(enviar, payload_alunos, mensagens):
    payload_alunos['agencia'] = '12a34'
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['agencia'])


def test_valor_solicitado_zero(enviar, payload_alunos, mensagens):
    payload_alunos['valor_solicitado'] = 'R$ 0,00'
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['valor'])


@pytest.mark.parametrize('email', ['maria.antonieta.usp.br', 'maria.antonieta@'])
def test_email_invalido(enviar, payload_alunos, mensagens, email):
    payload_alunos['email'] = email
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['email'])


def test_cpf_fora_do_formato(enviar, payload_alunos, mensagens):
    payload_alunos['cpf'] = '123456789'
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['cpf_formato'])


def test_cpf_com_digito_verificador_errado(enviar, payload_alunos, mensagens):
    payload_alunos['cpf'] = '123.456.789-00'
    linhas = mensagens(enviar(payload_alunos))
    assert tem(linhas, MENSAGENS['cpf_dv'])
    assert not tem(linhas, MENSAGENS['cpf_formato'])


def test_cep_fora_do_formato(enviar, payload_alunos, mensagens):
    payload_alunos['cep'] = '05508-09'
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['cep_formato'])


def test_data_fora_do_formato(enviar, payload_alunos, mensagens):
    payload_alunos['data_nascimento'] = '01021980'
    linhas = mensagens(enviar(payload_alunos))
    assert tem(linhas, MENSAGENS['data_formato'])
    assert not tem(linhas, MENSAGENS['data_invalida'])


@pytest.mark.parametrize('data', ['31/02/1980', '15/13/1980'])
def test_data_inexistente(enviar, payload_alunos, mensagens, data):
    payload_alunos['data_nascimento'] = data
    assert tem(mensagens(enviar(payload_alunos)), MENSAGENS['data_invalida'])


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(enviar, payload_alunos, mensagens):
    payload_alunos.update(
        {
            'n_usp': '12a4567',
            'email': 'maria.antonieta.usp.br',
            'valor_solicitado': 'R$ 0,00',
            'cpf': '999',
            'cep': '05508-09',
            'data_nascimento': '31/02/1980',
            'agencia': '12a34',
        }
    )
    linhas = mensagens(enviar(payload_alunos))
    for chave in ('n_usp', 'email', 'valor', 'cpf_formato', 'cep_formato', 'data_invalida', 'agencia'):
        assert tem(linhas, MENSAGENS[chave])
    assert not tem(linhas, MENSAGENS['obrigatorias'])


def test_docentes_passam_pela_mesma_validacao(enviar, payload_docentes, mensagens):
    payload_docentes['n_usp'] = '12a4567'
    assert tem(mensagens(enviar(payload_docentes)), MENSAGENS['n_usp'])


def test_com_erro_o_oficio_nao_e_gerado(enviar, payload_alunos, mensagens, oficio):
    payload_alunos['cep'] = '05508-09'
    resposta = enviar(payload_alunos)
    assert oficio(resposta).strip() == ''
    assert not tem(mensagens(resposta), 'Encaminhe-se ao Serviço Financeiro')
