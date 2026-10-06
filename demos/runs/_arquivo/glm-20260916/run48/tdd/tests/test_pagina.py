from helpers import ENDPOINT, corpo, dados_alunos

TITULOS_DOS_BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS_DOS_CAMPOS = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'NÍVEL',
    'TIPO DE AUXÍLIO',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAÍS DO EVENTO, EXAME OU DEFESA',
    'LINK DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

OPCOES_DE_SELECAO = [
    'Mestrado',
    'Doutorado',
    'Participação em evento',
    'Banca de exame ou defesa',
    'Outro',
    'Pôster',
    'Apresentação oral',
    'Outra',
    'Não irá apresentar trabalho',
]


def test_pagina_inicial_servida_como_html(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers['content-type']


def test_abas_com_rotulos_exatos_nessa_ordem(cliente):
    html = cliente.get('/').text
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_tres_blocos_com_titulos_visiveis(cliente):
    html = cliente.get('/').text
    for titulo in TITULOS_DOS_BLOCOS:
        assert titulo in html


def test_rotulos_dos_campos_exatos(cliente):
    html = cliente.get('/').text
    for rotulo in ROTULOS_DOS_CAMPOS:
        assert rotulo in html


def test_opcoes_das_selecoes_exatas(cliente):
    html = cliente.get('/').text
    for opcao in OPCOES_DE_SELECAO:
        assert opcao in html


def test_botao_enviar_em_cada_aba(cliente):
    html = cliente.get('/').text
    assert html.count('Enviar solicitação') >= 2


def test_campos_com_placeholder(cliente):
    html = cliente.get('/').text
    assert html.lower().count('placeholder') >= 25


def test_cabecalho_institucional_da_usp(cliente):
    html = cliente.get('/').text
    assert 'usp-logo.png' in html
    assert 'Universidade de São Paulo' in html


def test_sem_brasao_na_pagina(cliente):
    html = cliente.get('/').text.lower()
    assert 'brasao' not in html
    assert 'brasão' not in html


def test_arquivos_estaticos_servidos(cliente):
    assert cliente.get('/style.css').status_code == 200
    assert cliente.get('/app.js').status_code == 200
    logo = cliente.get('/assets/usp-logo.png')
    assert logo.status_code == 200
    assert logo.headers['content-type'].startswith('image/')


def test_css_com_as_cores_da_usp(cliente):
    css = cliente.get('/style.css').text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css


def test_fonte_sem_serifa(cliente):
    css = cliente.get('/style.css').text
    assert 'Open Sans' in css or 'sans-serif' in css


def test_nenhum_recurso_vem_da_rede(cliente):
    html = cliente.get('/').text
    css = cliente.get('/style.css').text
    assert 'src="http' not in html
    assert 'href="http' not in html
    assert 'url(http' not in css.lower()


def test_titulo_da_confirmacao_presente_na_aplicacao(cliente):
    html = cliente.get('/').text
    js = cliente.get('/app.js').text
    resposta = cliente.post(ENDPOINT, =dados_alunos())
    assert 'Solicitação registrada' in html + js + corpo(resposta)
