from html.parser import HTMLParser

BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

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

ROTULOS_SOMENTE_DA_ABA_ALUNOS = [
    'NÍVEL',
    'TIPO DE AUXÍLIO',
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


class ColetorDeCampos(HTMLParser):
    def __init__(self):
        super().__init__()
        self.campos = []
        self.selecoes = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('input', 'textarea'):
            self.campos.append(dict(attrs))
        elif tag == 'select':
            self.selecoes += 1


def test_abas_e_blocos_na_pagina(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 200
    html = resposta.text
    assert html.index('ALUNOS') < html.index('DOCENTES')
    for bloco in BLOCOS:
        assert html.count(bloco) >= 2, bloco
    assert html.count('Enviar solicitação') >= 2


def test_rotulos_presentes_nas_duas_abas(cliente):
    html = cliente.get('/').text
    for rotulo in ROTULOS_COMUNS:
        assert html.count(rotulo) >= 2, rotulo
    for rotulo in ROTULOS_SOMENTE_DA_ABA_ALUNOS:
        assert html.count(rotulo) == 1, rotulo


def test_opcoes_das_selecoes(cliente):
    html = cliente.get('/').text
    for opcao in OPCOES:
        assert opcao in html, opcao


def test_todo_campo_tem_placeholder_de_exemplo(cliente):
    html = cliente.get('/').text
    coletor = ColetorDeCampos()
    coletor.feed(html)
    assert coletor.selecoes >= 4
    digitaveis = [
        campo
        for campo in coletor.campos
        if campo.get('type', 'text') in ('text', 'email', 'tel', 'number', 'search')
    ]
    assert len(digitaveis) >= 40
    rotulos = ROTULOS_COMUNS + ROTULOS_SOMENTE_DA_ABA_ALUNOS
    for campo in digitaveis:
        placeholder = (campo.get('placeholder') or '').strip()
        assert placeholder, f'campo sem placeholder: {campo}'
        for rotulo in rotulos:
            assert placeholder.lower() != rotulo.lower(), placeholder


def test_arquivos_estaticos_e_logotipo(cliente):
    html = cliente.get('/').text
    css = cliente.get('/style.css')
    js = cliente.get('/app.js')
    assert css.status_code == 200
    assert js.status_code == 200
    assert css.text.strip()
    assert js.text.strip()
    assert 'style.css' in html
    assert 'app.js' in html
    assert 'usp-logo.png' in html
    assert cliente.get('/assets/usp-logo.png').status_code == 200


def test_identidade_usp_sem_recursos_externos(cliente):
    html = cliente.get('/').text.lower()
    css = cliente.get('/style.css').text.lower()
    js = cliente.get('/app.js').text.lower()
    assert '#1094ab' in css
    assert 'open sans' in css or 'sans-serif' in css
    for texto in (html, css, js):
        assert '@import' not in texto
        assert 'url(http' not in texto
    assert 'src="http' not in html
    assert 'href="http' not in html
    assert 'http://' not in js
    assert 'https://' not in js
