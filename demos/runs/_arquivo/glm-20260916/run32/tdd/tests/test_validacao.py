def test_solicitacao_valida_nao_gera_erros(enviar, campos_alunos):
    assert enviar(campos_alunos)['erros'] == []


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem(enviar, campos_alunos):
    campos = {
        **campos_alunos,
        'NOME COMPLETO - SEM ABREVIAR': '',
        'PROGRAMA': '',
        'LOGRADOURO': '',
    }
    dados = enviar(campos)
    assert dados['erros'].count('Preencha todos os campos') == 1
    assert not dados['oficio']


def test_nivel_e_tipo_de_auxilio_sao_obrigatorios_para_alunos(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'NÍVEL': '', 'TIPO DE AUXÍLIO': ''})
    assert 'Preencha todos os campos' in dados['erros']


def test_n_usp_deve_ter_somente_digitos(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'N. USP': '123a567'})
    assert 'N. USP deve conter apenas números' in dados['erros']


def test_agencia_deve_ter_somente_digitos(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'NÚMERO DA AGÊNCIA': '12a3'})
    assert 'Número da agência deve conter apenas números' in dados['erros']


def test_valor_solicitado_deve_ser_maior_que_zero(enviar, campos_alunos):
    for valor in ('0', '1a'):
        dados = enviar({**campos_alunos, 'VALOR SOLICITADO (R$)': valor})
        assert 'Valor solicitado deve ser maior que 0' in dados['erros']


def test_email_sem_arroba_ou_sem_dominio(enviar, campos_alunos):
    for email in ('maria.silva.usp.br', 'maria@'):
        dados = enviar({**campos_alunos, 'E-MAIL': email})
        assert 'E-mail inválido' in dados['erros']


def test_cpf_fora_do_formato(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)': '11144477735'})
    assert 'CPF deve estar no formato 000.000.000-00' in dados['erros']


def test_cpf_com_digito_verificador_errado(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)': '111.444.777-34'})
    assert 'CPF inválido' in dados['erros']


def test_cep_fora_do_formato(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'CEP': '05508090'})
    assert 'CEP deve estar no formato 00000-000' in dados['erros']


def test_data_de_nascimento_fora_do_formato(enviar, campos_alunos):
    dados = enviar({**campos_alunos, 'DATA DE NASCIMENTO': '01021980'})
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in dados['erros']


def test_data_de_nascimento_inexistente(enviar, campos_alunos):
    for data in ('31/02/1980', '13/13/1980'):
        dados = enviar({**campos_alunos, 'DATA DE NASCIMENTO': data})
        assert 'Data de nascimento inválida' in dados['erros']


def test_todas_as_mensagens_aparecem_juntas(enviar, campos_alunos):
    campos = {
        **campos_alunos,
        'N. USP': '123a567',
        'NÚMERO DA AGÊNCIA': '12a3',
        'VALOR SOLICITADO (R$)': '0',
        'E-MAIL': 'maria.silva.usp.br',
        'CPF (SEPARADOS POR PONTOS E TRAÇO)': '111.444.777-34',
        'CEP': '05508090',
        'DATA DE NASCIMENTO': '31/02/1980',
    }
    erros = enviar(campos)['erros']
    for mensagem in (
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF inválido',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento inválida',
    ):
        assert mensagem in erros
    assert 'Preencha todos os campos' not in erros
    assert not enviar(campos)['oficio']


def test_regras_valem_na_aba_docentes(enviar, campos_docentes):
    dados = enviar({**campos_docentes, 'N. USP': '12x4567'})
    assert 'N. USP deve conter apenas números' in dados['erros']
    assert not dados['oficio']
