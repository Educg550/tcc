import re

ROTULOS_COMUNS = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
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

ORDEM_NA_ABA_ALUNOS = [
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


def _html_normalizado(client):
    return ' '.join(client.get('/').text.split())


def test_pagina_inicial_servida(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = _html_normalizado(client)
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_rotulos_comuns_aparecem_nas_duas_abas(client):
    html = _html_normalizado(client)
    for rotulo in ROTULOS_COMUNS:
        assert html.count(rotulo) >= 2, f'rótulo aparece menos de duas vezes: {rotulo}'


def test_campos_exclusivos_da_aba_alunos(client):
    html = _html_normalizado(client)
    assert html.count('NÍVEL') == 1
    assert html.count('TIPO DE AUXÍLIO') == 1


def test_titulos_dos_blocos_aparecem_nas_duas_abas(client):
    html = _html_normalizado(client)
    for titulo in [
        'SOLICITANTE E EVENTO',
        'ENDEREÇO DO SOLICITANTE',
        'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    ]:
        assert html.count(titulo) >= 2, titulo


def test_cada_aba_tem_botao_enviar(client):
    html = _html_normalizado(client)
    assert html.count('Enviar solicitação') >= 2


def test_opcoes_das_selecoes(client):
    html = _html_normalizado(client)
    for opcao in ['Mestrado', 'Doutorado', 'Participação em evento', 'Banca de exame ou defesa']:
        assert html.count(opcao) == 1, opcao
    for opcao in ['Pôster', 'Apresentação oral', 'Outra', 'Não irá apresentar trabalho']:
        assert html.count(opcao) >= 2, opcao


def test_ordem_dos_campos_na_aba_alunos(client):
    html = _html_normalizado(client)
    posicao = 0
    for rotulo in ORDEM_NA_ABA_ALUNOS:
        posicao = html.find(rotulo, posicao)
        assert posicao != -1, f'campo ausente ou fora de ordem: {rotulo}'
        posicao += 1


def test_arquivos_do_front_servidos(client):
    html = client.get('/').text
    referencia_css = re.search(r'href=.(\S*?style[.]css)', html)
    referencia_js = re.search(r'src=.(\S*?app[.]js)', html)
    assert referencia_css, 'o index.html não referencia style.css'
    assert referencia_js, 'o index.html não referencia app.js'
    css = client.get(referencia_css.group(1))
    assert css.status_code == 200
    assert 'css' in css.headers.get('content-type', '')
    js = client.get(referencia_js.group(1))
    assert js.status_code == 200
    assert 'javascript' in js.headers.get('content-type', '')


def test_cabecalho_institucional_da_usp(client):
    html = client.get('/').text
    assert 'Universidade de São Paulo' in html
    logo = re.search(r'src=.(\S*?usp-logo[.]png)', html)
    assert logo, 'o cabeçalho não usa assets/usp-logo.png'
    resposta = client.get(logo.group(1))
    assert resposta.status_code == 200
    assert resposta.headers.get('content-type', '').startswith('image/')


def test_identidade_visual_no_css(client):
    html = client.get('/').text
    referencia = re.search(r'href=.(\S*?style[.]css)', html)
    assert referencia, 'o index.html não referencia style.css'
    css = client.get(referencia.group(1)).text.lower()
    assert '#1094ab' in css
    assert 'open sans' in css or 'sans-serif' in css


def test_todo_campo_tem_placeholder(client):
    html = client.get('/').text
    assert html.count('placeholder') >= 40
