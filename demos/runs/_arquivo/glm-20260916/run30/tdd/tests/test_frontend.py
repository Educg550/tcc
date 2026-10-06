import re

import pytest

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

BLOCOS = [
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


def _estatico(client, caminhos):
    for caminho in caminhos:
        resposta = client.get(caminho)
        if resposta.status_code == 200:
            return resposta.text
    pytest.fail(f'nenhum destes caminhos serve o arquivo: {caminhos}')


@pytest.fixture(scope='module')
def html(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')
    return resposta.text


@pytest.fixture(scope='module')
def js(client):
    return _estatico(client, ['/app.js', '/static/app.js'])


@pytest.fixture(scope='module')
def css(client):
    return _estatico(client, ['/style.css', '/static/style.css'])


@pytest.fixture(scope='module')
def pagina(html, js):
    return html + '\n' + js


def test_pagina_e_recursos_estaticos_servidos(html, js, css):
    assert html.strip()
    assert js.strip()
    assert css.strip()


def test_abas_com_rotulos_exatos_nessa_ordem(pagina):
    assert 'ALUNOS' in pagina
    assert 'DOCENTES' in pagina
    assert pagina.index('ALUNOS') < pagina.index('DOCENTES')


def test_todos_os_rotulos_exatos_presentes(pagina):
    ausentes = [rotulo for rotulo in ROTULOS if rotulo not in pagina]
    assert not ausentes, f'rótulos ausentes: {ausentes}'


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos(pagina):
    assert pagina.count('NÍVEL') == 1
    assert pagina.count('TIPO DE AUXÍLIO') == 1


def test_titulos_dos_tres_blocos(pagina):
    ausentes = [bloco for bloco in BLOCOS if bloco not in pagina]
    assert not ausentes, f'blocos ausentes: {ausentes}'


def test_opcoes_das_selecoes(pagina):
    ausentes = [opcao for opcao in OPCOES if opcao not in pagina]
    assert not ausentes, f'opções ausentes: {ausentes}'


def test_botao_enviar_solicitacao(pagina):
    assert 'Enviar solicitação' in pagina


def test_cabecalho_institucional_com_logotipo(client, html):
    assert 'usp-logo.png' in html
    assert 'Universidade de São Paulo' in html
    correspondencia = re.search(r'src\s*=\s*["\']([^"\']*usp-logo[^"\']*)["\']', html)
    caminho = correspondencia.group(1) if correspondencia else '/assets/usp-logo.png'
    if not caminho.startswith('/'):
        caminho = '/' + caminho
    assert client.get(caminho).status_code == 200


def test_placeholders_sao_exemplos_e_nao_rotulos(pagina):
    valores = re.findall(r'placeholder"?\s*[=:]\s*"([^"]*)"', pagina)
    valores += re.findall(r"placeholder'?\s*[=:]\s*'([^']*)'", pagina)
    assert len(valores) >= 25, 'todo campo precisa de um placeholder com exemplo'
    rotulos = {rotulo.casefold() for rotulo in ROTULOS}
    for valor in valores:
        assert valor.strip()
        assert valor.strip().casefold() not in rotulos


def test_titulo_da_confirmacao(pagina):
    assert 'Solicitação registrada' in pagina


def test_oficio_preserva_quebras_de_linha(pagina, css):
    assert 'pre-line' in css or 'pre-wrap' in css or '<pre' in pagina


def test_cores_da_identidade_usp(css):
    ausentes = [
        cor for cor in ('#1094ab', '#64c4d2', '#fcb421') if cor not in css.lower()
    ]
    assert not ausentes, f'cores ausentes: {ausentes}'


def test_fonte_sem_serifa(css):
    assert 'Open Sans' in css or 'sans-serif' in css.lower()


def test_campos_distribuidos_em_colunas(css):
    baixo = css.lower()
    assert any(
        marcador in baixo
        for marcador in ('grid', 'flex', 'inline-block', 'column')
    )


def test_sem_recursos_externos(html, css):
    for texto in (html, css):
        assert not re.search(r'(?:src|href)\s*=\s*["\']https?://', texto)
        assert '@import' not in texto
        assert 'url(http' not in texto.replace(' ', '').replace('\t', '')


def test_brasao_nao_aparece_na_pagina(pagina):
    baixo = pagina.casefold()
    assert 'brasao' not in baixo
    assert 'brasão' not in baixo
