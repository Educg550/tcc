import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app import app

CLIENTE = TestClient(app)

ALUNOS = {
    'aba': 'alunos',
    'nome_completo': 'Maria da Silva',
    'n_usp': '12345678',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria@ime.usp.br',
    'nome_evento': 'Simpósio Brasileiro de Computação',
    'periodo': '10 a 15 de outubro de 2024',
    'cidade_evento': 'São Paulo',
    'estado_evento': 'SP',
    'pais_evento': 'Brasil',
    'link_evento': 'https://evento.usp.br',
    'valor': 'R$ 1.500,00',
    'detalhamento': 'Passagem aérea e hospedagem',
    'apresentacao': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Matão',
    'numero': '1010',
    'complemento': 'Bloco B',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '12345-6',
}

DOCENTES = {chave: valor for chave, valor in ALUNOS.items() if chave not in ('nivel', 'tipo_auxilio')}
DOCENTES['aba'] = 'docentes'
DOCENTES['programa'] = 'Física'


def enviar(dados):
    resposta = CLIENTE.post('/api/solicitacao', json=dados)
    assert resposta.status_code in (200, 400, 422), resposta.text
    return resposta.json()


def erros_de(dados):
    return enviar(dados)['erros']


def test_solicitacao_de_aluno_gera_oficio_com_os_dados():
    corpo = enviar(dict(ALUNOS))
    assert corpo['erros'] == []
    oficio = corpo['oficio']
    assert '<<' not in oficio
    for linha in [
        'Interessada(o): Maria da Silva - 12345678',
        'E-mail: maria@ime.usp.br',
        'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
        'Programa: Ciência da Computação - Mestrado',
        'Dados do evento',
        'Evento: Simpósio Brasileiro de Computação',
        'Período: 10 a 15 de outubro de 2024',
        'Local: São Paulo - SP - Brasil',
        'Link do evento: https://evento.usp.br',
        'Apresentação de trabalho: Pôster',
        'Valor solicitado: R$ 1.500,00',
        'Detalhamento: Passagem aérea e hospedagem',
        'Endereço da(o) interessada(o)',
        'Rua do Matão, 1010',
        'Complemento: Bloco B',
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
    ]:
        assert linha in oficio, linha
    texto = ' '.join(oficio.split())
    assert 'A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:' in texto
    assert oficio.index('Dados do evento') < oficio.index('Endereço da(o) interessada(o)')
    assert oficio.index('Endereço da(o) interessada(o)') < oficio.index('Dados para pagamento')


def test_solicitacao_de_docente_nao_tem_nivel_nem_tipo_de_auxilio():
    corpo = enviar(dict(DOCENTES))
    assert corpo['erros'] == []
    oficio = corpo['oficio']
    assert 'Interessada(o): Maria da Silva - 12345678' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Física' in oficio
    assert 'Programa: Física -' not in oficio


def test_link_e_complemento_vazios_saem_do_oficio():
    corpo = enviar(dict(ALUNOS, link_evento='', complemento=''))
    assert corpo['erros'] == []
    oficio = corpo['oficio']
    assert 'Link do evento' not in oficio
    assert 'Complemento' not in oficio
    assert 'Apresentação de trabalho: Pôster' in oficio
    assert 'Butantã, São Paulo - SP' in oficio


def test_campo_obrigatorio_vazio_gera_uma_unica_mensagem():
    corpo = enviar(dict(ALUNOS, nome_completo='', numero=''))
    assert corpo['erros'] == ['Preencha todos os campos']
    assert not corpo.get('oficio')


def test_n_usp_so_aceita_numeros():
    assert erros_de(dict(ALUNOS, n_usp='12a456')) == ['N. USP deve conter apenas números']


def test_agencia_so_aceita_numeros():
    assert erros_de(dict(ALUNOS, agencia='12-34')) == ['Número da agência deve conter apenas números']


def test_valor_precisa_ser_maior_que_zero():
    assert erros_de(dict(ALUNOS, valor='R$ 0,00')) == ['Valor solicitado deve ser maior que 0']


def test_email_invalido():
    assert erros_de(dict(ALUNOS, email='maria.ime.usp.br')) == ['E-mail inválido']
    assert erros_de(dict(ALUNOS, email='maria@')) == ['E-mail inválido']


def test_cpf_fora_do_formato():
    assert erros_de(dict(ALUNOS, cpf='12345678909')) == ['CPF deve estar no formato 000.000.000-00']


def test_cep_fora_do_formato():
    assert erros_de(dict(ALUNOS, cep='05508090')) == ['CEP deve estar no formato 00000-000']


def test_data_de_nascimento_fora_do_formato():
    assert erros_de(dict(ALUNOS, data_nascimento='01-02-1980')) == ['Data de nascimento deve estar no formato dd/mm/aaaa']


def test_cpf_com_digitos_verificadores_errados():
    assert erros_de(dict(ALUNOS, cpf='123.456.789-00')) == ['CPF inválido']


def test_data_de_nascimento_inexistente():
    assert erros_de(dict(ALUNOS, data_nascimento='31/02/1980')) == ['Data de nascimento inválida']
    assert erros_de(dict(ALUNOS, data_nascimento='13/13/1980')) == ['Data de nascimento inválida']


def test_todas_as_mensagens_aplicaveis():
    dados = dict(ALUNOS, n_usp='12a456', email='maria', valor='R$ 0,00', cep='05508090')
    assert sorted(erros_de(dados)) == sorted([
        'N. USP deve conter apenas números',
        'E-mail inválido',
        'Valor solicitado deve ser maior que 0',
        'CEP deve estar no formato 00000-000',
    ])


def test_nivel_e_tipo_de_auxilio_sao_obrigatorios_para_alunos():
    dados = {chave: valor for chave, valor in ALUNOS.items() if chave not in ('nivel', 'tipo_auxilio')}
    assert erros_de(dados) == ['Preencha todos os campos']
