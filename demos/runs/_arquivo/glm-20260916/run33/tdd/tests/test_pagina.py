import pytest

BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS = [
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

OPCOES = [
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


def test_arquivos_estaticos_servidos(client):
    raiz = client.get('/')
    assert raiz.status_code == 200
    assert 'text/html' in raiz.headers['content-type']
    assert client.get('/style.css').status_code == 200
    js = client.get('/app.js')
    assert js.status_code == 200
    assert 'javascript' in js.headers['content-type']
    assert client.get('/assets/usp-logo.png').status_code == 200


def test_cabecalho_institucional(arquivos_front):
    assert 'Universidade de São Paulo' in arquivos_front
    assert 'usp-logo.png' in arquivos_front


def test_abas_com_rotulos_exatos_nessa_ordem(pagina):
    assert pagina.index('ALUNOS') < pagina.index('DOCENTES')


def test_cada_aba_tem_seu_botao_de_envio(pagina):
    assert pagina.count('Enviar solicitação') >= 2


def test_campos_tem_placeholder_de_exemplo(pagina):
    assert 'placeholder' in pagina


def test_titulo_da_confirmacao(pagina):
    assert 'Solicitação registrada' in pagina


@pytest.mark.parametrize('titulo', BLOCOS)
def test_titulos_dos_blocos(pagina, titulo):
    assert titulo in pagina


@pytest.mark.parametrize('rotulo', ROTULOS)
def test_rotulos_exatos(pagina, rotulo):
    assert rotulo in pagina


@pytest.mark.parametrize('opcao', OPCOES)
def test_opcoes_das_selecoes(pagina, opcao):
    assert opcao in pagina


def test_cores_da_identidade_usp(client):
    css = client.get('/style.css').text
    assert '#1094ab' in css
    assert '#64c4d2' in css
    assert '#fcb421' in css


def test_fonte_open_sans_com_fallback_sem_serifa(client):
    css = client.get('/style.css').text
    assert 'Open Sans' in css
    assert 'sans-serif' in css
