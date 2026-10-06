from conftest import dados_alunos, dados_docentes, dados_vazios, postar, textos

LINHAS_DO_OFICIO = [
    'Interessada(o): Maria da Silva Souza - 8765432',
    'E-mail: maria.souza@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou',
    'Evento: SBBD 2025',
    'Período: 6 a 9 de outubro de 2025',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://sbbd.org.br/2025',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Inscrição no evento e passagem aérea de ida e volta.',
    'Dados do evento',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Sala 214',
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


def test_oficio_da_aba_alunos_com_os_dados_no_lugar(client):
    resposta = postar(client, dados_alunos(), pista='aluno')
    assert resposta.status_code < 300
    corpo = textos(resposta)
    for linha in LINHAS_DO_OFICIO:
        assert linha in corpo, f'não apareceu no ofício: {linha!r}'
    assert 'Preencha todos os campos' not in corpo


def test_oficio_da_aba_docentes_usa_verba_do_programa(client):
    resposta = postar(client, dados_docentes(), pista='docente')
    corpo = textos(resposta)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in corpo
    assert 'Programa: Ciência da Computação' in corpo
    assert 'Programa: Ciência da Computação -' not in corpo
    assert '- Mestrado' not in corpo
    assert 'Interessada(o): Maria da Silva Souza - 8765432' in corpo
    assert 'Valor solicitado: R$ 1.500,00' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo


def test_link_do_evento_vazio_sai_do_oficio(client):
    resposta = postar(client, dados_alunos(link_evento=''), pista='aluno')
    corpo = textos(resposta)
    assert 'Link do evento:' not in corpo
    assert 'Complemento: Sala 214' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo


def test_complemento_vazio_sai_do_oficio(client):
    resposta = postar(client, dados_alunos(complemento=''), pista='aluno')
    corpo = textos(resposta)
    assert 'Complemento:' not in corpo
    assert 'Link do evento: https://sbbd.org.br/2025' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo


def test_todos_os_campos_vazios_pedem_preenchimento_uma_vez(client):
    resposta = postar(client, dados_vazios(), pista='aluno')
    corpo = textos(resposta)
    assert corpo.count('Preencha todos os campos') == 1
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_mensagens_de_erro_de_formato_aparecem_juntas(client):
    resposta = postar(
        client,
        dados_alunos(
            n_usp='87a6543',
            email='maria.souza.usp.br',
            numero_agencia='12b4',
            valor_solicitado='R$ 0,00',
            cpf='123.456.789',
            cep='55080-90',
            data_nascimento='01021980',
        ),
        pista='aluno',
    )
    corpo = textos(resposta)
    for mensagem in (
        'N. USP deve conter apenas números',
        'E-mail inválido',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'CPF deve estar no formato 000.000.000-00',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento deve estar no formato dd/mm/aaaa',
    ):
        assert mensagem in corpo
    assert 'Preencha todos os campos' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_cpf_no_formato_mas_com_verificador_errado(client):
    resposta = postar(client, dados_alunos(cpf='123.456.789-00'), pista='aluno')
    corpo = textos(resposta)
    assert 'CPF inválido' in corpo
    assert 'CPF deve estar no formato 000.000.000-00' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro' not in corpo


def test_data_de_nascimento_inexistente(client):
    for valor in ('31/02/1980', '13/13/1980'):
        resposta = postar(client, dados_alunos(data_nascimento=valor), pista='aluno')
        corpo = textos(resposta)
        assert 'Data de nascimento inválida' in corpo, valor
        assert 'Data de nascimento deve estar no formato dd/mm/aaaa' not in corpo
