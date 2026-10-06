import pytest

CAMPOS = [
    ('NOME COMPLETO - SEM ABREVIAR', 'Maria Souza da Silva', ('nome_completo',)),
    ('N. USP', '1234567', ('n_usp', 'numero_usp')),
    ('PROGRAMA', 'Ciência da Computação', ('programa',)),
    ('NÍVEL', 'Mestrado', ('nivel',)),
    ('TIPO DE AUXÍLIO', 'Participação em evento', ('tipo_auxilio', 'tipo_de_auxilio')),
    ('E-MAIL', 'maria@usp.br', ('email',)),
    ('NOME DO EVENTO / BANCA DE EXAME OU DEFESA', 'SBBD', ('nome_evento', 'nome_do_evento', 'evento')),
    ('PERÍODO DO EVENTO, EXAME OU DEFESA', '1 a 4 de outubro de 2025', ('periodo_evento', 'periodo_do_evento', 'periodo')),
    ('CIDADE DO EVENTO, EXAME OU DEFESA', 'São Paulo', ('cidade_evento', 'cidade_do_evento')),
    ('ESTADO DO EVENTO, EXAME OU DEFESA', 'SP', ('estado_evento', 'estado_do_evento')),
    ('PAÍS DO EVENTO, EXAME OU DEFESA', 'Brasil', ('pais_evento', 'pais_do_evento')),
    ('LINK DO EVENTO, EXAME OU DEFESA', 'https://sbbd.org.br', ('link_evento', 'link_do_evento', 'link')),
    ('VALOR SOLICITADO (R$)', 'R$ 1.500,00', ('valor_solicitado', 'valor')),
    ('DETALHAMENTO DO PEDIDO', 'Passagem aérea e inscrição no evento', ('detalhamento', 'detalhamento_do_pedido')),
    ('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', 'Pôster', ('apresentacao_trabalho', 'ira_apresentar_trabalho', 'apresentacao')),
    ('DATA DE NASCIMENTO', '01/02/1980', ('data_nascimento', 'data_de_nascimento')),
    ('LOGRADOURO', 'Rua do Anfiteatro', ('logradouro', 'endereco')),
    ('NÚMERO', '181', ('numero', 'numero_endereco')),
    ('COMPLEMENTO', 'Sala 12', ('complemento',)),
    ('BAIRRO', 'Cidade Universitária', ('bairro',)),
    ('CEP', '05508-090', ('cep',)),
    ('CIDADE', 'São Paulo', ('cidade',)),
    ('ESTADO', 'SP', ('estado',)),
    ('CPF (SEPARADOS POR PONTOS E TRAÇO)', '123.456.789-09', ('cpf',)),
    ('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', '12.345.678-9', ('rg_rnm', 'rg', 'rnm')),
    ('NOME DO BANCO', 'Banco do Brasil', ('nome_banco', 'nome_do_banco', 'banco')),
    ('NÚMERO DA AGÊNCIA', '1234', ('agencia', 'numero_da_agencia', 'numero_agencia')),
    ('NÚMERO DA CONTA', '98765-4', ('conta', 'numero_da_conta', 'numero_conta')),
]

ROTULO_APELIDOS = {rotulo: apelidos for rotulo, _, apelidos in CAMPOS}

DISCRIMINADORES = ('aba', 'perfil', 'categoria', 'tipo_solicitante', 'tipo_de_solicitante')

CAMINHOS = [
    '/api/solicitacao',
    '/solicitacao',
    '/api/solicitar',
    '/solicitar',
    '/api/solicitacoes',
    '/solicitacoes',
    '/api/solicitacao/alunos',
    '/solicitacao/alunos',
    '/api/auxilio',
    '/auxilio',
    '/api/enviar',
    '/enviar',
    '/',
]

CAMINHOS_DOCENTES = [
    '/api/solicitacao/docentes',
    '/solicitacao/docentes',
    '/api/docentes',
    '/docentes',
]


def _base(apelidos):
    base = {}
    for rotulo, valor, apelidos_do_campo in CAMPOS:
        base[rotulo] = valor
        if apelidos:
            for apelido in apelidos_do_campo:
                base[apelido] = valor
    return base


def _com_discriminadores(base, valor):
    payload = dict(base)
    for chave in DISCRIMINADORES:
        payload[chave] = valor
    return payload


def _descobrir(client):
    for apelidos in (False, True):
        for valor_numerico in (False, True):
            base = _base(apelidos)
            if valor_numerico:
                base['VALOR SOLICITADO (R$)'] = 1500
                if apelidos:
                    base['valor_solicitado'] = 1500
                    base['valor'] = 1500
            for caminho in CAMINHOS:
                for valor_aba in ('ALUNOS', 'alunos', 'ALUNO', 'aluno'):
                    payload = _com_discriminadores(base, valor_aba)
                    try:
                        resposta = client.post(caminho, =payload)
                    except Exception:
                        continue
                    if 'Interessada(o):' in resposta.text and 'Preencha todos os campos' not in resposta.text:
                        return {'caminho': caminho, 'base': base, 'valor_aba': valor_aba}
    return None


_achado = {}


@pytest.fixture(scope='module')
def envio(client):
    achado = _descobrir(client)
    if achado is None:
        pytest.fail('nenhum endpoint do backend respondeu a uma solicitação de aluno válida')
    _achado.update(achado)

    def enviar(alt=None):
        payload = _com_discriminadores(_achado['base'], _achado['valor_aba'])
        if alt:
            for campo, valor in alt.items():
                payload[campo] = valor
                for apelido in ROTULO_APELIDOS.get(campo, ()):                    
                    if apelido in payload:
                        payload[apelido] = valor
        return client.post(_achado['caminho'], =payload)

    return enviar


@pytest.fixture(scope='module')
def base(envio):
    return _achado['base']


CASOS_DE_ERRO = [
    ('N. USP', '1234a567', 'N. USP deve conter apenas números'),
    ('NÚMERO DA AGÊNCIA', '12a4', 'Número da agência deve conter apenas números'),
    ('E-MAIL', 'maria.souza', 'E-mail inválido'),
    ('CPF (SEPARADOS POR PONTOS E TRAÇO)', '123.456.789-0', 'CPF deve estar no formato 000.000.000-00'),
    ('CEP', '0550809', 'CEP deve estar no formato 00000-000'),
    ('DATA DE NASCIMENTO', '01-02-1980', 'Data de nascimento deve estar no formato dd/mm/aaaa'),
    ('CPF (SEPARADOS POR PONTOS E TRAÇO)', '123.456.789-00', 'CPF inválido'),
    ('DATA DE NASCIMENTO', '31/02/2000', 'Data de nascimento inválida'),
]


@pytest.mark.parametrize('campo, valor, mensagem', CASOS_DE_ERRO)
def test_erro_de_campo_especifico(envio, campo, valor, mensagem):
    resposta = envio({campo: valor})
    assert mensagem in resposta.text
    assert 'Interessada(o):' not in resposta.text


def test_valor_zero_e_rejeitado(envio, base):
    invalido = 0 if isinstance(base['VALOR SOLICITADO (R$)'], int) else 'R$ 0,00'
    resposta = envio({'VALOR SOLICITADO (R$)': invalido})
    assert 'Valor solicitado deve ser maior que 0' in resposta.text
    assert 'Interessada(o):' not in resposta.text


def test_formulario_vazio_mostra_mensagem_unica(envio, base):
    vazio = {campo: '' for campo in base if campo not in DISCRIMINADORES}
    resposta = envio(vazio)
    assert 'Preencha todos os campos' in resposta.text
    assert resposta.text.count('Preencha todos os campos') == 1
    assert 'Interessada(o):' not in resposta.text


def test_dois_erros_aparecem_juntos(envio):
    resposta = envio({'N. USP': '1234a567', 'E-MAIL': 'maria.souza'})
    assert 'N. USP deve conter apenas números' in resposta.text
    assert 'E-mail inválido' in resposta.text


LINHAS_DO_OFICIO = [
    'Interessada(o): Maria Souza da Silva - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'CCP-Ciência da Computação aprovou',
    'Dados do evento',
    'Evento: SBBD',
    'Período: 1 a 4 de outubro de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://sbbd.org.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Sala 12',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]


@pytest.mark.parametrize('linha', LINHAS_DO_OFICIO)
def test_oficio_do_aluno(envio, linha):
    assert linha in envio().text


def test_oficio_do_aluno_nao_menciona_verba_do_programa(envio):
    assert 'Verba do programa' not in envio().text


def test_opcionais_vazios_saem_do_oficio(envio):
    resposta = envio({'LINK DO EVENTO, EXAME OU DEFESA': '', 'COMPLEMENTO': ''})
    assert 'Link do evento:' not in resposta.text
    assert 'Complemento:' not in resposta.text


def _descobrir_docentes(client):
    excluidos = ('NÍVEL', 'TIPO DE AUXÍLIO', 'nivel', 'tipo_auxilio', 'tipo_de_auxilio')
    base = {campo: valor for campo, valor in _achado['base'].items() if campo not in excluidos}
    for caminho in [_achado['caminho'], *CAMINHOS_DOCENTES]:
        for valor_aba in ('DOCENTES', 'docentes', 'Docentes', 'DOCENTE', 'docente'):
            payload = _com_discriminadores(base, valor_aba)
            try:
                resposta = client.post(caminho, =payload)
            except Exception:
                continue
            if 'Verba do programa' in resposta.text and 'Interessada(o):' in resposta.text:
                return {'caminho': caminho, 'base': payload}
    return None


@pytest.fixture(scope='module')
def envio_docentes(client, envio):
    achado = _descobrir_docentes(client)
    if achado is None:
        pytest.fail('nenhum endpoint gerou o ofício da aba DOCENTES')

    def enviar(alt=None):
        payload = dict(achado['base'])
        if alt:
            for campo, valor in alt.items():
                payload[campo] = valor
                for apelido in ROTULO_APELIDOS.get(campo, ()):                    
                    if apelido in payload:
                        payload[apelido] = valor
        return client.post(achado['caminho'], =payload)

    return enviar


@pytest.mark.parametrize('linha', [
    'Interessada(o): Maria Souza da Silva - 1234567',
    'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
    'Programa: Ciência da Computação',
    'Encaminhe-se ao Serviço Financeiro para providências.',
])
def test_oficio_do_docente(envio_docentes, linha):
    assert linha in envio_docentes().text


def test_oficio_do_docente_nao_menciona_campos_de_aluno(envio_docentes):
    resposta = envio_docentes().text
    assert 'Mestrado' not in resposta
    assert 'Participação em evento' not in resposta
