import pytest

from conftest import GRUPOS, campos, trocar

OFICIO = 'Encaminhe-se ao Serviço Financeiro'

CASOS = [
    ('n_usp', '12a3456', 'N. USP deve conter apenas números'),
    ('agencia', '12a4', 'Número da agência deve conter apenas números'),
    ('valor', '0', 'Valor solicitado deve ser maior que 0'),
    ('email', 'maria.usp.br', 'E-mail inválido'),
    ('email', 'maria@', 'E-mail inválido'),
    ('cpf', '12345678909', 'CPF deve estar no formato 000.000.000-00'),
    ('cpf', '123.456.789-00', 'CPF inválido'),
    ('cep', '05508090', 'CEP deve estar no formato 00000-000'),
    (
        'data_nascimento',
        '01021980',
        'Data de nascimento deve estar no formato dd/mm/aaaa',
    ),
    ('data_nascimento', '31/02/1980', 'Data de nascimento inválida'),
    ('data_nascimento', '15/13/1980', 'Data de nascimento inválida'),
]


@pytest.mark.parametrize(('campo', 'valor_invalido', 'mensagem'), CASOS)
def test_erro_de_validacao(post_solicitacao, campo, valor_invalido, mensagem):
    dados = campos()
    trocar(dados, campo, valor_invalido)
    resposta = post_solicitacao(dados, mensagem)
    assert mensagem in resposta.text
    assert OFICIO not in resposta.text


def test_campos_vazios_geram_uma_unica_mensagem(post_solicitacao):
    dados = campos(vazios=set(GRUPOS))
    resposta = post_solicitacao(dados, 'Preencha todos os campos')
    assert resposta.text.count('Preencha todos os campos') == 1
    assert OFICIO not in resposta.text


def test_todas_as_mensagens_que_se_aplicam(post_solicitacao):
    dados = campos()
    trocar(dados, 'n_usp', '12a3456')
    trocar(dados, 'email', 'maria.usp.br')
    resposta = post_solicitacao(dados, 'N. USP deve conter apenas números')
    assert 'N. USP deve conter apenas números' in resposta.text
    assert 'E-mail inválido' in resposta.text


def test_validacao_igual_na_aba_docentes(post_solicitacao):
    dados = campos('docentes')
    trocar(dados, 'cep', '05508090')
    resposta = post_solicitacao(dados, 'CEP deve estar no formato 00000-000')
    assert 'CEP deve estar no formato 00000-000' in resposta.text
    assert OFICIO not in resposta.text
