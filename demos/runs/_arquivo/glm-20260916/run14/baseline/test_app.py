from fastapi.testclient import TestClient

from app import app

cliente = TestClient(app)

CAMPOS = {
    'nome_completo': 'Maria Aparecida de Souza',
    'n_usp': '1234567',
    'programa': 'Matemática',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria.souza@usp.br',
    'nome_evento': 'Congresso Brasileiro de Matemática',
    'periodo_evento': '10 a 14 de agosto de 2025',
    'cidade_evento': 'Rio de Janeiro',
    'estado_evento': 'RJ',
    'pais_evento': 'Brasil',
    'link_evento': '',
    'valor_solicitado': '150000',
    'detalhamento': 'Passagem aérea e inscrição no evento',
    'apresentacao': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Matão',
    'numero': '1010',
    'complemento': '',
    'bairro': 'Cidade Universitária',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg_rnm': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '12345-6',
}


def enviar(**alteracoes):
    corpo = dict(CAMPOS)
    corpo.update(alteracoes)
    return cliente.post('/api/solicitacao', =corpo).()


def enviar_docentes(**alteracoes):
    corpo = {c: v for c, v in CAMPOS.items() if c not in ('nivel', 'tipo_auxilio')}
    corpo.update(alteracoes)
    corpo['perfil'] = 'docentes'
    return cliente.post('/api/solicitacao', =corpo).()


def test_pagina_inicial_e_servida():
    pagina = cliente.get('/')
    assert pagina.status_code == 200
    assert 'ALUNOS' in pagina.text


def test_solicitacao_valida_gera_oficio():
    resposta = enviar()
    assert resposta['ok'] is True
    oficio = resposta['oficio']
    assert 'Interessada(o): Maria Aparecida de Souza - 1234567' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in oficio
    assert 'Programa: Matemática - Mestrado' in oficio
    assert 'Valor solicitado: R$ 1.500,00' in oficio
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in oficio


def test_oficio_docentes():
    resposta = enviar_docentes()
    assert resposta['ok'] is True
    oficio = resposta['oficio']
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Matemática\n' in oficio


def test_campo_obrigatorio_vazio():
    resposta = enviar(programa='')
    assert resposta == {'ok': False, 'erros': ['Preencha todos os campos']}


def test_n_usp_nao_numerico():
    resposta = enviar(n_usp='123a567')
    assert 'N. USP deve conter apenas números' in resposta['erros']


def test_valor_zero():
    resposta = enviar(valor_solicitado='0')
    assert 'Valor solicitado deve ser maior que 0' in resposta['erros']


def test_email_sem_dominio():
    resposta = enviar(email='maria@')
    assert 'E-mail inválido' in resposta['erros']


def test_cpf_fora_do_formato_e_invalido():
    assert 'CPF deve estar no formato 000.000.000-00' in enviar(cpf='12345678909')['erros']
    assert 'CPF inválido' in enviar(cpf='123.456.789-00')['erros']


def test_cep_fora_do_formato():
    resposta = enviar(cep='5508-090')
    assert 'CEP deve estar no formato 00000-000' in resposta['erros']


def test_data_de_nascimento():
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in enviar(data_nascimento='01021980')['erros']
    assert 'Data de nascimento inválida' in enviar(data_nascimento='30/02/1980')['erros']


def test_campos_opcionais_vazios_saem_do_oficio():
    oficio = enviar()['oficio']
    assert 'Link do evento' not in oficio
    assert 'Complemento' not in oficio


def test_erro_vazio_nao_esconde_erro_de_formato():
    resposta = enviar(n_usp='', cpf='123.456.789-00')
    assert resposta['erros'] == ['Preencha todos os campos', 'CPF inválido']
