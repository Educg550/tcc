import re

import pytest

TITULOS_DE_BLOCO = [
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


@pytest.fixture(scope='session')
def pagina(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')
    return resposta.text


def test_pagina_responde_na_raiz(client):
    assert client.get('/').status_code == 200


def test_abas_alunos_e_docentes_nessa_ordem(pagina):
    assert pagina.index('ALUNOS') < pagina.index('DOCENTES')


@pytest.mark.parametrize('titulo', TITULOS_DE_BLOCO)
def test_titulo_de_bloco_visivel(pagina, titulo):
    assert titulo in pagina


@pytest.mark.parametrize('rotulo', ROTULOS)
def test_rotulo_de_campo_visivel(pagina, rotulo):
    assert rotulo in pagina


@pytest.mark.parametrize('opcao', OPCOES)
def test_opcao_de_selecao_visivel(pagina, opcao):
    assert opcao in pagina


def test_botao_de_envio_em_cada_aba(pagina):
    assert pagina.count('Enviar solicitação') >= 2


def test_cabecalho_institucional(pagina):
    assert 'Universidade de São Paulo' in pagina
    assert 'assets/usp-logo.png' in pagina


def test_pagina_referencia_style_e_app(pagina):
    assert 'style.css' in pagina
    assert 'app.js' in pagina


def test_todo_campo_tem_placeholder(pagina):
    campos = re.findall(r'<(?:input|textarea)\b[^>]*>', pagina)
    assert campos
    for campo in campos:
        assert 'placeholder' in campo, campo


def test_nenhum_recurso_remoto(pagina):
    urls = re.findall(r'''(?:href|src)=["']([^"']+)["']''', pagina)
    remotos = [url for url in urls if url.startswith(('http://', 'https://', '//'))]
    assert remotos == []


def test_arquivos_referenciados_sao_servidos(client, pagina):
    urls = re.findall(r'''(?:href|src)=["']([^"']+)["']''', pagina)
    locais = [
        url for url in urls
        if not url.startswith(('http://', 'https://', '//', 'data:', '#', 'mailto:'))
    ]
    assert locais
    for url in locais:
        assert client.get(url).status_code == 200, url


def test_titulo_da_confirmacao_esta_no_frontend(client, pagina):
    textos = pagina
    for url in re.findall(r'''src=["']([^"']+)["']''', pagina):
        if url.endswith('.js'):
            resposta = client.get(url)
            if resposta.status_code == 200:
                textos += resposta.text
    assert 'Solicitação registrada' in textos
