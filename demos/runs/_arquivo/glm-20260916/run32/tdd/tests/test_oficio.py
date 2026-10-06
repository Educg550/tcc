import pytest


def test_oficio_de_aluno(enviar, campos_alunos):
    oficio = enviar(campos_alunos)['oficio']
    assert oficio
    assert 'Interessada(o): Maria Silva - 1234567\nE-mail: maria.silva@usp.br' in oficio
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in oficio
    assert 'Programa: Ciência da Computação - Mestrado' in oficio
    assert 'A CCP-Ciência da Computação aprovou' in oficio
    for titulo in ('Dados do evento', 'Endereço da(o) interessada(o)', 'Dados para pagamento'):
        assert titulo in oficio
    assert 'Evento: SBES 2025' in oficio
    assert 'Período: 22 a 26 de setembro de 2025' in oficio
    assert 'Local: Fortaleza - Ceará - Brasil' in oficio
    assert 'Link do evento: https://sbes.org.br/2025' in oficio
    assert 'Apresentação de trabalho: Pôster' in oficio
    assert 'Valor solicitado: R$ 1.500,00' in oficio
    assert 'Detalhamento: Passagem aérea e inscrição no evento' in oficio
    assert 'Rua do Anfiteatro, 375' in oficio
    assert 'Complemento: Sala 2' in oficio
    assert 'CEP: 05508-090' in oficio
    assert 'Butantã, São Paulo - São Paulo' in oficio
    assert 'Data de nascimento: 01/02/1980' in oficio
    assert 'CPF: 111.444.777-35' in oficio
    assert 'RG / RNM: 12.345.678-9' in oficio
    assert 'Banco: Banco do Brasil' in oficio
    assert 'Agência: 0001' in oficio
    assert 'Conta: 12345-6' in oficio
    assert oficio.rstrip().endswith('Encaminhe-se ao Serviço Financeiro para providências.')


def test_oficio_de_docente(enviar, campos_docentes):
    dados = enviar(campos_docentes)
    assert dados['erros'] == []
    oficio = dados['oficio']
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Ciência da Computação\n' in oficio
    assert 'A CCP-Ciência da Computação aprovou' in oficio
    assert oficio.rstrip().endswith('Encaminhe-se ao Serviço Financeiro para providências.')


def test_oficio_de_docente_nao_cita_nivel(enviar, campos_docentes):
    oficio = enviar(campos_docentes)['oficio']
    assert 'Mestrado' not in oficio
    assert 'Doutorado' not in oficio


def test_linhas_de_campos_opicionais_somem_do_oficio(enviar, campos_alunos):
    campos = {
        **campos_alunos,
        'LINK DO EVENTO, EXAME OU DEFESA': '',
        'COMPLEMENTO': '',
    }
    dados = enviar(campos)
    assert dados['erros'] == []
    oficio = dados['oficio']
    assert 'Link do evento:' not in oficio
    assert 'Complemento:' not in oficio


@pytest.mark.parametrize(
    'digitos,mostrado',
    [
        ('1500', 'R$ 15,00'),
        ('150000', 'R$ 1.500,00'),
        ('150000000', 'R$ 1.500.000,00'),
    ],
)
def test_valor_no_oficio_em_moeda_brasileira(enviar, campos_alunos, digitos, mostrado):
    oficio = enviar({**campos_alunos, 'VALOR SOLICITADO (R$)': digitos})['oficio']
    assert 'Valor solicitado: ' + mostrado in oficio
