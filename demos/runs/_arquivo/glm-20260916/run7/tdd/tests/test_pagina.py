import re

BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

BLOCO1 = [
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
]

BLOCO2 = [
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
]

BLOCO3 = [
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

ROTULOS = BLOCO1 + BLOCO2 + BLOCO3

ORDEM = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'COMPLEMENTO',
    'BAIRRO',
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


def test_pagina_inicial(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_abas_na_ordem(index):
    assert 'ALUNOS' in index
    assert 'DOCENTES' in index
    assert index.index('ALUNOS') < index.index('DOCENTES')


def test_blocos_na_ordem(index):
    posicoes = [index.find(titulo) for titulo in BLOCOS]
    assert -1 not in posicoes
    assert posicoes == sorted(posicoes)


def test_rotulos_exatos(index):
    for rotulo in ROTULOS:
        assert rotulo in index, f'rótulo ausente: {rotulo}'
    assert index.count('NÍVEL') == 1
    assert index.count('TIPO DE AUXÍLIO') == 1


def test_rotulos_na_ordem(index):
    posicoes = [index.find(rotulo) for rotulo in ORDEM]
    assert -1 not in posicoes
    assert posicoes == sorted(posicoes)


def test_opcoes_de_selecao(index):
    for opcao in OPCOES:
        assert opcao in index, f'opção ausente: {opcao}'


def test_botao_em_cada_aba(index):
    assert index.count('Enviar solicitação') >= 2


def test_cabecalho_institucional(index):
    assert 'Universidade de São Paulo' in index
    assert 'usp-logo.png' in index


def test_logo_servida(client):
    resp = client.get('/assets/usp-logo.png')
    assert resp.status_code == 200
    assert resp.content


def test_arquivos_estaticos(client):
    for caminho in ('/style.css', '/app.js'):
        resp = client.get(caminho)
        assert resp.status_code == 200
        assert resp.text.strip()


def test_cores_e_fonte_da_identidade(client):
    css = client.get('/style.css').text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css
    assert 'open sans' in css or 'sans-serif' in css


def test_sem_recursos_remotos(client, index):
    html = re.sub(r'placeholder="[^"]*"', '', index)
    html = re.sub(r"placeholder='[^']*'", '', html)
    for conteudo in (html, client.get('/style.css').text, client.get('/app.js').text):
        assert 'http://' not in conteudo
        assert 'https://' not in conteudo


def test_brasao_nao_aparece(client, index):
    css = client.get('/style.css').text.lower()
    for termo in ('brasão', 'brasao', 'escudo'):
        assert termo not in index.lower()
        assert termo not in css


def test_placeholders_com_exemplos(index):
    placeholders = re.findall(r'placeholder="([^"]*)"', index)
    placeholders += re.findall(r"placeholder='([^']*)'", index)
    assert len(placeholders) >= 45
    for placeholder in placeholders:
        assert placeholder not in ROTULOS, f'placeholder repete o rótulo: {placeholder}'


def test_titulo_da_confirmacao(client, index):
    js = client.get('/app.js').text
    assert 'Solicitação registrada' in index or 'Solicitação registrada' in js


def test_oficio_preserva_quebras_de_linha(client, index):
    css = client.get('/style.css').text.lower()
    js = client.get('/app.js').text.lower()
    com_css = 'white-space' in css and 'pre' in css
    assert com_css or '<pre' in index or '<pre' in js or 'pre-line' in js or 'pre-wrap' in js
