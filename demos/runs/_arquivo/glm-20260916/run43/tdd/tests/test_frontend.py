import re

REFERENCIAS = re.compile(r'(src|href)\s*=\s*["\']?([^"\' >]+)', re.IGNORECASE)

ROTULOS_DAS_DUAS_ABAS = [
    'SOLICITANTE E EVENTO',
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
    'ENDEREÇO DO SOLICITANTE',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

ROTULOS_SO_NA_ABA_ALUNOS = ['NÍVEL', 'TIPO DE AUXÍLIO']


def _pagina(client):
    return client.get('/').text + client.get('/app.js').text


def test_pagina_inicial_e_servida(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers['content-type']


def test_abas_com_rotulos_exatos_nessa_ordem(client):
    pagina = _pagina(client)
    assert 'ALUNOS' in pagina
    assert 'DOCENTES' in pagina
    assert pagina.index('ALUNOS') < pagina.index('DOCENTES')


def test_cada_aba_tem_botao_enviar(client):
    assert _pagina(client).count('Enviar solicitação') >= 2


def test_rotulos_dos_campos_nas_duas_abas(client):
    pagina = _pagina(client)
    for rotulo in ROTULOS_DAS_DUAS_ABAS:
        assert pagina.count(rotulo) >= 2, f'rótulo esperado nas duas abas: {rotulo}'
    for rotulo in ROTULOS_SO_NA_ABA_ALUNOS:
        assert rotulo in pagina, f'rótulo esperado na aba ALUNOS: {rotulo}'


def test_cabecalho_institucional_com_logotipo(client):
    pagina = _pagina(client)
    assert 'assets/usp-logo.png' in pagina
    assert 'Universidade de São Paulo' in pagina


def test_arquivos_do_frontend_servidos(client):
    css = client.get('/style.css')
    assert css.status_code == 200
    assert 'text/css' in css.headers['content-type']
    js = client.get('/app.js')
    assert js.status_code == 200
    assert 'javascript' in js.headers['content-type']
    pagina = _pagina(client)
    assert 'style.css' in pagina
    assert 'app.js' in pagina


def test_logotipo_servido_como_imagem(client):
    resposta = client.get('/assets/usp-logo.png')
    assert resposta.status_code == 200
    assert resposta.headers['content-type'].startswith('image/')


def test_cores_e_fonte_da_identidade_no_css(client):
    css = client.get('/style.css').text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css, f'cor da USP ausente no CSS: {cor}'
    assert 'open sans' in css


def test_nenhuma_referencia_externa(client):
    html = client.get('/').text
    css = client.get('/style.css').text
    js = client.get('/app.js').text
    for texto in (html, css, js):
        for _atributo, valor in REFERENCIAS.findall(texto):
            assert not valor.lower().startswith(('http://', 'https://')), (
                f'referência externa não permitida: {valor}'
            )
    assert 'http://' not in css and 'https://' not in css


def test_brasao_nao_aparece(client):
    tudo = '\n'.join(
        [
            client.get('/').text,
            client.get('/style.css').text,
            client.get('/app.js').text,
        ]
    )
    assert not re.search(r'bras[ãa]o|escudo', tudo, re.IGNORECASE)


def test_todo_campo_tem_placeholder(client):
    campos = re.findall(r'<(?:input|textarea)[^>]*>', _pagina(client), re.IGNORECASE)
    assert campos, 'o formulário precisa de campos de entrada'
    for campo in campos:
        tipo = re.search(r'type\s*=\s*["\']?([\w-]+)', campo, re.IGNORECASE)
        if tipo and tipo.group(1).lower() in ('hidden', 'submit', 'button', 'image'):
            continue
        assert 'placeholder' in campo.lower(), f'campo sem placeholder: {campo}'


def test_oficio_preserva_quebras_de_linha(client):
    css = client.get('/style.css').text
    html = client.get('/').text
    tem_pre = re.search(r'white-space\s*:\s*pre', css, re.IGNORECASE)
    tem_tag_pre = re.search(r'<pre[\s>]', html, re.IGNORECASE)
    assert tem_pre or tem_tag_pre


def test_titulo_da_confirmacao(client):
    assert 'Solicitação registrada' in _pagina(client)
