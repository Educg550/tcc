OFICIO_ALUNOS = (
    'Interessada(o): Maria de Souza - 1234567\n'
    'E-mail: maria@usp.br\n'
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento\n'
    'Programa: Ciência da Computação - Mestrado\n'
    '\n'
    'A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a\n'
    'interessada(o) acima, conforme segue:\n'
    '\n'
    'Dados do evento\n'
    'Evento: SBBC 2025\n'
    'Período: 10/06/2025 a 13/06/2025\n'
    'Local: Águas de Lindóia - SP - Brasil\n'
    'Link do evento: https://sbbc.org.br/2025\n'
    'Apresentação de trabalho: Pôster\n'
    'Valor solicitado: R$ 1.500,00\n'
    'Detalhamento: Passagem aérea e inscrição\n'
    '\n'
    'Endereço da(o) interessada(o)\n'
    'Rua do Anfiteatro, 181\n'
    'Complemento: Sala 222\n'
    'CEP: 05508-090\n'
    'Cidade Universitária, São Paulo - SP\n'
    '\n'
    'Dados para pagamento\n'
    'Data de nascimento: 01/02/1980\n'
    'CPF: 123.456.789-09\n'
    'RG / RNM: 12.345.678-9\n'
    'Banco: Banco do Brasil\n'
    'Agência: 0001\n'
    'Conta: 12345-6\n'
    '\n'
    'Encaminhe-se ao Serviço Financeiro para providências.'
)

OFICIO_DOCENTES = OFICIO_ALUNOS.replace(
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
).replace(
    'Programa: Ciência da Computação - Mestrado',
    'Programa: Ciência da Computação',
)


def enviar(client, payload):
    resposta = client.post('/solicitacao', =payload)
    assert resposta.status_code == 200, resposta.text
    return resposta.()['oficio'].rstrip('\n')


def test_oficio_da_aba_alunos(client, payload_alunos):
    assert enviar(client, payload_alunos) == OFICIO_ALUNOS


def test_oficio_da_aba_docentes(client, payload_docentes):
    assert enviar(client, payload_docentes) == OFICIO_DOCENTES


def test_oficio_docentes_nao_menciona_nivel(client, payload_docentes):
    oficio = enviar(client, payload_docentes)
    assert 'Verba do programa' in oficio
    assert 'Mestrado' not in oficio


def test_link_vazio_sai_do_oficio(client, payload_alunos):
    payload_alunos['LINK DO EVENTO, EXAME OU DEFESA'] = ''
    oficio = enviar(client, payload_alunos)
    assert oficio == OFICIO_ALUNOS.replace(
        'Link do evento: https://sbbc.org.br/2025\n', ''
    )


def test_complemento_vazio_sai_do_oficio(client, payload_alunos):
    payload_alunos['COMPLEMENTO'] = ''
    oficio = enviar(client, payload_alunos)
    assert oficio == OFICIO_ALUNOS.replace('Complemento: Sala 222\n', '')


def test_campo_obrigatorio_vazio(client, payload_alunos):
    payload_alunos['NOME COMPLETO - SEM ABREVIAR'] = ''
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert resposta.()['erros'] == ['Preencha todos os campos']


def test_mensagem_de_vazio_aparece_uma_unicamente(client, payload_alunos):
    payload_alunos['NOME COMPLETO - SEM ABREVIAR'] = ''
    payload_alunos['PROGRAMA'] = ''
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.()['erros'] == ['Preencha todos os campos']


def test_nivel_e_tipo_sao_obrigatorios_na_aba_alunos(client, payload_alunos):
    payload_alunos['NÍVEL'] = ''
    payload_alunos['TIPO DE AUXÍLIO'] = ''
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert resposta.()['erros'] == ['Preencha todos os campos']


def test_vazio_e_erro_de_formato_convivem(client, payload_alunos):
    payload_alunos['NOME COMPLETO - SEM ABREVIAR'] = ''
    payload_alunos['CEP'] = '0550809'
    resposta = client.post('/solicitacao', =payload_alunos)
    erros = resposta.()['erros']
    assert 'Preencha todos os campos' in erros
    assert 'CEP deve estar no formato 00000-000' in erros


def test_n_usp_deve_ter_so_digitos(client, payload_alunos):
    payload_alunos['N. USP'] = '12a4567'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'N. USP deve conter apenas números' in resposta.()['erros']


def test_agencia_deve_ter_so_digitos(client, payload_alunos):
    payload_alunos['NÚMERO DA AGÊNCIA'] = '0a01'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'Número da agência deve conter apenas números' in resposta.()['erros']


def test_valor_zero_e_rejeitado(client, payload_alunos):
    payload_alunos['VALOR SOLICITADO (R$)'] = 'R$ 0,00'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'Valor solicitado deve ser maior que 0' in resposta.()['erros']


def test_valor_nao_numerico_e_rejeitado(client, payload_alunos):
    payload_alunos['VALOR SOLICITADO (R$)'] = 'abc'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'Valor solicitado deve ser maior que 0' in resposta.()['erros']


def test_email_sem_arroba(client, payload_alunos):
    payload_alunos['E-MAIL'] = 'maria.usp.br'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'E-mail inválido' in resposta.()['erros']


def test_email_sem_dominio(client, payload_alunos):
    payload_alunos['E-MAIL'] = 'maria@'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'E-mail inválido' in resposta.()['erros']


def test_cpf_fora_do_formato(client, payload_alunos):
    payload_alunos['CPF (SEPARADOS POR PONTOS E TRAÇO)'] = '123456789-09'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'CPF deve estar no formato 000.000.000-00' in resposta.()['erros']


def test_cpf_com_digito_verificador_errado(client, payload_alunos):
    payload_alunos['CPF (SEPARADOS POR PONTOS E TRAÇO)'] = '123.456.789-00'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'CPF inválido' in resposta.()['erros']


def test_cep_fora_do_formato(client, payload_alunos):
    payload_alunos['CEP'] = '0550809'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'CEP deve estar no formato 00000-000' in resposta.()['erros']


def test_data_fora_do_formato(client, payload_alunos):
    payload_alunos['DATA DE NASCIMENTO'] = '1980-02-01'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in resposta.()['erros']


def test_data_com_dia_inexistente(client, payload_alunos):
    payload_alunos['DATA DE NASCIMENTO'] = '31/02/1980'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'Data de nascimento inválida' in resposta.()['erros']


def test_data_com_mes_inexistente(client, payload_alunos):
    payload_alunos['DATA DE NASCIMENTO'] = '05/13/1980'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'Data de nascimento inválida' in resposta.()['erros']


def test_todas_as_mensagens_aplicaveis_aparecem(client, payload_alunos):
    payload_alunos['N. USP'] = '12a4567'
    payload_alunos['E-MAIL'] = 'maria.usp.br'
    payload_alunos['CEP'] = '0550809'
    payload_alunos['CPF (SEPARADOS POR PONTOS E TRAÇO)'] = '123.456.789-00'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert sorted(resposta.()['erros']) == sorted(
        [
            'N. USP deve conter apenas números',
            'E-mail inválido',
            'CEP deve estar no formato 00000-000',
            'CPF inválido',
        ]
    )


def test_com_erro_nao_ha_oficio(client, payload_alunos):
    payload_alunos['N. USP'] = '12a4567'
    resposta = client.post('/solicitacao', =payload_alunos)
    assert resposta.status_code == 400
    assert 'oficio' not in resposta.()
