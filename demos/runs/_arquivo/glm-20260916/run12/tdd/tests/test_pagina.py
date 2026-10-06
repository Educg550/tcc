import re
from html.parser import HTMLParser

ROTULOS_EM_ORDEM = [
    'SOLICITANTE E EVENTO',
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
    'ENDEREÇO DO SOLICITANTE',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
    'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO',
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


def _elemento_com_texto(texto):
    return re.compile(r'>\s*' + re.escape(texto) + r'\s*<')


def _pagina(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers['content-type']
    return resposta.text


def test_abas_com_rotulos_exatos_alunos_antes_de_docentes(client):
    html = _pagina(client)
    alunos = _elemento_com_texto('ALUNOS').search(html)
    docentes = _elemento_com_texto('DOCENTES').search(html)
    assert alunos is not None
    assert docentes is not None
    assert alunos.start() < docentes.start()


def test_blocos_e_rotulos_exatos_nessa_ordem(client):
    html = _pagina(client)
    posicoes = []
    for rotulo in ROTULOS_EM_ORDEM:
        achou = _elemento_com_texto(rotulo).search(html)
        assert achou is not None, rotulo
        posicoes.append(achou.start())
    assert posicoes == sorted(posicoes)


def test_nivel_e_tipo_de_auxilio_so_na_aba_alunos(client):
    html = _pagina(client)
    assert len(_elemento_com_texto('NÍVEL').findall(html)) == 1
    assert len(_elemento_com_texto('TIPO DE AUXÍLIO').findall(html)) == 1


def test_opcoes_das_selecoes(client):
    html = _pagina(client)
    for opcao in OPCOES:
        assert _elemento_com_texto(opcao).search(html) is not None, opcao


def test_cada_aba_tem_seu_botao_enviar(client):
    html = _pagina(client)
    assert len(_elemento_com_texto('Enviar solicitação').findall(html)) == 2


def test_cabecalho_institucional_usp(client):
    html = _pagina(client)
    assert 'assets/usp-logo.png' in html
    assert 'Universidade de São Paulo' in html


def test_titulo_da_confirmacao(client):
    assert 'Solicitação registrada' in _pagina(client)


def test_brasao_nao_aparece(client):
    for caminho in ('/', '/style.css', '/app.js'):
        texto = client.get(caminho).text.lower()
        assert 'brasao' not in texto
        assert 'brasão' not in texto
        assert 'escudo' not in texto


def test_arquivos_do_frontend_e_do_logo_sao_servidos(client):
    for caminho, tipo in (
        ('/style.css', 'text/css'),
        ('/app.js', ''),
        ('/assets/usp-logo.png', 'image/'),
    ):
        resposta = client.get(caminho)
        assert resposta.status_code == 200, caminho
        if tipo:
            assert tipo in resposta.headers.get('content-type', ''), caminho
    html = _pagina(client)
    assert 'style.css' in html
    assert 'app.js' in html


def test_identidade_visual_usp_no_css(client):
    css = client.get('/style.css').text.lower()
    assert '#1094ab' in css
    assert '#64c4d2' in css
    assert '#fcb421' in css
    assert 'open sans' in css


def test_nada_vem_da_rede(client):
    html = _pagina(client)
    css = client.get('/style.css').text
    js = client.get('/app.js').text
    for texto in (html, css, js):
        assert 'http://' not in texto
        assert 'https://' not in texto
    assert '@import' not in css.lower()
    assert 'fonts.googleapis' not in (html + css + js).lower()


def test_frontend_conversa_com_o_backend(client):
    js = client.get('/app.js').text
    assert 'solicitacao' in js


class _ColetorDePlaceholders(HTMLParser):
    def __init__(self):
        super().__init__()
        self.valores = []

    def handle_starttag(self, tag, attrs):
        for nome, valor in attrs:
            if nome == 'placeholder' and valor is not None:
                self.valores.append(valor)


def test_todo_campo_tem_placeholder_que_nao_repete_o_rotulo(client):
    html = _pagina(client)
    coletor = _ColetorDePlaceholders()
    coletor.feed(html)
    assert len(coletor.valores) >= 48
    rotulos = {rotulo.casefold() for rotulo in ROTULOS_EM_ORDEM}
    for placeholder in coletor.valores:
        assert placeholder.strip(), 'placeholder vazio'
        assert placeholder.strip().casefold() not in rotulos, placeholder
