from app import Solicitacao, montar_oficio, validar

DADOS = dict(
    nome='Maria Aparecida da Silva',
    n_usp='1234567',
    programa='Ciência da Computação',
    nivel='Mestrado',
    tipo_auxilio='Participação em evento',
    email='maria@usp.br',
    nome_evento='Congresso Brasileiro de Computação',
    periodo_evento='10/03/2025 a 14/03/2025',
    cidade_evento='Salvador',
    estado_evento='BA',
    pais_evento='Brasil',
    link_evento='https://cbc.sbc.org.br',
    valor_solicitado='R$ 1.500,00',
    detalhamento='Passagem aérea e inscrição no evento',
    apresentacao='Pôster',
    data_nascimento='01/02/1980',
    logradouro='Rua do Matão',
    numero='1010',
    complemento='Sala 222',
    bairro='Cidade Universitária',
    cep='05508-090',
    cidade='São Paulo',
    estado='SP',
    cpf='111.444.777-35',
    rg_rnm='12.345.678-9',
    banco='Banco do Brasil',
    agencia='1234',
    conta='12345-6',
)


def test_alunos_valido_gera_oficio():
    solicitacao = Solicitacao(**DADOS)
    assert validar(solicitacao) == []
    oficio = montar_oficio(solicitacao)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in oficio
    assert 'Programa: Ciência da Computação - Mestrado' in oficio
    assert 'Valor solicitado: R$ 1.500,00' in oficio


def test_docentes_sem_nivel_e_tipo():
    dados = {c: v for c, v in DADOS.items() if c not in ('nivel', 'tipo_auxilio')}
    solicitacao = Solicitacao(tipo='docentes', **dados)
    assert validar(solicitacao) == []
    oficio = montar_oficio(solicitacao)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in oficio
    assert 'Programa: Ciência da Computação\n' in oficio


def test_formulario_vazio():
    assert validar(Solicitacao()) == ['Preencha todos os campos']


def test_todas_as_mensagens():
    dados = dict(
        DADOS,
        n_usp='12a3',
        agencia='12x',
        valor_solicitado='R$ 0,00',
        email='maria.usp.br',
        cpf='111.444.777-00',
        cep='05508090',
        data_nascimento='31/02/1980',
    )
    assert validar(Solicitacao(**dados)) == [
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CEP deve estar no formato 00000-000',
        'CPF inválido',
        'Data de nascimento inválida',
    ]


def test_opcionais_vazios_saem_do_oficio():
    dados = dict(DADOS, link_evento='', complemento='')
    oficio = montar_oficio(Solicitacao(**dados))
    assert 'Link do evento' not in oficio
    assert 'Complemento' not in oficio
