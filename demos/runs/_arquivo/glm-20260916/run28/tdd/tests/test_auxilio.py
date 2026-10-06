import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

RAIZ = Path(__file__).resolve().parents[1]

ROTAS_POST = [
    rota.path for rota in app.routes if 'POST' in getattr(rota, 'methods', set())
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

MENSAGENS = [
    'Preencha todos os campos',
    'N. USP deve conter apenas números',
    'Número da agência deve conter apenas números',
    'Valor solicitado deve ser maior que 0',
    'E-mail inválido',
    'CPF deve estar no formato 000.000.000-00',
    'CEP deve estar no formato 00000-000',
    'Data de nascimento deve estar no formato dd/mm/aaaa',
    'CPF inválido',
    'Data de nascimento inválida',
]

DADOS_ALUNOS = {
    'NOME COMPLETO - SEM ABREVIAR': 'Maria da Silva',
    'N. USP': '12345678',
    'PROGRAMA': 'Ciência da Computação',
    'NÍVEL': 'Mestrado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'maria@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBES 2025',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': '1 a 5 de setembro de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'Porto Alegre',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'RS',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbes.org.br/2025',
    'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Passagem aérea e inscrição no evento.',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NÚMERO': '181',
    'COMPLEMENTO': 'Bloco C',
    'BAIRRO': 'Butantã',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '0001',
    'NÚMERO DA CONTA': '12345-6',
}

DADOS_DOCENTES = {
    campo: valor
    for campo, valor in DADOS_ALUNOS.items()
    if campo
    not in (
        'NÍVEL',
        'TIPO DE AUXÍLIO',
        'LINK DO EVENTO, EXAME OU DEFESA',
        'COMPLEMENTO',
    )
}


def obter(caminho):
    resposta = client.get(caminho)
    assert resposta.status_code == 200, f'GET {caminho} -> {resposta.status_code}'
    return resposta


def buscar_texto(caminho):
    return obter(caminho).content.decode('utf-8')


def pagina():
    return buscar_texto('/')


def tela():
    html = pagina()
    scripts = re.findall(r'src=["\']([^"\']+\.js)', html, re.I)
    return html + ''.join(buscar_texto('/' + s.lstrip('/')) for s in scripts)


def css_da_pagina():
    html = pagina()
    folhas = re.findall(r'href=["\']([^"\']+\.css)', html, re.I)
    assert folhas, 'a página não referencia folha de estilo'
    return '\n'.join(buscar_texto('/' + f.lstrip('/')) for f in folhas)


def texto_da_raiz(nome):
    caminho = RAIZ / nome
    assert caminho.exists(), f'{nome} não existe na raiz do projeto'
    return caminho.read_text(encoding='utf-8')


def textos_do_projeto():
    partes = []
    for padrao in ('*.py', '*.html', '*.js', '*.css'):
        for caminho in sorted(RAIZ.glob(padrao)):
            partes.append(caminho.read_text(encoding='utf-8', errors='replace'))
    return '\n'.join(partes)


def postar(dados, aba):
    corpo = dict(dados)
    corpo['aba'] = aba
    respostas = []
    for rota in ROTAS_POST:
        for kwargs in ({'': corpo}, {'data': corpo}):
            resposta = client.post(rota, **kwargs)
            if resposta.status_code in (200, 201, 400):
                respostas.append(resposta.text)
                break
    assert respostas, f'nenhuma rota POST aceitou a solicitação: {ROTAS_POST}'
    return '\n'.join(respostas)


def test_pagina_responde_com_html():
    resposta = obter('/')
    assert 'text/html' in resposta.headers['content-type']


def test_backend_tem_rota_post_para_a_solicitacao():
    assert ROTAS_POST, 'o app não registra nenhuma rota POST'


def test_abas_rotuladas_e_nessa_ordem():
    conteudo = tela()
    assert 'ALUNOS' in conteudo
    assert 'DOCENTES' in conteudo
    assert conteudo.index('ALUNOS') < conteudo.index('DOCENTES')


def test_cabecalho_institucional():
    html = pagina()
    assert 'Universidade de São Paulo' in html
    assert 'usp-logo.png' in html


def test_rotulos_dos_campos():
    conteudo = tela()
    for rotulo in ROTULOS:
        assert rotulo in conteudo, rotulo


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos():
    conteudo = tela()
    assert conteudo.count('NÍVEL') == 1
    assert conteudo.count('TIPO DE AUXÍLIO') == 1


def test_titulos_dos_blocos():
    conteudo = tela()
    for bloco in BLOCOS:
        assert bloco in conteudo, bloco


def test_opcoes_das_selecoes():
    conteudo = tela()
    for opcao in OPCOES:
        assert opcao in conteudo, opcao


def test_um_botao_enviar_por_aba():
    conteudo = tela()
    assert conteudo.count('Enviar solicitação') >= 2


def test_placeholders_exemplificam_em_vez_de_repetir_rotulo():
    conteudo = tela()
    placeholders = re.findall(r'placeholder=["\']([^"\']*)["\']', conteudo)
    assert len(placeholders) >= 25
    for placeholder in placeholders:
        assert placeholder not in ROTULOS


def test_arquivos_do_frontend_existem():
    for nome in ('index.html', 'style.css', 'app.js'):
        texto_da_raiz(nome)


def test_estaticos_ficam_servidos():
    html = pagina()
    alvos = [r for r in re.findall(r'(?:href|src)=["\']([^"\']+)', html, re.I) if r.endswith(('.css', '.js'))]
    alvos += re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    assert any(r.endswith('.css') for r in alvos)
    assert any(r.endswith('.js') for r in alvos)
    assert any(r.endswith('.png') for r in alvos)
    for ref in alvos:
        obter('/' + ref.lstrip('/'))


def test_o_logotipo_e_a_unica_imagem_da_pagina():
    html = texto_da_raiz('index.html')
    imagens = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    assert imagens
    for src in imagens:
        assert 'usp-logo' in src
    assert not re.search(r'bras[ãa]', html, re.I)


def test_css_usa_as_cores_da_usp():
    css = css_da_pagina().lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in css, cor


def test_css_usa_open_sans_com_fallback_sem_serifa():
    css = css_da_pagina()
    assert 'Open Sans' in css
    assert 'sans-serif' in css


def test_nenhum_recurso_externo():
    for nome in ('index.html', 'style.css', 'app.js'):
        texto = texto_da_raiz(nome).lower()
        for padrao in (
            'src="http',
            "src='http",
            'href="http',
            "href='http",
            '@import',
            'url(http',
            "url('http",
            'url("http',
            'src="//',
            'href="//',
        ):
            assert padrao not in texto, (nome, padrao)


def test_textos_do_oficio_estao_no_projeto():
    projeto = textos_do_projeto()
    for fragmento in (
        'Solicitação registrada',
        'Interessada(o):',
        'Assunto: Solicitação de Auxílio Financeiro',
        'Verba do programa',
        'aprovou na data de hoje',
        'Dados do evento',
        'Endereço da(o) interessada(o)',
        'Dados para pagamento',
        'Apresentação de trabalho:',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ):
        assert fragmento in projeto, fragmento


def test_mensagens_de_erro_estao_no_projeto():
    projeto = textos_do_projeto()
    for mensagem in MENSAGENS:
        assert mensagem in projeto, mensagem


def test_envio_valido_na_aba_alunos_gera_oficio():
    corpo = postar(DADOS_ALUNOS, 'ALUNOS')
    assert 'Interessada(o): Maria da Silva - 12345678' in corpo
    assert 'E-mail: maria@usp.br' in corpo
    assert 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento' in corpo
    assert 'Programa: Ciência da Computação - Mestrado' in corpo
    assert 'A CCP-Ciência da Computação aprovou na data de hoje' in corpo
    assert 'Evento: SBES 2025' in corpo
    assert 'Período: 1 a 5 de setembro de 2025' in corpo
    assert 'Local: Porto Alegre - RS - Brasil' in corpo
    assert 'Link do evento: https://sbes.org.br/2025' in corpo
    assert 'Apresentação de trabalho: Pôster' in corpo
    assert 'Valor solicitado: R$ 1.500,00' in corpo
    assert 'Detalhamento: Passagem aérea e inscrição no evento.' in corpo
    assert 'Rua do Anfiteatro, 181' in corpo
    assert 'Complemento: Bloco C' in corpo
    assert 'CEP: 05508-090' in corpo
    assert 'Butantã, São Paulo - SP' in corpo
    assert 'Data de nascimento: 01/02/1980' in corpo
    assert 'CPF: 123.456.789-09' in corpo
    assert 'RG / RNM: 12.345.678-9' in corpo
    assert 'Banco: Banco do Brasil' in corpo
    assert 'Agência: 0001' in corpo
    assert 'Conta: 12345-6' in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo
    assert '<<' not in corpo


def test_envio_valido_na_aba_docentes_gera_oficio():
    corpo = postar(DADOS_DOCENTES, 'DOCENTES')
    assert 'Interessada(o): Maria da Silva - 12345678' in corpo
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in corpo
    assert 'Programa: Ciência da Computação' in corpo
    assert 'Programa: Ciência da Computação -' not in corpo
    assert 'Mestrado' not in corpo
    assert 'Link do evento:' not in corpo
    assert 'Complemento:' not in corpo
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in corpo


def test_campos_obrigatorios_vazios():
    vazios = {campo: '' for campo in DADOS_ALUNOS}
    corpo = postar(vazios, 'ALUNOS')
    assert 'Preencha todos os campos' in corpo
    assert 'Interessada(o):' not in corpo


@pytest.mark.parametrize(
    ('campo', 'valor', 'mensagem'),
    [
        ('N. USP', '12a45', 'N. USP deve conter apenas números'),
        ('NÚMERO DA AGÊNCIA', '12b', 'Número da agência deve conter apenas números'),
        ('VALOR SOLICITADO (R$)', '0', 'Valor solicitado deve ser maior que 0'),
        ('E-MAIL', 'maria.usp.br', 'E-mail inválido'),
        (
            'CPF (SEPARADOS POR PONTOS E TRAÇO)',
            '123.456.789-0a',
            'CPF deve estar no formato 000.000.000-00',
        ),
        ('CEP', '0550809', 'CEP deve estar no formato 00000-000'),
        (
            'DATA DE NASCIMENTO',
            '1980',
            'Data de nascimento deve estar no formato dd/mm/aaaa',
        ),
        ('CPF (SEPARADOS POR PONTOS E TRAÇO)', '123.456.789-00', 'CPF inválido'),
        ('DATA DE NASCIMENTO', '31/02/2000', 'Data de nascimento inválida'),
    ],
)
def test_violacoes_geram_as_mensagens_do_requisito(campo, valor, mensagem):
    corpo = postar(dict(DADOS_ALUNOS, **{campo: valor}), 'ALUNOS')
    assert mensagem in corpo
    assert 'Interessada(o):' not in corpo


def test_todas_as_mensagens_aplicaveis_aparecem_juntas():
    corpo = postar(
        dict(
            DADOS_ALUNOS,
            **{
                'N. USP': '12a45',
                'NÚMERO DA AGÊNCIA': '12b',
                'VALOR SOLICITADO (R$)': '0',
                'E-MAIL': 'maria.usp.br',
                'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-00',
                'CEP': '0550809',
                'DATA DE NASCIMENTO': '1980',
            },
        ),
        'ALUNOS',
    )
    for mensagem in (
        'N. USP deve conter apenas números',
        'Número da agência deve conter apenas números',
        'Valor solicitado deve ser maior que 0',
        'E-mail inválido',
        'CPF deve estar no formato 000.000.000-00',
        'CEP deve estar no formato 00000-000',
        'Data de nascimento deve estar no formato dd/mm/aaaa',
    ):
        assert mensagem in corpo
