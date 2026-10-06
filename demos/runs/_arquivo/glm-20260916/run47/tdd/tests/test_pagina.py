import re

TITULOS = [
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


def test_pagina_inicial_disponivel(client, html):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers['content-type']
    assert '<html' in html.lower()
    assert 'style.css' in html
    assert 'app.js' in html


def test_abas_alunos_e_docentes_nessa_ordem(html):
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_aba_alunos_ativa_ao_abrir(html):
    posicao = html.index('ALUNOS')
    janela = html[max(0, posicao - 400):posicao + 400]
    marcas = ('active', 'ativa', 'aria-selected', 'aria-current')
    assert any(marca in janela for marca in marcas)


def test_tres_blocos_na_ordem(html):
    posicao = -1
    for titulo in TITULOS:
        ache = html.find(titulo, posicao + 1)
        assert ache != -1, f'título ausente: {titulo}'
        assert ache > posicao, f'título fora de ordem: {titulo}'
        posicao = ache


def test_rotulos_exatos_e_na_ordem(html):
    posicao = -1
    for rotulo in ROTULOS:
        ache = html.find(rotulo, posicao + 1)
        assert ache != -1, f'rótulo ausente: {rotulo}'
        assert ache > posicao, f'rótulo fora de ordem: {rotulo}'
        posicao = ache


def test_campos_presentes_nas_duas_abas(html):
    for rotulo in ROTULOS:
        minimo = 1 if rotulo in ('NÍVEL', 'TIPO DE AUXÍLIO') else 2
        assert html.count(rotulo) >= minimo, f'rótulo insuficiente: {rotulo}'


def test_formulario_docentes_sem_nivel_e_sem_tipo_de_auxilio(html):
    primeiro = html.find('N. USP')
    segundo = html.find('N. USP', primeiro + 1)
    assert segundo != -1
    docentes = html[segundo:]
    assert 'NÍVEL' not in docentes
    assert 'TIPO DE AUXÍLIO' not in docentes


def test_botao_enviar_em_cada_aba(html):
    assert html.count('Enviar solicitação') >= 2


def test_todo_campo_tem_placeholder_de_exemplo(html):
    valores = re.findall(r'placeholder="([^"]*)"', html)
    valores += re.findall(r"placeholder='([^']*)'", html)
    assert len(valores) >= 50
    rotulos = {rotulo.strip().casefold() for rotulo in ROTULOS}
    for valor in valores:
        assert valor.strip().casefold() not in rotulos


def test_logotipo_e_nome_da_universidade(client, html):
    assert 'usp-logo.png' in html
    assert 'Universidade de São Paulo' in html
    resposta = client.get('/assets/usp-logo.png')
    assert resposta.status_code == 200
    assert resposta.headers['content-type'].startswith('image/')


def test_brasao_nao_aparece(html, js):
    pagina = (html + js).lower()
    for marca in ('brasao', 'brasão', 'escudo'):
        assert marca not in pagina


def test_cores_da_universidade(css):
    estilo = css.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in estilo


def test_fonte_open_sans(css):
    estilo = css.lower()
    assert 'open sans' in estilo
    assert 'sans-serif' in estilo


def test_aba_ativa_distinguivel_no_estilo(css):
    estilo = css.lower()
    marcas = ('active', 'ativa', 'aria-selected', 'aria-current')
    assert any(marca in estilo for marca in marcas)


def test_nenhum_recurso_externo(html, css):
    estilo = css.lower()
    assert '@import' not in estilo
    assert 'url(http' not in estilo
    pagina = html.lower()
    assert '"http' not in pagina
    assert "'http" not in pagina


def test_oficio_preserva_quebras_de_linha(css, html):
    assert 'white-space' in css.lower() or '<pre' in html.lower()


def test_app_js_envia_a_solicitacao_ao_backend(js):
    assert 'fetch(' in js or 'XMLHttpRequest' in js
    assert 'R$' in js
