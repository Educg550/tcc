from app import Solicitacao, construir_oficio, validar

BASE = {
    'aba': 'ALUNOS',
    'nome': 'Maria Souza da Silva',
    'n_usp': '1234567',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria.silva@usp.br',
    'evento': 'Congresso da SBC',
    'periodo': '10/07/2025 a 14/07/2025',
    'cidade_evento': 'Rio de Janeiro',
    'estado_evento': 'RJ',
    'pais_evento': 'Brasil',
    'link_evento': '',
    'valor': 'R$ 1.500,00',
    'detalhamento': 'Inscrição no evento',
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
    'rg': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '12345-6',
}


def test_solicitacao_valida_gera_oficio():
    d = Solicitacao(**BASE)
    assert validar(d) == []
    oficio = construir_oficio(d)
    assert 'Interessada(o): Maria Souza da Silva - 1234567' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in oficio
    assert 'Programa: Ciência da Computação - Mestrado' in oficio
    assert 'Valor solicitado: R$ 1.500,00' in oficio
    assert 'Link do evento' not in oficio
    assert 'Complemento' not in oficio


def test_docentes_gera_oficio_sem_nivel_e_tipo():
    dados = dict(BASE, aba='DOCENTES')
    del dados['nivel']
    del dados['tipo_auxilio']
    d = Solicitacao(**dados)
    assert validar(d) == []
    oficio = construir_oficio(d)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Ciência da Computação\n' in oficio


def test_campo_obrigatorio_vazio():
    assert validar(Solicitacao(**dict(BASE, nome=''))) == ['Preencha todos os campos']


def test_validacoes_de_formato():
    assert 'N. USP deve conter apenas números' in validar(Solicitacao(**dict(BASE, n_usp='abc123')))
    assert 'Número da agência deve conter apenas números' in validar(Solicitacao(**dict(BASE, agencia='12a4')))
    assert 'Valor solicitado deve ser maior que 0' in validar(Solicitacao(**dict(BASE, valor='R$ 0,00')))
    assert 'E-mail inválido' in validar(Solicitacao(**dict(BASE, email='maria.sem-arroba')))
    assert 'CPF deve estar no formato 000.000.000-00' in validar(Solicitacao(**dict(BASE, cpf='12345678909')))
    assert 'CPF inválido' in validar(Solicitacao(**dict(BASE, cpf='123.456.789-00')))
    assert 'CEP deve estar no formato 00000-000' in validar(Solicitacao(**dict(BASE, cep='05508090')))
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in validar(Solicitacao(**dict(BASE, data_nascimento='1/2/1980')))
    assert 'Data de nascimento inválida' in validar(Solicitacao(**dict(BASE, data_nascimento='30/02/1980')))
