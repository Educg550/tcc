"""Testes da aplicação de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app

client = TestClient(app)

TITULOS_DOS_BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS_SOLICITANTE_E_EVENTO = [
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

ROTULOS_ENDERECO = [
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
]

ROTULOS_PAGAMENTO = [
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

ROTULOS_ALUNOS = ROTULOS_SOLICITANTE_E_EVENTO + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO
ROTULOS_DOCENTES = [r for r in ROTULOS_ALUNOS if r not in ('NÍVEL', 'TIPO DE AUXÍLIO')]

VALORES = {
    'NOME COMPLETO - SEM ABREVIAR': 'Maria de Souza',
    'N. USP': '1234567',
    'PROGRAMA': 'Ciência da Computação',
    'NÍVEL': 'Mestrado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'maria@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBBD',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': '1 a 3 de outubro de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'São Paulo',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbbd.org.br/2025',
    'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Inscrição no evento e passagem aérea',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NÚMERO': '181',
    'COMPLEMENTO': 'Sala 222',
    'BAIRRO': 'Butantã',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '1234',
    'NÚMERO DA CONTA': '12345-6',
}

CASOS_DE_ERRO = [
    ('N. USP deve conter apenas números', {'N. USP': '12a4567'}),
    ('Número da agência deve conter apenas números', {'NÚMERO DA AGÊNCIA': '12a4'}),
    ('Valor solicitado deve ser maior que 0', {'VALOR SOLICITADO (R$)': 'R$ 0,00'}),
    ('E-mail inválido', {'E-MAIL': 'maria.usp.br'}),
    ('CPF deve estar no formato 000.000.000-00', {'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123456789'}),
    ('CPF inválido', {'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-00'}),
    ('CEP deve estar no formato 00000-000', {'CEP': '05508090'}),
    ('Data de nascimento deve estar no formato dd/mm/aaaa', {'DATA DE NASCIMENTO': '01021980'}),
    ('Data de nascimento inválida', {'DATA DE NASCIMENTO': '31/02/1980'}),
    ('Data de nascimento inválida', {'DATA DE NASCIMENTO': '01/13/1980'}),
]

LINHAS_COMUNS_DO_OFICIO = [
    'A CCP-Ciência da Computação aprovou na data de hoje, a solicitação de auxílio financeiro para a',
    'Dados do evento',
    'Evento: SBBD',
    'Período: 1 a 3 de outubro de 2025',
    'Local: São Paulo - SP - Brasil',
    'Link do evento: https://sbbd.org.br/2025',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Inscrição no evento e passagem aérea',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Sala 222',
    'CEP: 05508-090',
    'Butantã, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 12345-6',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]

LINHAS_DO_OFICIO_ALUNOS = [
    'Interessada(o): Maria de Souza - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    *LINHAS_COMUNS_DO_OFICIO,
]

LINHAS_DO_OFICIO_DOCENTES = [
    'Interessada(o): Maria de Souza - 1234567',
    'E-mail: maria@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
    'Programa: Ciência da Computação',
    *LINHAS_COMUNS_DO_OFICIO,
]


def _attr(texto, nome):
    m = re.search(re.escape(nome) + r'\s*=\s*["\']([^"\']*)["\']', texto)
    return m.group(1) if m else None


def _limpa(fatia):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', fatia)).strip()


def _texto(caminho):
    resp = client.get(caminho)
    assert resp.status_code == 200, caminho
    return resp.text


def _mapa_campos(html):
    """Rótulo do requisito -> nomes, tag, attrs e opções dos campos no HTML servido."""
    infos = {
        rotulo: {'nomes': [], 'tag': '', 'attrs': '', 'opcoes': [], 'valores': []}
        for rotulo in ROTULOS_ALUNOS
    }

    rotulo_por_id = {}
    for m in re.finditer(r'<label\b([^>]*)>(.*?)</label>', html, re.S):
        alvo, rotulo = _attr(m.group(1), 'for'), _limpa(m.group(2))
        if alvo and rotulo in infos:
            rotulo_por_id[alvo] = rotulo

    campos = []
    for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>', html):
        tag, attrs = m.group(1), m.group(2)
        nome = _attr(attrs, 'name') or _attr(attrs, 'id')
        if not nome:
            continue
        idv = _attr(attrs, 'id')
        rotulo = rotulo_por_id.get(idv, '') if idv else ''
        campos.append((m.start(), rotulo, nome, tag, attrs))

    rotulo_por_posicao = {}
    for rotulo in ROTULOS_ALUNOS:
        for m in re.finditer(re.escape(rotulo) + r'\s*<', html):
            seguintes = [c for c in campos if c[0] > m.start()]
            if seguintes:
                rotulo_por_posicao[seguintes[0][0]] = rotulo

    for posicao, rotulo_fixado, nome, tag, attrs in campos:
        rotulo = rotulo_fixado or rotulo_por_posicao.get(posicao, '')
        if not rotulo:
            continue
        info = infos[rotulo]
        if nome not in info['nomes']:
            info['nomes'].append(nome)
            info['tag'], info['attrs'] = tag, attrs

    for m in re.finditer(r'<select\b([^>]*)>(.*?)</select>', html, re.S):
        nome = _attr(m.group(1), 'name') or _attr(m.group(1), 'id')
        textos, valores = [], []
        for om in re.finditer(r'<option\b([^>]*)>(.*?)</option>', m.group(2), re.S):
            valor, texto = _attr(om.group(1), 'value'), _limpa(om.group(2))
            if valor == '' or (valor is None and not texto):
                continue
            if texto and texto not in textos:
                textos.append(texto)
            if valor and valor not in valores:
                valores.append(valor)
        for info in infos.values():
            if nome and nome in info['nomes'] and not info['opcoes']:
                info['opcoes'], info['valores'] = textos, valores
    return infos


def _dados(rotulos, mudancas=None, indice=0):
    mudancas = mudancas or {}
    infos = _mapa_campos(_texto('/'))
    faltando = [r for r in rotulos if not infos[r]['nomes']]
    assert not faltando, f'rótulos sem campo correspondente na página: {faltando}'
    dados = {}
    for rotulo in rotulos:
        info = infos[rotulo]
        nomes = info['nomes']
        nome = nomes[indice] if indice < len(nomes) else nomes[0]
        if rotulo in mudancas:
            dados[nome] = mudancas[rotulo]
        elif info['opcoes']:
            preferido = VALORES.get(rotulo)
            dados[nome] = preferido if preferido in info['opcoes'] else info['opcoes'][0]
        else:
            dados[nome] = VALORES.get(rotulo, '')
    return dados


def _endpoints_de_envio():
    urls = []
    for m in re.finditer(r'fetch\(\s*["\'`]([^"\'`]+)', _texto('/app.js')):
        url = m.group(1).split('?')[0]
        while url.startswith('./'):
            url = url[2:]
        if not url.startswith('/'):
            url = '/' + url
        if url not in urls:
            urls.append(url)
    assert urls, 'nenhuma URL de fetch encontrada em app.js'
    return urls


def _enviar(dados, indice=0):
    urls = _endpoints_de_envio()
    url = urls[indice] if indice < len(urls) else urls[0]
    resp = client.post(url, =dados)
    if resp.status_code == 405:
        resp = client.put(url, =dados)
    return resp


def _texto_da_resposta(resp):
    assert resp.status_code < 500, (resp.status_code, resp.text)
    return resp.text


def test_arquivos_do_frontend_e_do_logo_servidos():
    assert client.get('/').status_code == 200
    assert client.get('/style.css').status_code == 200
    assert client.get('/app.js').status_code == 200
    logo = client.get('/assets/usp-logo.png')
    assert logo.status_code == 200
    assert logo.headers['content-type'].startswith('image/')


def test_cabecalho_institucional_com_logo_e_nome_da_universidade():
    html = _texto('/')
    assert 'assets/usp-logo.png' in html
    assert 'Universidade de São Paulo' in html


def test_abas_alunos_e_docentes_nessa_ordem():
    html = _texto('/')
    assert 'ALUNOS' in html
    assert 'DOCENTES' in html
    assert html.index('ALUNOS') < html.index('DOCENTES')


def test_titulos_dos_tres_blocos_visiveis():
    html = _texto('/')
    for titulo in TITULOS_DOS_BLOCOS:
        assert titulo in html


def test_rotulos_da_aba_alunos_presentes_e_na_ordem():
    html = _texto('/')
    posicoes = []
    for rotulo in ROTULOS_ALUNOS:
        m = re.search(re.escape(rotulo) + r'\s*<', html)
        assert m, f'rótulo ausente na página: {rotulo}'
        posicoes.append(m.start())
    assert posicoes == sorted(posicoes)


def test_campos_repetidos_para_a_aba_docentes():
    html = _texto('/')
    for rotulo in ROTULOS_DOCENTES:
        encontrados = re.findall(re.escape(rotulo) + r'\s*<', html)
        assert len(encontrados) >= 2, rotulo


def test_botao_enviar_solicitacao_em_cada_aba():
    assert _texto('/').count('Enviar solicitação') >= 2


def test_titulo_da_confirmacao():
    servido = _texto('/') + _texto('/app.js')
    assert 'Solicitação registrada' in servido


def test_selecoes_com_as_opcoes_do_requisito():
    mapa = _mapa_campos(_texto('/'))
    esperado = {
        'NÍVEL': ['Mestrado', 'Doutorado'],
        'TIPO DE AUXÍLIO': ['Participação em evento', 'Banca de exame ou defesa', 'Outro'],
        'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': [
            'Pôster',
            'Apresentação oral',
            'Outra',
            'Não irá apresentar trabalho',
        ],
    }
    for rotulo, opcoes in esperado.items():
        info = mapa[rotulo]
        assert info['tag'] == 'select', rotulo
        for opcao in opcoes:
            assert opcao in info['opcoes'] + info['valores'], (rotulo, opcao)


def test_placeholders_com_exemplos_em_vez_do_rotulo():
    mapa = _mapa_campos(_texto('/'))
    for rotulo in ROTULOS_ALUNOS:
        info = mapa[rotulo]
        if info['tag'] == 'select':
            continue
        exemplo = _attr(info['attrs'], 'placeholder')
        assert exemplo is not None, rotulo
        assert exemplo.strip(), rotulo
        assert exemplo.strip().upper() != rotulo.upper(), rotulo


def test_identidade_visual_usp_no_css():
    css = _texto('/style.css').lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css, cor
    assert 'open sans' in css or 'sans-serif' in css


def test_nenhum_brasao_e_nenhum_recurso_remoto():
    html = _texto('/')
    css = _texto('/style.css')
    imgs = re.findall(r'<img\b[^>]*>', html)
    srcs = [_attr(tag, 'src') or '' for tag in imgs]
    assert srcs, 'o logotipo da USP deve aparecer na página'
    assert all('usp-logo' in src for src in srcs)
    tudo = (html + css).lower()
    assert 'brasao' not in tudo and 'brasão' not in tudo
    for remoto in ('fonts.googleapis', 'fonts.gstatic', 'cdn.jsdelivr', 'unpkg.com', 'cdnjs.cloudflare.com'):
        assert remoto not in tudo


def test_oficio_da_aba_alunos_com_todos_os_dados():
    texto = _texto_da_resposta(_enviar(_dados(ROTULOS_ALUNOS)))
    for linha in LINHAS_DO_OFICIO_ALUNOS:
        assert linha in texto, linha


def test_oficio_da_aba_docentes_sem_nivel_e_sem_tipo_de_auxilio():
    texto = _texto_da_resposta(_enviar(_dados(ROTULOS_DOCENTES, indice=1), indice=1))
    for linha in LINHAS_DO_OFICIO_DOCENTES:
        assert linha in texto, linha


def test_oficio_omite_as_linhas_dos_opcionais_vazios():
    texto = _texto_da_resposta(
        _enviar(
            _dados(
                ROTULOS_ALUNOS,
                mudancas={'LINK DO EVENTO, EXAME OU DEFESA': '', 'COMPLEMENTO': ''},
            )
        )
    )
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto
    assert 'Evento: SBBD' in texto
    assert 'Rua do Anfiteatro, 181' in texto


@pytest.mark.parametrize(('mensagem', 'mudancas'), CASOS_DE_ERRO)
def test_validacao_reporta_a_mensagem_e_nao_gera_oficio(mensagem, mudancas):
    texto = _texto_da_resposta(_enviar(_dados(ROTULOS_ALUNOS, mudancas=mudancas)))
    assert mensagem in texto
    assert 'Interessada(o):' not in texto


def test_validacao_reporta_todas_as_mensagens_aplicaveis_de_uma_vez():
    mudancas = {
        'PROGRAMA': '',
        'N. USP': '12a4567',
        'NÚMERO DA AGÊNCIA': '12a4',
        'VALOR SOLICITADO (R$)': 'R$ 0,00',
        'E-MAIL': 'maria.usp.br',
        'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123456789',
        'CEP': '05508090',
        'DATA DE NASCIMENTO': '01021980',
    }
    texto = _texto_da_resposta(_enviar(_dados(ROTULOS_ALUNOS, mudancas=mudancas)))
    mensagens = [
        'Preencha todos os campos',
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF deve estar no formato 000.000.000-00',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento deve estar no formato dd/mm/aaaa',
    ]
    for mensagem in mensagens:
        assert mensagem in texto, mensagem
    assert texto.count('Preencha todos os campos') == 1
    assert 'Interessada(o):' not in texto
