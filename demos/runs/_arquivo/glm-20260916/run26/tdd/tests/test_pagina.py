from html.parser import HTMLParser

LABELS = [
    'ALUNOS',
    'DOCENTES',
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
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


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elementos = []

    def handle_starttag(self, tag, attrs):
        self.elementos.append((tag.lower(), {k.lower(): (v or '') for k, v in attrs}))


def _elementos(html):
    p = _Parser()
    p.feed(html)
    return p.elementos


def _absoluto(url):
    return url if url.startswith('/') else '/' + url


def _html(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'text/html' in r.headers.get('content-type', '')
    return r.text


def _recurso(client, attr, pista, padrao):
    for tag, attrs in _elementos(_html(client)):
        alvo = attrs.get(attr, '')
        if tag in ('link', 'script', 'img') and pista in alvo:
            r = client.get(_absoluto(alvo))
            if r.status_code == 200:
                return r
    r = client.get(padrao)
    assert r.status_code == 200, padrao + ' não está sendo servido'
    return r


def _css(client):
    return _recurso(client, 'href', '.css', '/style.css').text


def _js(client):
    return _recurso(client, 'src', '.js', '/app.js').text


def test_pagina_inicial_abre(client):
    _html(client)


def test_abas_alunos_e_docentes_nessa_ordem(client):
    html = _html(client).lower()
    assert 'alunos' in html
    assert 'docentes' in html
    assert html.index('alunos') < html.index('docentes')


def test_aba_alunos_esta_marcada_como_ativa(client):
    html = _html(client).lower()
    marcas = ('ativa', 'active', 'selected', 'current', 'show')
    inicio = 0
    achou = False
    while True:
        i = html.find('alunos', inicio)
        if i < 0:
            break
        janela = html[max(0, i - 300):i + 300]
        if any(m in janela for m in marcas):
            achou = True
            break
        inicio = i + 1
    assert achou, 'nenhuma marca de aba ativa junto do rótulo ALUNOS'


def test_todos_os_rotulos_exatos_estao_na_pagina(client):
    html = _html(client).lower()
    for rotulo in LABELS:
        assert rotulo.lower() in html, 'rótulo ausente: ' + rotulo


def test_nivel_e_tipo_de_auxilio_so_existem_na_aba_alunos(client):
    html = _html(client).lower()
    formas = []
    inicio = 0
    while True:
        i = html.find('<form', inicio)
        if i < 0:
            break
        formas.append(i)
        inicio = i + 1
    assert len(formas) >= 2
    docentes_html = html[formas[-1]:]
    assert 'nível' not in docentes_html
    assert 'tipo de auxílio' not in docentes_html


def test_opcoes_das_selecoes(client):
    html = _html(client).lower()
    for op in OPCOES:
        assert op.lower() in html, 'opção ausente: ' + op


def test_cada_aba_tem_o_botao_enviar_solicitacao(client):
    html = _html(client).lower()
    assert html.count('enviar solicitação') >= 2


def test_dois_formularios(client):
    html = _html(client).lower()
    total = 0
    inicio = 0
    while True:
        i = html.find('<form', inicio)
        if i < 0:
            break
        total += 1
        inicio = i + 1
    assert total >= 2


def test_todo_campo_tem_placeholder_de_exemplo(client):
    rotulos = {r.lower() for r in LABELS}
    campos = 0
    for tag, attrs in _elementos(_html(client)):
        if tag == 'input':
            if attrs.get('type', 'text').lower() in ('hidden', 'submit', 'button', 'checkbox', 'radio', 'image'):
                continue
        elif tag != 'textarea':
            continue
        ph = attrs.get('placeholder', '').strip()
        assert ph, 'campo sem placeholder'
        assert ph.lower() not in rotulos, 'placeholder repete o rótulo'
        campos += 1
    assert campos >= 40


def test_titulo_da_confirmacao_esta_no_frontend(client):
    assert 'solicitação registrada' in (_html(client) + _js(client)).lower()


def test_cabecalho_institucional_da_usp(client):
    html = _html(client).lower()
    assert 'universidade de são paulo' in html
    assert 'usp-logo' in html


def test_logotipo_da_usp_servido(client):
    r = _recurso(client, 'src', 'usp-logo', '/assets/usp-logo.png')
    assert len(r.content) > 0
    assert 'image' in r.headers.get('content-type', '')


def test_style_e_appjs_servidos(client):
    assert _css(client).strip()
    assert _js(client).strip()


def test_cores_da_identidade_usp_no_css(client):
    css = _css(client).lower()
    assert '#1094ab' in css
    assert '#64c4d2' in css
    assert '#fcb421' in css


def test_fonte_sem_serifa(client):
    css = _css(client).lower()
    assert 'open sans' in css or 'sans-serif' in css


def test_nenhum_recurso_vem_da_rede(client):
    for tag, attrs in _elementos(_html(client)):
        if tag in ('link', 'script', 'img', 'source'):
            for attr in ('href', 'src'):
                alvo = attrs.get(attr, '')
                assert not alvo.startswith(('http://', 'https://', '//')), 'recurso externo: ' + alvo
    css = _css(client).lower()
    js = _js(client).lower()
    assert 'http://' not in css and 'https://' not in css
    assert 'http://' not in js and 'https://' not in js
