OFICIO_ALUNOS = '''Interessada(o): Maria Silva Almeida - 1234567
E-mail: maria@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Mestrado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD 2025
Período: 10 a 14 de novembro de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://sbbd.org.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagens aéreas e inscrição no evento.

Endereço da(o) interessada(o)
Rua do Anfiteatro, 101
Complemento: Sala 215
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 98765-4

Encaminhe-se ao Serviço Financeiro para providências.'''

OFICIO_ALUNOS_SEM_OPCIONAIS = '''Interessada(o): Maria Silva Almeida - 1234567
E-mail: maria@usp.br
Assunto: Solicitação de Auxílio Financeiro - Participação em evento
Programa: Ciência da Computação - Mestrado

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD 2025
Período: 10 a 14 de novembro de 2025
Local: São Paulo - SP - Brasil
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagens aéreas e inscrição no evento.

Endereço da(o) interessada(o)
Rua do Anfiteatro, 101
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 98765-4

Encaminhe-se ao Serviço Financeiro para providências.'''

OFICIO_DOCENTES = '''Interessada(o): Maria Silva Almeida - 1234567
E-mail: maria@usp.br
Assunto: Solicitação de Auxílio Financeiro - Verba do programa
Programa: Ciência da Computação

A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: SBBD 2025
Período: 10 a 14 de novembro de 2025
Local: São Paulo - SP - Brasil
Link do evento: https://sbbd.org.br
Apresentação de trabalho: Pôster
Valor solicitado: R$ 1.500,00
Detalhamento: Passagens aéreas e inscrição no evento.

Endereço da(o) interessada(o)
Rua do Anfiteatro, 101
Complemento: Sala 215
CEP: 05508-090
Cidade Universitária, São Paulo - SP

Dados para pagamento
Data de nascimento: 01/02/1980
CPF: 123.456.789-09
RG / RNM: 12.345.678-9
Banco: Banco do Brasil
Agência: 1234
Conta: 98765-4

Encaminhe-se ao Serviço Financeiro para providências.'''


def carga(aba):
    dados = {
        'ABA': aba,
        'NOME COMPLETO - SEM ABREVIAR': 'Maria Silva Almeida',
        'N. USP': '1234567',
        'PROGRAMA': 'Ciência da Computação',
        'E-MAIL': 'maria@usp.br',
        'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBBD 2025',
        'PERÍODO DO EVENTO, EXAME OU DEFESA': '10 a 14 de novembro de 2025',
        'CIDADE DO EVENTO, EXAME OU DEFESA': 'São Paulo',
        'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
        'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
        'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbbd.org.br',
        'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
        'DETALHAMENTO DO PEDIDO': 'Passagens aéreas e inscrição no evento.',
        'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
        'DATA DE NASCIMENTO': '01/02/1980',
        'LOGRADOURO': 'Rua do Anfiteatro',
        'NÚMERO': '101',
        'COMPLEMENTO': 'Sala 215',
        'BAIRRO': 'Cidade Universitária',
        'CEP': '05508-090',
        'CIDADE': 'São Paulo',
        'ESTADO': 'SP',
        'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
        'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
        'NOME DO BANCO': 'Banco do Brasil',
        'NÚMERO DA AGÊNCIA': '1234',
        'NÚMERO DA CONTA': '98765-4',
    }
    if aba == 'ALUNOS':
        dados['NÍVEL'] = 'Mestrado'
        dados['TIPO DE AUXÍLIO'] = 'Participação em evento'
    return dados


def corpo(resposta):
    try:
        return resposta.()
    except ValueError:
        return resposta.text


def textos(conteudo):
    if isinstance(conteudo, str):
        return [conteudo]
    if isinstance(conteudo, dict):
        achados = []
        for valor in conteudo.values():
            achados.extend(textos(valor))
        return achados
    if isinstance(conteudo, (list, tuple)):
        achados = []
        for valor in conteudo:
            achados.extend(textos(valor))
        return achados
    return []


def tem_mensagem(resposta, mensagem):
    return any(mensagem in texto for texto in textos(corpo(resposta)))


def tem_oficio(resposta, esperado):
    partes = [texto.replace('\r\n', '\n').strip() for texto in textos(corpo(resposta))]
    return any(parte == esperado for parte in partes) or '\n'.join(partes).strip() == esperado


def oficio_gerado(resposta):
    return any('Encaminhe-se ao Serviço Financeiro' in texto for texto in textos(corpo(resposta)))


def test_solicitacao_valida_de_alunos_gera_oficio(cliente):
    resposta = cliente.post('/api/solicitacao', =carga('ALUNOS'))
    assert resposta.status_code == 200
    assert tem_oficio(resposta, OFICIO_ALUNOS)


def test_oficio_de_alunos_omite_as_linhas_opcionais_vazias(cliente):
    dados = carga('ALUNOS')
    dados['LINK DO EVENTO, EXAME OU DEFESA'] = ''
    dados['COMPLEMENTO'] = ''
    resposta = cliente.post('/api/solicitacao', =dados)
    assert resposta.status_code == 200
    assert tem_oficio(resposta, OFICIO_ALUNOS_SEM_OPCIONAIS)


def test_solicitacao_valida_de_docentes_gera_oficio(cliente):
    resposta = cliente.post('/api/solicitacao', =carga('DOCENTES'))
    assert resposta.status_code == 200
    assert tem_oficio(resposta, OFICIO_DOCENTES)


def test_confirmacao_mostra_solicitacao_registrada(cliente):
    resposta = cliente.post('/api/solicitacao', =carga('ALUNOS'))
    fontes = textos(corpo(resposta))
    fontes.append(cliente.get('/').text)
    fontes.append(cliente.get('/app.js').text)
    assert any('Solicitação registrada' in fonte for fonte in fontes)


def test_campos_obrigatorios_vazios_geram_uma_unica_mensagem(cliente):
    dados = carga('ALUNOS')
    for chave in dados:
        if chave != 'ABA':
            dados[chave] = ''
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'Preencha todos os campos')
    juntado = '\n'.join(textos(corpo(resposta)))
    assert juntado.count('Preencha todos os campos') == 1
    assert not oficio_gerado(resposta)


def test_n_usp_deve_conter_apenas_numeros(cliente):
    dados = carga('ALUNOS')
    dados['N. USP'] = '12a45'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'N. USP deve conter apenas números')
    assert not tem_mensagem(resposta, 'Preencha todos os campos')
    assert not oficio_gerado(resposta)


def test_numero_da_agencia_deve_conter_apenas_numeros(cliente):
    dados = carga('ALUNOS')
    dados['NÚMERO DA AGÊNCIA'] = '12b4'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'Número da agência deve conter apenas números')
    assert not tem_mensagem(resposta, 'Preencha todos os campos')
    assert not oficio_gerado(resposta)


def test_valor_solicitado_deve_ser_maior_que_zero(cliente):
    dados = carga('ALUNOS')
    dados['VALOR SOLICITADO (R$)'] = 'R$ 0,00'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'Valor solicitado deve ser maior que 0')
    assert not tem_mensagem(resposta, 'Preencha todos os campos')
    assert not oficio_gerado(resposta)


def test_email_sem_arroba_ou_sem_dominio(cliente):
    for email in ('maria.usp.br', 'maria@'):
        dados = carga('ALUNOS')
        dados['E-MAIL'] = email
        resposta = cliente.post('/api/solicitacao', =dados)
        assert tem_mensagem(resposta, 'E-mail inválido'), email
        assert not tem_mensagem(resposta, 'Preencha todos os campos')
        assert not oficio_gerado(resposta)


def test_cpf_fora_do_formato(cliente):
    for cpf in ('12345678909', '123.456.789-0'):
        dados = carga('ALUNOS')
        dados['CPF (SEPARADOS POR PONTOS E TRAÇO)'] = cpf
        resposta = cliente.post('/api/solicitacao', =dados)
        assert tem_mensagem(resposta, 'CPF deve estar no formato 000.000.000-00'), cpf
        assert not tem_mensagem(resposta, 'Preencha todos os campos')
        assert not oficio_gerado(resposta)


def test_cep_fora_do_formato(cliente):
    dados = carga('ALUNOS')
    dados['CEP'] = '05508090'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'CEP deve estar no formato 00000-000')
    assert not tem_mensagem(resposta, 'Preencha todos os campos')
    assert not oficio_gerado(resposta)


def test_data_de_nascimento_fora_do_formato(cliente):
    dados = carga('ALUNOS')
    dados['DATA DE NASCIMENTO'] = '01021980'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'Data de nascimento deve estar no formato dd/mm/aaaa')
    assert not tem_mensagem(resposta, 'Preencha todos os campos')
    assert not oficio_gerado(resposta)


def test_cpf_com_digitos_verificadores_errados(cliente):
    dados = carga('ALUNOS')
    dados['CPF (SEPARADOS POR PONTOS E TRAÇO)'] = '123.456.789-10'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'CPF inválido')
    assert not tem_mensagem(resposta, 'CPF deve estar no formato 000.000.000-00')
    assert not oficio_gerado(resposta)


def test_data_de_nascimento_inexistente(cliente):
    for data in ('31/02/1980', '15/13/1980'):
        dados = carga('ALUNOS')
        dados['DATA DE NASCIMENTO'] = data
        resposta = cliente.post('/api/solicitacao', =dados)
        assert tem_mensagem(resposta, 'Data de nascimento inválida'), data
        assert not tem_mensagem(resposta, 'Data de nascimento deve estar no formato dd/mm/aaaa')
        assert not oficio_gerado(resposta)


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(cliente):
    dados = carga('ALUNOS')
    dados['N. USP'] = '12a45'
    dados['NÚMERO DA AGÊNCIA'] = '12b4'
    dados['VALOR SOLICITADO (R$)'] = 'R$ 0,00'
    dados['E-MAIL'] = 'maria.usp.br'
    dados['CPF (SEPARADOS POR PONTOS E TRAÇO)'] = '123.456.789-10'
    dados['CEP'] = '05508090'
    dados['DATA DE NASCIMENTO'] = '31/02/1980'
    resposta = cliente.post('/api/solicitacao', =dados)
    for mensagem in (
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF inválido',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento inválida',
    ):
        assert tem_mensagem(resposta, mensagem), mensagem
    assert not tem_mensagem(resposta, 'Preencha todos os campos')
    assert not oficio_gerado(resposta)


def test_validacao_vale_igual_na_aba_docentes(cliente):
    dados = carga('DOCENTES')
    dados['N. USP'] = 'abc'
    resposta = cliente.post('/api/solicitacao', =dados)
    assert tem_mensagem(resposta, 'N. USP deve conter apenas números')
    assert not oficio_gerado(resposta)
