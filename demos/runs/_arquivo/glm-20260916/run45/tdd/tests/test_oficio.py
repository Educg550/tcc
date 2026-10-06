import pytest

from helpers import (
    DADOS_ALUNOS,
    DADOS_DOCENTES,
    EXTRAS_ALUNOS,
    EXTRAS_DOCENTES,
    montar_payload,
    substituir,
)

LINHAS_DO_OFICIO_ALUNOS = [
    'Interessada(o): Maria da Silva - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'A CCP-Ciência da Computação aprovou na data de hoje',
    'Dados do evento',
    'Evento: SBBD',
    'Período: 1 a 4 de outubro de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://sbbd.org.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagens aéreas e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Sala 214',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 12345-6',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


def test_oficio_da_aba_alunos(solicitar):
    texto = solicitar(montar_payload(DADOS_ALUNOS, EXTRAS_ALUNOS), 'Mestrado')
    for linha in LINHAS_DO_OFICIO_ALUNOS:
        assert linha in texto, f'linha ausente no ofício: {linha}'


def test_oficio_da_aba_docentes(solicitar):
    texto = solicitar(montar_payload(DADOS_DOCENTES, EXTRAS_DOCENTES), 'Verba do programa')
    assert 'Interessada(o): Maria da Silva - 1234567' in texto
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'A CCP-Ciência da Computação aprovou na data de hoje' in texto
    assert 'Valor solicitado: R$ 1.500,00' in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto
    assert 'Mestrado' not in texto
    assert 'Doutorado' not in texto
    assert 'Participação em evento' not in texto


def test_linhas_de_campos_opcionais_vazios_saem_do_oficio(solicitar):
    dados = substituir(DADOS_ALUNOS, link_evento='', complemento='')
    texto = solicitar(montar_payload(dados, EXTRAS_ALUNOS), 'R$ 1.500,00')
    assert 'Link do evento' not in texto
    assert 'Complemento' not in texto
    assert 'Valor solicitado: R$ 1.500,00' in texto


def test_campo_obrigatorio_vazio_nao_gera_oficio(solicitar):
    dados = substituir(DADOS_ALUNOS, nome_completo='', logradouro='')
    texto = solicitar(montar_payload(dados, EXTRAS_ALUNOS), 'Preencha todos os campos')
    assert 'Preencha todos os campos' in texto
    assert texto.count('Preencha todos os campos') == 1
    assert 'Interessada(o):' not in texto


@pytest.mark.parametrize(
    ('campo', 'valor', 'mensagem'),
    [
        ('numero_usp', '123a456', 'N. USP deve conter apenas números'),
        ('numero_agencia', '12a4', 'Número da agência deve conter apenas números'),
        ('valor_solicitado', '0', 'Valor solicitado deve ser maior que 0'),
        ('email', 'maria.usp.br', 'E-mail inválido'),
        ('cpf', '123.456.789-0', 'CPF deve estar no formato 000.000.000-00'),
        ('cep', '0550-8090', 'CEP deve estar no formato 00000-000'),
        ('data_nascimento', '01-02-1980', 'Data de nascimento deve estar no formato dd/mm/aaaa'),
        ('cpf', '123.456.789-00', 'CPF inválido'),
        ('data_nascimento', '31/02/1980', 'Data de nascimento inválida'),
    ],
)
def test_mensagens_de_validacao(solicitar, campo, valor, mensagem):
    dados = substituir(DADOS_ALUNOS, **{campo: valor})
    texto = solicitar(montar_payload(dados, EXTRAS_ALUNOS), mensagem)
    assert mensagem in texto
    assert 'Interessada(o):' not in texto


def test_todas_as_mensagens_aplicaveis_aparecem_juntas(solicitar):
    dados = substituir(
        DADOS_ALUNOS,
        numero_usp='12a',
        email='maria.usp.br',
        cep='0550-8090',
    )
    texto = solicitar(
        montar_payload(dados, EXTRAS_ALUNOS),
        'N. USP deve conter apenas números',
    )
    assert 'N. USP deve conter apenas números' in texto
    assert 'E-mail inválido' in texto
    assert 'CEP deve estar no formato 00000-000' in texto
    assert 'Interessada(o):' not in texto
