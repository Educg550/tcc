import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app import app

CLIENTE = TestClient(app)

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


def baixar(caminho):
    for prefixo in ('', '/static'):
        resposta = CLIENTE.get(prefixo + caminho)
        if resposta.status_code == 200:
            return resposta
    raise AssertionError(não encontrado: ' + caminho)


def test_cabecalho_institucional():
    html = baixar('/').text
    assert 'Universidade de São Paulo' in html
    assert 'usp-logo.png' in html + baixar('/style.css').text


def test_logotipo_e_servido_como_estatico():
    assert baixar('/assets/usp-logo.png').content


def test_abas_alunos_e_docentes():
    html = baixar('/').text
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_blocos_de_campos_na_ordem():
    html = baixar('/').text
    titulos = ['SOLICITANTE E EVENTO', 'ENDEREÇO DO SOLICITANTE', 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO']
    for titulo in titulos:
        assert titulo in html
    assert html.index(titulos[0]) < html.index(titulos[1]) < html.index(titulos[2])


def test_rotulos_dos_campos():
    html = baixar('/').text
    for rotulo in ROTULOS:
        assert rotulo in html, rotulo


def test_botao_em_cada_aba():
    html = baixar('/').text
    assert html.count('Enviar solicitação') >= 2


def test_placeholders_de_exemplo():
    html = baixar('/').text
    placeholders = re.findall(r'''placeholder=["']([^"']*)["']''', html, flags=re.IGNORECASE)
    assert len(placeholders) >= 20
    rotulos = {rotulo.upper() for rotulo in ROTULOS}
    for exemplo in placeholders:
        assert exemplo.strip()
        assert exemplo.strip().upper() not in rotulos


def test_cores_da_universidade():
    css = baixar('/style.css').text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css


def test_sem_recursos_da_rede():
    html = baixar('/').text
    assert not re.search(r'''(src|href)\s*=\s*["']https?://''', html, flags=re.IGNORECASE)
    css = baixar('/style.css').text
    assert 'http://' not in css and 'https://' not in css


def test_javascript_da_pagina():
    assert baixar('/app.js').content


def test_tela_de_confirmacao():
    texto = baixar('/').text + baixar('/app.js').text
    assert 'Solicitação registrada' in texto
