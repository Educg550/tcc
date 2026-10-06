def _junto(client, *caminhos):
    return ''.join(client.get(c).text for c in caminhos)


def test_pagina_inicial_responde_com_html(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')
    assert 'style.css' in resposta.text
    assert 'app.js' in resposta.text


def test_abas_alunos_e_docentes_nessa_ordem(client):
    tudo = _junto(client, '/', '/app.js')
    assert 'ALUNOS' in tudo
    assert 'DOCENTES' in tudo
    assert tudo.index('ALUNOS') < tudo.index('DOCENTES')


def test_aba_alunos_e_a_ativa_ao_abrir(client):
    tudo = _junto(client, '/', '/style.css', '/app.js')
    marcadores = ('ativa', 'active', 'selected', 'checked')
    assert any(m in tudo for m in marcadores)


def test_tres_blocos_com_titulos_visiveis(client):
    tudo = _junto(client, '/', '/app.js')
    for titulo in (
        'SOLICITANTE E EVENTO',
        'ENDEREÇO DO SOLICITANTE',
        'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    ):
        assert titulo in tudo


_ROTULOS = [
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


def test_rotulos_dos_campos_exatos(client):
    tudo = _junto(client, '/', '/app.js')
    for rotulo in _ROTULOS:
        assert rotulo in tudo


def test_rotulos_exclusivos_da_aba_alunos_aparecem_uma_vez(client):
    tudo = _junto(client, '/', '/app.js')
    assert tudo.count('NÍVEL') == 1
    assert tudo.count('TIPO DE AUXÍLIO') == 1


def test_opcoes_das_selecoes(client):
    tudo = _junto(client, '/', '/app.js')
    for opcao in (
        'Mestrado',
        'Doutorado',
        'Participação em evento',
        'Banca de exame ou defesa',
        'Outro',
        'Pôster',
        'Apresentação oral',
        'Outra',
        'Não irá apresentar trabalho',
    ):
        assert opcao in tudo


def test_botao_enviar_solicitacao_em_cada_aba(client):
    tudo = _junto(client, '/', '/app.js')
    assert tudo.count('Enviar solicitação') >= 2


def test_todo_campo_tem_placeholder(client):
    tudo = _junto(client, '/', '/app.js')
    assert tudo.count('placeholder') >= 30


def test_cabecalho_institucional_com_logo(client):
    html = client.get('/').text
    assert 'assets/usp-logo.png' in html
    assert 'Universidade de São Paulo' in html
    baixo = html.lower()
    assert 'brasao' not in baixo
    assert 'brasão' not in baixo


def test_imagem_do_logo_e_servida(client):
    resposta = client.get('/assets/usp-logo.png')
    assert resposta.status_code == 200
    assert resposta.headers.get('content-type', '').startswith('image/')
    assert resposta.content


def test_css_e_js_sao_servidos(client):
    css = client.get('/style.css')
    js = client.get('/app.js')
    assert css.status_code == 200
    assert js.status_code == 200
    assert css.text.strip()
    assert js.text.strip()


def test_css_usa_a_identidade_da_usp(client):
    css = client.get('/style.css').text
    assert '#1094ab' in css
    assert 'Open Sans' in css
    assert '#64c4d2' in css or '#fcb421' in css


def test_titulo_da_confirmacao_existe(client):
    tudo = _junto(client, '/', '/app.js')
    assert 'Solicitação registrada' in tudo


def test_nenhum_recurso_remoto(client):
    tudo = _junto(client, '/', '/style.css')
    for proibido in (
        'fonts.googleapis.com',
        'fonts.gstatic.com',
        'cdn.jsdelivr',
        'unpkg.com',
        'url(http',
        "@import url('http",
        '@import url("http',
    ):
        assert proibido not in tudo
