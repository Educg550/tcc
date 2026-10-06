# Contrato: POST /api/solicitacao recebe JSON com 'aba' ('ALUNOS' ou 'DOCENTES')
# e um campo por rótulo do formulário, com o valor exatamente como exibido no
# campo (CPF, CEP, data de nascimento e valor já formatados). A resposta é
# {'errors': [...]} quando há erro e {'oficio': '...'} quando a solicitação é válida.

import pytest

DADOS_ALUNOS = {
    'NOME COMPLETO - SEM ABREVIAR': 'Maria Souza',
    'N. USP': '1234567',
    'PROGRAMA': 'Ciência da Computação',
    'NÍVEL': 'Mestrado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'maria@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'Congresso Brasileiro de Computação',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': '10/03/2025 a 15/03/2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'São Paulo',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://congresso.example.br',
    'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Passagens aéreas e hospedagem',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NÚMERO': '101',
    'COMPLEMENTO': 'Sala 5',
    'BAIRRO': 'Butantã',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '1234',
    'NÚMERO DA CONTA': '98765-4',
}

DADOS_DOCENTES = {
    chave: valor
    for chave, valor in DADOS_ALUNOS.items()
    if chave not in ('NÍVEL', 'TIPO DE AUXÍLIO')
}
DADOS_DOCENTES.update(
    {
        'NOME COMPLETO - SEM ABREVIAR': 'Carlos Andrade',
        'N. USP': '7654321',
        'PROGRAMA': 'Estatística',
        'E-MAIL': 'carlos@ime.usp.br',
        'VALOR SOLICITADO (R$)': 'R$ 250,00',
        'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Não irá apresentar trabalho',
    }
)

LINHAS_DO_OFICIO = [
    'Interessada(o): Maria Souza - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou',
    'Dados do evento',
    'Evento: Congresso Brasileiro de Computação',
    'Período: 10/03/2025 a 15/03/2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://congresso.example.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagens aéreas e hospedagem',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 101',
    'Complemento: Sala 5',
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


def enviar(client, dados, aba='ALUNOS'):
    return client.post('/api/solicitacao', ={'aba': aba, **dados})


def test_solicitacao_valida_de_aluno_gera_oficio(client):
    resposta = enviar(client, DADOS_ALUNOS)
    assert resposta.status_code == 200
    oficio = resposta.()['oficio']
    assert '\n' in oficio
    for linha in LINHAS_DO_OFICIO:
        assert linha in oficio, linha


def test_solicitacao_valida_de_docente_gera_oficio_sem_nivel_e_sem_tipo(client):
    resposta = enviar(client, DADOS_DOCENTES, aba='DOCENTES')
    assert resposta.status_code == 200
    oficio = resposta.()['oficio']
    assert 'Interessada(o): Carlos Andrade - 7654321' in oficio
    assert 'E-mail: carlos@ime.usp.br' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Estatística' in oficio
    assert 'Valor solicitado: R$ 250,00' in oficio
    assert 'Apresentação de trabalho: Não irá apresentar trabalho' in oficio
    assert '- Mestrado' not in oficio
    assert '- Doutorado' not in oficio


def test_link_vazio_tira_a_linha_do_oficio(client):
    dados = dict(DADOS_ALUNOS)
    dados['LINK DO EVENTO, EXAME OU DEFESA'] = ''
    oficio = enviar(client, dados).()['oficio']
    assert 'Link do evento' not in oficio


def test_complemento_vazio_tira_a_linha_do_oficio(client):
    dados = dict(DADOS_ALUNOS)
    dados['COMPLEMENTO'] = ''
    oficio = enviar(client, dados).()['oficio']
    assert 'Complemento' not in oficio


def test_campo_obrigatorio_vazio(client):
    dados = dict(DADOS_ALUNOS)
    dados['PROGRAMA'] = ''
    erros = enviar(client, dados).()['errors']
    assert isinstance(erros, list)
    assert 'Preencha todos os campos' in erros


def test_campo_obrigatorio_ausente(client):
    dados = dict(DADOS_ALUNOS)
    del dados['NÍVEL']
    erros = enviar(client, dados).()['errors']
    assert 'Preencha todos os campos' in erros


def test_mensagem_de_vazio_aparece_uma_unicamente(client):
    dados = dict(DADOS_ALUNOS)
    dados['PROGRAMA'] = ''
    dados['BAIRRO'] = ''
    dados['NOME DO BANCO'] = ''
    erros = enviar(client, dados).()['errors']
    assert erros.count('Preencha todos os campos') == 1


def test_com_erro_o_oficio_nao_e_gerado(client):
    dados = dict(DADOS_ALUNOS)
    dados['PROGRAMA'] = ''
    corpo = enviar(client, dados).()
    assert not corpo.get('oficio')


@pytest.mark.parametrize(
    ('campo', 'valor', 'mensagem'),
    [
        ('N. USP', '12a4567', 'N. USP deve conter apenas números'),
        ('NÚMERO DA AGÊNCIA', '12a4', 'Número da agência deve conter apenas números'),
        ('VALOR SOLICITADO (R$)', 'R$ 0,00', 'Valor solicitado deve ser maior que 0'),
        ('E-MAIL', 'maria.usp.br', 'E-mail inválido'),
        ('E-MAIL', 'maria@', 'E-mail inválido'),
        ('CPF (SEPARADOS POR PONTOS E TRAÇO)', '12345678909', 'CPF deve estar no formato 000.000.000-00'),
        ('CEP', '05508090', 'CEP deve estar no formato 00000-000'),
        ('DATA DE NASCIMENTO', '01021980', 'Data de nascimento deve estar no formato dd/mm/aaaa'),
        ('CPF (SEPARADOS POR PONTOS E TRAÇO)', '123.456.789-00', 'CPF inválido'),
        ('DATA DE NASCIMENTO', '31/02/1980', 'Data de nascimento inválida'),
        ('DATA DE NASCIMENTO', '05/13/1980', 'Data de nascimento inválida'),
    ],
)
def test_mensagem_de_validacao_por_campo(client, campo, valor, mensagem):
    dados = dict(DADOS_ALUNOS)
    dados[campo] = valor
    erros = enviar(client, dados).()['errors']
    assert mensagem in erros


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(client):
    dados = dict(DADOS_ALUNOS)
    dados['N. USP'] = 'abc'
    dados['E-MAIL'] = 'maria.usp.br'
    dados['CEP'] = '05508090'
    erros = enviar(client, dados).()['errors']
    assert 'N. USP deve conter apenas números' in erros
    assert 'E-mail inválido' in erros
    assert 'CEP deve estar no formato 00000-000' in erros
    assert 'Preencha todos os campos' not in erros
