import re

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

TITULOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
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


def _elemento_com_texto(html, texto):
    return re.search(r'>\s*' + re.escape(texto) + r'\s*<', html)


def _tem_recurso_remoto(texto):
    padroes = [
        r'''<script[^>]+src=["']https?://''',
        r'''<link[^>]+href=["']https?://''',
        r'''<img[^>]+src=["']https?://''',
        r'''@import\s+["']?https?://''',
        r'''url\(\s*["']?https?://''',
    ]
    return any(re.search(padrao, texto, re.IGNORECASE) for padrao in padroes)


def test_pagina_inicial_e_servida(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = client.get('/').text
    alunos = _elemento_com_texto(html, 'ALUNOS')
    docentes = _elemento_com_texto(html, 'DOCENTES')
    assert alunos is not None
    assert docentes is not None
    assert alunos.start() < docentes.start()


def test_tres_blocos_com_titulos_visiveis(client):
    html = client.get('/').text
    for titulo in TITULOS:
        assert _elemento_com_texto(html, titulo) is not None, titulo


def test_todos_os_rotulos_estao_na_pagina(client):
    html = client.get('/').text
    for rotulo in ROTULOS:
        assert _elemento_com_texto(html, rotulo) is not None, rotulo


def test_opcoes_das_selecoes(client):
    html = client.get('/').text
    for opcao in OPCOES:
        assert _elemento_com_texto(html, opcao) is not None, opcao


def test_cada_aba_tem_botao_enviar_solicitacao(client):
    html = client.get('/').text
    assert len(re.findall(r'>\s*Enviar solicitação\s*<', html)) >= 2


def test_cabecalho_institucional_da_usp(client):
    html = client.get('/').text
    assert 'Universidade de São Paulo' in html
    assert 'assets/usp-logo.png' in html
    assert 'brasao' not in html.lower()
    assert 'escudo' not in html.lower()


def test_logo_e_servida_como_estatico(client):
    assert client.get('/assets/usp-logo.png').status_code == 200


def test_style_css_e_app_js_sao_servidos(client):
    assert client.get('/style.css').status_code == 200
    assert client.get('/app.js').status_code == 200
    html = client.get('/').text
    assert 'style.css' in html
    assert 'app.js' in html


def test_css_usa_as_cores_da_usp_e_open_sans(client):
    css = client.get('/style.css').text.lower()
    assert '#1094ab' in css
    assert '#64c4d2' in css
    assert '#fcb421' in css
    assert 'open sans' in css


def test_nenhum_recurso_vem_da_rede(client):
    html = client.get('/').text
    css = client.get('/style.css').text
    assert not _tem_recurso_remoto(html)
    assert not _tem_recurso_remoto(css)


def test_titulo_da_confirmacao_esta_na_aplicacao(client):
    html = client.get('/').text
    js = client.get('/app.js').text
    assert 'Solicitação registrada' in html or 'Solicitação registrada' in js


def test_placeholders_sao_exemplos_nao_rotulos(client):
    html = client.get('/').text
    placeholders = re.findall(r'''placeholder\s*=\s*["']([^"']+)["']''', html)
    assert placeholders
    for placeholder in placeholders:
        assert placeholder.strip(), placeholder
        assert placeholder not in ROTULOS, placeholder
