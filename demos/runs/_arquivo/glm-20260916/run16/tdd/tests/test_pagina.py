from html.parser import HTMLParser

BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDEREÇO DO SOLICITANTE',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS_CAMPOS = [
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

SEM_ORDEM_CONFIÁVEL = ('NÚMERO', 'CIDADE', 'ESTADO')


class Coletor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.placeholders = []
        self.imagens = []
        self.urls = []

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        placeholder = atributos.get('placeholder')
        if placeholder and placeholder.strip():
            self.placeholders.append(placeholder)
        if tag == 'img':
            self.imagens.append(atributos.get('src') or '')
        for chave in ('src', 'href'):
            valor = atributos.get(chave)
            if valor:
                self.urls.append(valor)


def _coletar(html):
    coletor = Coletor()
    coletor.feed(html)
    return coletor


def test_pagina_abre_com_cabecalho_abas_blocos_e_rotulos_na_ordem(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    html = resposta.text
    assert 'universidade de são paulo' in html.lower()
    assert html.find('ALUNOS') != -1
    assert html.find('DOCENTES') != -1
    assert html.find('ALUNOS') < html.find('DOCENTES')
    pos_blocos = [html.find(bloco) for bloco in BLOCOS]
    assert -1 not in pos_blocos
    assert pos_blocos == sorted(pos_blocos)
    for rotulo in ROTULOS_CAMPOS:
        assert rotulo in html
    pos_rotulos = [html.find(rotulo) for rotulo in ROTULOS_CAMPOS
                   if rotulo not in SEM_ORDEM_CONFIÁVEL]
    assert pos_rotulos == sorted(pos_rotulos)
    for opcao in OPCOES:
        assert opcao in html
    assert html.count('Enviar solicitação') >= 2


def test_todo_campo_de_texto_tem_placeholder_de_exemplo(client):
    html = client.get('/').text
    placeholders = [p.strip() for p in _coletar(html).placeholders if p.strip()]
    assert len(placeholders) >= 25
    rotulos = {rotulo.lower() for rotulo in ROTULOS_CAMPOS}
    for placeholder in placeholders:
        assert placeholder.lower() not in rotulos


def test_cabecalho_usp_com_logo_sem_brasao_e_sem_recursos_externos(client):
    html = client.get('/').text
    coletor = _coletar(html)
    assert coletor.imagens
    for imagem in coletor.imagens:
        assert imagem.endswith('usp-logo.png')
    pagina = html.lower()
    for proibido in ('brasao', 'brasão', 'escudo'):
        assert proibido not in pagina
    for url in coletor.urls:
        assert not url.lower().startswith(('http://', 'https://'))
    assert client.get('/' + coletor.imagens[0].lstrip('/')).status_code == 200


def test_css_e_js_servidos_localmente_e_com_identidade_usp(client):
    html = client.get('/').text
    urls = _coletar(html).urls
    caminho_css = next(url for url in urls if url.split('?')[0].endswith('.css'))
    caminho_js = next(url for url in urls if url.split('?')[0].endswith('.js'))
    resposta_css = client.get('/' + caminho_css.lstrip('/'))
    resposta_js = client.get('/' + caminho_js.lstrip('/'))
    assert resposta_css.status_code == 200
    assert resposta_js.status_code == 200
    estilo = resposta_css.text.lower()
    for cor in ('#1094ab', '#64c4d2', '#fcb421'):
        assert cor in estilo
    assert 'open sans' in estilo
    assert 'Solicitação registrada' in html + resposta_js.text
    javascript = resposta_js.text
    assert 'http://' not in javascript
    assert 'https://' not in javascript
    assert 'fetch(' in javascript or 'XMLHttpRequest' in javascript
