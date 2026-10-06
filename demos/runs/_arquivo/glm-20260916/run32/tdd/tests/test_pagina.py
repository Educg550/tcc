from html.parser import HTMLParser

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


class LeitorDePagina(HTMLParser):
    def __init__(self):
        super().__init__()
        self.campos = []
        self.recursos_remotos = []

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag in ('input', 'textarea'):
            self.campos.append(atributos)
        if tag != 'a':
            for atributo in ('src', 'href'):
                valor = atributos.get(atributo) or ''
                if valor.startswith(('http://', 'https://')):
                    self.recursos_remotos.append(valor)


def _pagina(arquivo_estatico):
    return arquivo_estatico('/', '/index.html').text


def _tudo(arquivo_estatico):
    return _pagina(arquivo_estatico) + arquivo_estatico('/app.js', '/static/app.js').text


def test_abas_e_formularios(arquivo_estatico):
    tudo = _tudo(arquivo_estatico)
    assert tudo.index('ALUNOS') < tudo.index('DOCENTES')
    assert 'Enviar solicitação' in tudo
    for bloco in (
        'SOLICITANTE E EVENTO',
        'ENDEREÇO DO SOLICITANTE',
        'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
    ):
        assert bloco in tudo
    for rotulo in ROTULOS:
        assert rotulo in tudo
    for opcao in OPCOES:
        assert opcao in tudo


def test_cabecalho_institucional(arquivo_estatico):
    pagina = _pagina(arquivo_estatico)
    assert 'Universidade de São Paulo' in pagina
    assert 'usp-logo.png' in pagina


def test_tela_de_confirmacao(arquivo_estatico):
    assert 'Solicitação registrada' in _tudo(arquivo_estatico)


def test_estaticos_servidos(arquivo_estatico):
    assert arquivo_estatico('/app.js', '/static/app.js').status_code == 200
    assert arquivo_estatico('/style.css', '/static/style.css').status_code == 200
    logotipo = arquivo_estatico('/assets/usp-logo.png', '/static/assets/usp-logo.png')
    assert logotipo.headers['content-type'].startswith('image/')


def test_estilo_usa_identidade_da_usp(arquivo_estatico):
    estilo = arquivo_estatico('/style.css', '/static/style.css').text
    assert '#1094ab' in estilo
    assert 'sans-serif' in estilo


def test_pagina_nao_baixa_nada_da_rede(arquivo_estatico):
    leitor = LeitorDePagina()
    leitor.feed(_pagina(arquivo_estatico))
    estilo = arquivo_estatico('/style.css', '/static/style.css').text
    assert leitor.recursos_remotos == []
    assert 'http://' not in estilo
    assert 'https://' not in estilo


def test_todo_campo_tem_placeholder(arquivo_estatico):
    leitor = LeitorDePagina()
    leitor.feed(_pagina(arquivo_estatico))
    assert len(leitor.campos) >= 25
    for campo in leitor.campos:
        exemplo = campo.get('placeholder')
        assert exemplo, campo
        assert exemplo not in ROTULOS
