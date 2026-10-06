'''Testes do formulario de solicitacao de auxilio financeiro da Pos-Graduacao do IME-USP.

Os testes exercitam a aplicacao como o navegador faz: leem a pagina servida na
raiz e enviam a solicitacao pelo mesmo caminho que o app.js usa. Os nomes dos
campos e a rota de envio sao descobertos do que a aplicacao serve, porque o
requisito fixa rotulos, mensagens e comportamento - nao a implementacao.
'''

import re
import unicodedata
from html import unescape
from html.parser import HTMLParser

import pytest
from fastapi.testclient import TestClient

from app import app


BLOCOS = [
    'SOLICITANTE E EVENTO',
    'ENDERECO DO SOLICITANTE',
    'INFORMACOES PARA PAGAMENTO / REEMBOLSO',
]

ROTULOS_SOLICITANTE = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'NIVEL',
    'TIPO DE AUXILIO',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERIODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAIS DO EVENTO, EXAME OU DEFESA',
    'LINK DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRA APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
]

ROTULOS_ENDERECO = [
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NUMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
]

ROTULOS_PAGAMENTO = [
    'CPF (SEPARADOS POR PONTOS E TRACO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRACO)',
    'NOME DO BANCO',
    'NUMERO DA AGENCIA',
    'NUMERO DA CONTA',
]

ROTULOS_TODOS = ROTULOS_SOLICITANTE + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO

OPCOES_ESPERADAS = [
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

MENSAGENS_FORMATO = [
    'Preencha todos os campos',
    'N. USP deve conter apenas números',
    'Número da agência deve conter apenas números',
    'Valor solicitado deve ser maior que 0',
    'E-mail inválido',
    'CPF deve estar no formato 000.000.000-00',
    'CEP deve estar no formato 00000-000',
    'Data de nascimento deve estar no formato dd/mm/aaaa',
]

LINHA_OFICIO = 'Encaminhe-se ao Serviço Financeiro para providências.'

DADOS_ALUNOS = {
    'NOME COMPLETO - SEM ABREVIAR': 'Maria Souza da Silva',
    'N. USP': '1234567',
    'PROGRAMA': 'Ciência da Computação',
    'NIVEL': 'Mestrado',
    'TIPO DE AUXILIO': 'Participação em evento',
    'E-MAIL': 'maria.souza@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBMF 2025',
    'PERIODO DO EVENTO, EXAME OU DEFESA': '22 a 26 de setembro de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'Recife',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'PE',
    'PAIS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbfm.org.br/sbmf2025',
    'VALOR SOLICITADO (R$)': 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Passagem aérea e inscrição no evento.',
    'IRA APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NUMERO': '123',
    'COMPLEMENTO': 'Sala 214',
    'BAIRRO': 'Cidade Universitária',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRACO)': '123.456.789-09',
    'RG / RNM (SEPARADOS POR PONTOS E TRACO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NUMERO DA AGENCIA': '0183',
    'NUMERO DA CONTA': '45678-9',
}

DADOS_DOCENTES = {
    'NOME COMPLETO - SEM ABREVIAR': 'Pedro Alves do Nascimento',
    'N. USP': '7654321',
    'PROGRAMA': 'Estatística',
    'E-MAIL': 'pedro.nascimento@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'Defesa de mestrado de Ana Lima',
    'PERIODO DO EVENTO, EXAME OU DEFESA': '10 de outubro de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'São Paulo',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'SP',
    'PAIS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': '',
    'VALOR SOLICITADO (R$)': 'R$ 2.000,00',
    'DETALHAMENTO DO PEDIDO': 'Diária para participação em banca de defesa.',
    'IRA APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Não irá apresentar trabalho',
    'DATA DE NASCIMENTO': '03/12/1975',
    'LOGRADOURO': 'Avenida Professor Lineu Prestes',
    'NUMERO': '65',
    'COMPLEMENTO': '',
    'BAIRRO': 'Butantã',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRACO)': '987.654.321-00',
    'RG / RNM (SEPARADOS POR PONTOS E TRACO)': '23.456.789-0',
    'NOME DO BANCO': 'Caixa Econômica Federal',
    'NUMERO DA AGENCIA': '0001',
    'NUMERO DA CONTA': '12345-6',
}

BRUTOS = {
    'DATA DE NASCIMENTO': '03121975',
    'CEP': '05508090',
    'CPF (SEPARADOS POR PONTOS E TRACO)': '98765432100',
}

LINHAS_ALUNOS = [
    'Interessada(o): Maria Souza da Silva - 1234567',
    'E-mail: maria.souza@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Mestrado',
    'Dados do evento',
    'Evento: SBMF 2025',
    'Período: 22 a 26 de setembro de 2025',
    'Local: Recife - PE - Brasil',
    'Link do evento: https://sbfm.org.br/sbmf2025',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 123',
    'Complemento: Sala 214',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 0183',
    'Conta: 45678-9',
    LINHA_OFICIO,
]

LINHAS_DOCENTES = [
    'Interessada(o): Pedro Alves do Nascimento - 7654321',
    'E-mail: pedro.nascimento@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
    'Programa: Estatística',
    'Dados do evento',
    'Evento: Defesa de mestrado de Ana Lima',
    'Período: 10 de outubro de 2025',
    'Local: São Paulo - SP - Brasil',
    'Apresentação de trabalho: Não irá apresentar trabalho',
    'Valor solicitado: R$ 2.000,00',
    'Detalhamento: Diária para participação em banca de defesa.',
    'Endereço da(o) interessada(o)',
    'Avenida Professor Lineu Prestes, 65',
    'CEP: 05508-090',
    'Butantã, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 03/12/1975',
    'CPF: 987.654.321-00',
    'RG / RNM: 23.456.789-0',
    'Banco: Caixa Econômica Federal',
    'Agência: 0001',
    'Conta: 12345-6',
    LINHA_OFICIO,
]

_CACHE = {}


def _norm(texto):
    return re.sub(r'\s+', ' ', texto or '').strip()


def _padrao_busca(texto):
    partes = r'\s+'.join(re.escape(p) for p in texto.split())
    if texto[:1].isalnum():
        partes = r'\b' + partes
    if texto[-1:].isalnum():
        partes = partes + r'\b'
    return partes


def _sem_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')


def _chaves_extras(rotulo):
    slug = re.sub(r'[^a-z0-9]+', '_', _sem_acentos(rotulo.lower())).strip('_')
    chaves = {slug, slug.replace('_', '')}
    chaves.add(re.sub(r'_([a-z])', lambda m: m.group(1).upper(), slug))
    if re.search(r'_[a-z]$', slug):
        chaves.add(re.sub(r'_[a-z]$', '', slug))
    return chaves


def _nome_campo(form, rotulo):
    alvo = _norm(rotulo)
    rotulos = form['rotulos']
    if alvo in rotulos:
        return rotulos[alvo]
    base = alvo.rstrip(':* ').strip()
    for texto, nome in rotulos.items():
        if texto.rstrip(':* ').strip() == base:
            return nome
    for texto, nome in rotulos.items():
        if base.lower() in texto.lower():
            return nome
    return None


class _Leitor(HTMLParser):
    '''Extrai formularios, rotulos, opcoes e referencias de recursos do HTML.'''

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self.pseudo = None
        self.idx_form = -1
        self.ids = {}
        self.pendentes = []
        self.pilha_labels = []
        self.radios = []
        self.hiddens = []
        self.recursos = []
        self.srcs_js = []
        self.hrefs_css = []
        self.sel_atual = None
        self.dentro_opcao = False
        self.texto_opcao = []
        self.valor_opcao = ''

    def _forma(self, idx):
        if isinstance(idx, int) and 0 <= idx < len(self.forms):
            return self.forms[idx]
        return self.pseudo

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {}
        for chave, valor in attrs:
            a.setdefault(chave.lower(), valor if valor is not None else '')
        if tag == 'form':
            self.forms.append({'rotulos': {}, 'nomes': {}, 'campos': [], 'opcoes': {}})
            self.idx_form = len(self.forms) - 1
        elif tag == 'label':
            self.pilha_labels.append(
                {'idx': self.idx_form, 'texto': [], 'for': a.get('for'),
                 'ligado': False, 'alvo': None})
        elif tag in ('input', 'select', 'textarea'):
            self._campo(tag, a)
        elif tag == 'option':
            self.dentro_opcao = True
            self.texto_opcao = []
            self.valor_opcao = a.get('value', '')
        elif tag == 'script':
            if a.get('src'):
                self.srcs_js.append(a['src'])
                self.recursos.append(('script', a['src']))
        elif tag == 'link':
            rel = (a.get('rel') or '').lower()
            if a.get('href') and any(p in rel for p in ('stylesheet', 'icon', 'preload', 'font', 'preconnect')):
                self.hrefs_css.append(a['href'])
                self.recursos.append(('link', a['href']))
        elif tag == 'img':
            if a.get('src'):
                self.recursos.append(('img', a['src']))

    def _campo(self, tag, a):
        nome = a.get('name') or a.get('id')
        tipo = (a.get('type') or '').lower()
        if tag == 'input' and tipo == 'hidden':
            self.hiddens.append({'name': nome, 'value': a.get('value', '')})
            return
        if tag == 'input' and tipo == 'radio':
            rotulo = _norm(''.join(self.pilha_labels[-1]['texto'])) if self.pilha_labels else ''
            self.radios.append({'name': nome, 'value': a.get('value', ''), 'id': a.get('id', ''),
                                'rotulo': rotulo, 'checked': 'checked' in a})
            return
        if tag == 'input' and tipo in ('submit', 'button', 'image', 'reset'):
            return
        if self.idx_form == -1:
            if self.pseudo is None:
                self.pseudo = {'rotulos': {}, 'nomes': {}, 'campos': [], 'opcoes': {}}
            alvo = self.pseudo
            idx = -1
        else:
            alvo = self.forms[self.idx_form]
            idx = self.idx_form
        campo = {'tag': tag, 'name': nome, 'tipo': tipo, 'attrs': a, 'form_idx': idx}
        alvo['campos'].append(campo)
        if nome:
            if a.get('id'):
                self.ids[a['id']] = nome
            if self.pilha_labels:
                texto = _norm(''.join(self.pilha_labels[-1]['texto']))
                if texto:
                    alvo['rotulos'].setdefault(texto, nome)
                    alvo['nomes'].setdefault(nome, texto)
                    self.pilha_labels[-1]['ligado'] = True
                    self.pilha_labels[-1]['alvo'] = nome
        if tag == 'select':
            self.sel_atual = campo

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'label' and self.pilha_labels:
            item = self.pilha_labels.pop()
            texto = _norm(''.join(item['texto']))
            if item['for']:
                if texto:
                    self.pendentes.append((item['idx'], texto, item['for']))
            elif not item['ligado'] and texto and item['alvo']:
                alvo = self._forma(item['idx'])
                if alvo is not None:
                    alvo['rotulos'].setdefault(texto, item['alvo'])
                    alvo['nomes'].setdefault(item['alvo'], texto)
        elif tag == 'select':
            self.sel_atual = None
        elif tag == 'option' and self.dentro_opcao:
            self.dentro_opcao = False
            texto = _norm(''.join(self.texto_opcao))
            if self.sel_atual is not None and self.sel_atual['name']:
                destino = self._forma(self.sel_atual['form_idx'])
                if destino is not None:
                    destino['opcoes'].setdefault(self.sel_atual['name'], []).append((texto, self.valor_opcao))

    def handle_data(self, data):
        if self.pilha_labels:
            self.pilha_labels[-1]['texto'].append(data)
        if self.dentro_opcao:
            self.texto_opcao.append(data)

    def finalizar(self):
        for idx, texto, for_id in self.pendentes:
            nome = self.ids.get(for_id)
            if not nome:
                continue
            alvo = self._forma(idx)
            if alvo is None:
                continue
            alvo['rotulos'].setdefault(texto, nome)
            alvo['nomes'].setdefault(nome, texto)
        if not self.forms and self.pseudo is not None:
            self.forms.append(self.pseudo)


def _carregar_pagina():
    if 'html' in _CACHE:
        return
    resp = TestClient(app, raise_server_exceptions=False).get('/')
    assert resp.status_code == 200, f'GET / respondeu {resp.status_code}'
    html = resp.text
    leitor = _Leitor()
    leitor.feed(html)
    leitor.finalizar()
    _CACHE['html'] = html
    _CACHE['leitor'] = leitor


def _html():
    _carregar_pagina()
    return _CACHE['html']


def _arquivo_estatico(nome, urls):
    client = TestClient(app, raise_server_exceptions=False)
    tentadas = []
    for url in urls:
        limpo = (url or '').split('?')[0]
        if limpo.endswith(nome):
            alvo = limpo if limpo.startswith('/') else '/' + limpo
            if alvo not in tentadas:
                tentadas.append(alvo)
    if '/' + nome not in tentadas:
        tentadas.append('/' + nome)
    for alvo in tentadas:
        resp = client.get(alvo)
        if resp.status_code == 200:
            return resp.text
    pytest.fail(f'o arquivo estatico {nome} nao foi servido pela aplicacao')


def _css():
    if 'css' not in _CACHE:
        _carregar_pagina()
        _CACHE['css'] = _arquivo_estatico('style.css', _CACHE['leitor'].hrefs_css)
    return _CACHE['css']


def _js():
    if 'js' not in _CACHE:
        _carregar_pagina()
        _CACHE['js'] = _arquivo_estatico('app.js', _CACHE['leitor'].srcs_js)
    return _CACHE['js']


def _formularios():
    if 'formularios' in _CACHE:
        return _CACHE['formularios']
    _carregar_pagina()
    alunos = None
    docentes = None
    for form in _CACHE['leitor'].forms:
        if _nome_campo(form, 'NIVEL') and _nome_campo(form, 'CPF (SEPARADOS POR PONTOS E TRACO)'):
            alunos = form
        elif _nome_campo(form, 'CPF (SEPARADOS POR PONTOS E TRACO)'):
            docentes = docentes or form
    if alunos is None or docentes is None:
        pytest.fail('a pagina nao traz os dois formularios distintos (ALUNOS e DOCENTES)')
    _CACHE['formularios'] = {'alunos': alunos, 'docentes': docentes}
    return _CACHE['formularios']


def _achatar(objeto):
    if isinstance(objeto, str):
        return objeto
    if isinstance(objeto, dict):
        return '\n'.join(_achatar(v) for v in objeto.values())
    if isinstance(objeto, (list, tuple)):
        return '\n'.join(_achatar(v) for v in objeto)
    if objeto is None:
        return ''
    return str(objeto)


def _texto(resp):
    try:
        corpo = resp.()
    except Exception:
        return unescape(resp.text)
    return _achatar(corpo)


def _montar(form, valores, com_extras):
    dados = {}
    for campo in form['campos']:
        nome = campo['name']
        if not nome:
            continue
        rotulo = form['nomes'].get(nome) or (campo['attrs'].get('aria-label') or '')
        if rotulo not in valores:
            continue
        valor = valores[rotulo]
        if campo['tag'] == 'select':
            for texto, opcao in form['opcoes'].get(nome, []):
                if opcao and texto == valor:
                    valor = opcao
                    break
        dados[nome] = valor
    if com_extras:
        for rotulo, valor in valores.items():
            for chave in _chaves_extras(rotulo):
                dados.setdefault(chave, valor)
    return dados


def _marcador_de_aba(dados, palavra):
    leitor = _CACHE['leitor']
    for radio in leitor.radios:
        alvo = ' '.join([radio['rotulo'], radio['value'], radio['id'], radio['name'] or '']).lower()
        if radio['name'] and palavra in alvo:
            dados.setdefault(radio['name'], radio['value'])
    for escondido in leitor.hiddens:
        alvo = ' '.join([escondido['name'] or '', escondido['value']]).lower()
        if escondido['name'] and palavra in alvo:
            dados.setdefault(escondido['name'], escondido['value'])


def _candidatos():
    if 'candidatos' in _CACHE:
        return _CACHE['candidatos']
    js = _js()
    html = _html()
    achados = []
    padrao_fetch = re.compile(
        r'fetch\(\s*["\'`]([^"`\s]+)["\'`]([^;]{0,500}?)method\s*:\s*["\']POST["\']',
        re.S | re.I)
    for m in padrao_fetch.finditer(js):
        achados.append(m.group(1))
    for m in re.finditer(r'<form\b[^>]*>', html, re.I):
        tag = m.group(0)
        if re.search(r'method\s*=\s*["\']?post', tag, re.I):
            action = re.search(r'action\s*=\s*["\']([^"\']+)', tag, re.I)
            if action:
                achados.append(action.group(1))
    achados += [
        '/api/solicitacao', '/solicitacao', '/api/solicitacoes', '/solicitacoes',
        '/api/auxilio', '/auxilio', '/api/solicitar', '/solicitar',
        '/api/enviar', '/enviar', '/api/submit', '/submit',
    ]
    candidatos = []
    for url in achados:
        if '${' in url:
            base = url.split('${')[0]
            candidatos += [base + 'alunos', base + 'docentes', base]
            continue
        candidatos.append(url)
        if url.endswith('/'):
            candidatos += [url + 'alunos', url + 'docentes']
    rota = []
    for url in candidatos:
        url = url.split('?')[0]
        if not url or '{' in url:
            continue
        if not url.startswith('/'):
            url = '/' + url
        if url not in rota:
            rota.append(url)
    _CACHE['candidatos'] = rota
    return rota


def _resolver(chave):
    if _CACHE.get(chave):
        return _CACHE[chave]
    base = DADOS_DOCENTES if chave == 'docentes' else DADOS_ALUNOS
    marcador = ('Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
                if chave == 'docentes'
                else 'Assunto: Solicitação de Auxílio Financeiro - Participação em evento')
    palavra = 'docentes' if chave == 'docentes' else 'alunos'
    form = _formularios()[chave]
    client = TestClient(app, raise_server_exceptions=False)
    tentativas = []
    for url in _candidatos():
        for encoding in ('', 'form'):
            for estilo in ('formatado', 'bruto'):
                for com_extras in (False, True):
                    tentativas.append((url, encoding, estilo, com_extras, {}))
    for nome in ('aba', 'tipo', 'perfil', 'origem', 'formulario', 'form', 'tab',
                 'tipo_solicitante', 'categoria', 'tipo_formulario'):
        for url in _candidatos():
            for encoding in ('', 'form'):
                for estilo in ('formatado', 'bruto'):
                    tentativas.append((url, encoding, estilo, False, {nome: palavra}))
    for url, encoding, estilo, com_extras, extra in tentativas:
        valores = dict(base)
        if estilo == 'bruto':
            valores.update(BRUTOS)
            valores['VALOR SOLICITADO (R$)'] = '200000' if chave == 'docentes' else '150000'
        dados = _montar(form, valores, com_extras)
        _marcador_de_aba(dados, palavra)
        dados.update(extra)
        if encoding == '':
            resp = client.post(url, =dados)
        else:
            resp = client.post(url, data=dados)
        if resp.status_code in (200, 201):
            texto = _texto(resp)
            if marcador in texto and LINHA_OFICIO in texto:
                _CACHE[chave] = {'url': url, 'encoding': encoding, 'estilo': estilo,
                                 'dados': dados, 'texto': texto}
                return _CACHE[chave]
    pytest.fail(f'nao foi encontrado o endpoint de envio que devolve o oficio ({chave})')


def _enviar(chave, overrides=None):
    cfg = _resolver(chave)
    dados = dict(cfg['dados'])
    for rotulo, valor in (overrides or {}).items():
        nome = _nome_campo(_formularios()[chave], rotulo)
        if nome:
            dados[nome] = valor
        for chave_extra in _chaves_extras(rotulo):
            if chave_extra in dados:
                dados[chave_extra] = valor
    client = TestClient(app, raise_server_exceptions=False)
    if cfg['encoding'] == '':
        resp = client.post(cfg['url'], =dados)
    else:
        resp = client.post(cfg['url'], data=dados)
    return _texto(resp)


def test_a_pagina_do_formulario_e_servida_na_raiz():
    resp = TestClient(app, raise_server_exceptions=False).get('/')
    assert resp.status_code == 200
    assert 'ALUNOS' in resp.text
    assert 'DOCENTES' in resp.text


def test_as_abas_tem_os_rotulos_exatos_nessa_ordem():
    html = _html()
    alunos = re.search(_padrao_busca('ALUNOS'), html)
    docentes = re.search(_padrao_busca('DOCENTES'), html)
    assert alunos, 'aba ALUNOS ausente'
    assert docentes, 'aba DOCENTES ausente'
    assert alunos.start() < docentes.start()


def test_os_tres_blocos_tem_os_titulos_exatos():
    html = _html()
    for titulo in BLOCOS:
        assert re.search(_padrao_busca(titulo), html), f'bloco ausente: {titulo}'


def test_rotulos_exatos_de_todos_os_campos():
    _carregar_pagina()
    leitor = _CACHE['leitor']
    html = _CACHE['html']
    com_rotulos_ligados = sum(len(f['rotulos']) for f in leitor.forms) >= 20
    for rotulo in ROTULOS_TODOS:
        if com_rotulos_ligados:
            achou = any(_nome_campo(f, rotulo) for f in leitor.forms)
        else:
            achou = bool(re.search(_padrao_busca(rotulo), html))
        assert achou, f'rotulo ausente: {rotulo}'


def test_nivel_e_tipo_de_auxilio_somente_na_aba_alunos():
    html = _html()
    assert len(re.findall(_padrao_busca('NIVEL'), html)) == 1
    assert len(re.findall(_padrao_busca('TIPO DE AUXILIO'), html)) == 1
    forms = _formularios()
    assert _nome_campo(forms['alunos'], 'NIVEL')
    assert _nome_campo(forms['alunos'], 'TIPO DE AUXILIO')
    assert _nome_campo(forms['docentes'], 'NIVEL') is None
    assert _nome_campo(forms['docentes'], 'TIPO DE AUXILIO') is None


def test_as_selecoes_oferecem_as_opcoes_do_requisito():
    _carregar_pagina()
    leitor = _CACHE['leitor']
    oferecidas = set()
    for form in leitor.forms:
        for opcoes in form['opcoes'].values():
            for texto, _ in opcoes:
                if texto:
                    oferecidas.add(texto)
    for radio in leitor.radios:
        oferecidas.add(radio['rotulo'])
        oferecidas.add(radio['value'])
    for esperado in OPCOES_ESPERADAS:
        assert esperado in oferecidas, f'opcao ausente: {esperado}'


def test_todo_campo_tem_placeholder_que_nao_repete_o_rotulo():
    forms = _formularios()
    for chave in ('alunos', 'docentes'):
        for campo in forms[chave]['campos']:
            nome = campo['name']
            if campo['tag'] == 'select':
                opcoes = forms[chave]['opcoes'].get(nome, [])
                assert any(texto.strip() for texto, _ in opcoes), f'select sem opcoes: {nome}'
                continue
            if campo['tipo'] in ('hidden', 'radio', 'checkbox', 'submit', 'button'):
                continue
            placeholder = (campo['attrs'].get('placeholder') or '').strip()
            assert placeholder, f'campo sem placeholder: {nome}'
            rotulo = forms[chave]['nomes'].get(nome, '')
            assert placeholder.lower() != rotulo.strip().lower(), \
                f'placeholder repete o rotulo: {nome}'


def test_cada_aba_tem_o_botao_enviar_solicitacao():
    html = _html()
    assert len(re.findall(_padrao_busca('Enviar solicitação'), html)) >= 2


def test_o_cabecalho_mostra_a_universidade_e_o_logotipo():
    html = _html()
    assert re.search(_padrao_busca('Universidade de São Paulo'), html), \
        'o nome Universidade de São Paulo deve aparecer no cabecalho'
    leitor = _CACHE['leitor']
    logos = [url for tipo, url in leitor.recursos if 'usp-logo' in url.lower()]
    assert logos, 'o cabecalho nao referencia o logotipo usp-logo.png'
    alvo = logos[0].split('?')[0]
    if not alvo.startswith('/'):
        alvo = '/' + alvo
    resp = TestClient(app, raise_server_exceptions=False).get(alvo)
    assert resp.status_code == 200, f'o logotipo nao foi servido em {alvo}'
    assert resp.headers.get('content-type', '').startswith('image/')


def test_nenhum_recurso_vem_da_rede():
    _carregar_pagina()
    leitor = _CACHE['leitor']
    for tipo, url in leitor.recursos:
        assert not (url or '').lower().startswith(('http://', 'https://', '//')), \
            f'recurso externo ({tipo}): {url}'
    assert _js().strip(), 'app.js vazio'
    css = _css()
    for bloco in re.findall(r'@import[^;]+;', css, re.I):
        assert 'http' not in bloco.lower(), bloco
    for alvo in re.findall(r'url\(\s*["\']?([^"\')]+)', css, re.I):
        assert not alvo.lower().startswith(('http://', 'https://', '//')), alvo


def test_o_css_usa_a_identidade_da_usp():
    css = _css().lower()
    assert '#1094ab' in css, 'o azul primario #1094ab deve estar no style.css'
    assert 'sans-serif' in css, 'a fonte deve ser Open Sans ou outra sem serifa'


def test_o_brasao_nao_aparece_na_pagina():
    for conteudo in (_html(), _js(), _css()):
        baixo = conteudo.lower()
        assert 'brasao' not in baixo and 'brasão' not in baixo


def test_a_aba_alunos_comeca_ativa():
    _carregar_pagina()
    leitor = _CACHE['leitor']
    html = _CACHE['html']
    radio_alunos = [r for r in leitor.radios
                    if 'alunos' in (r['rotulo'] + ' ' + r['value'] + ' ' + r['id']).lower()]
    radio_docentes = [r for r in leitor.radios
                      if 'docentes' in (r['rotulo'] + ' ' + r['value'] + ' ' + r['id']).lower()]
    if radio_alunos and radio_docentes:
        assert radio_alunos[0]['checked'], 'a aba ALUNOS deveria vir marcada como ativa'
        assert not radio_docentes[0]['checked'], 'a aba DOCENTES nao deveria vir ativa'
        return
    marca_ativa = re.compile(r'activ|ativ|selec|current|open|check', re.I)
    marca_inativa = re.compile(r'inactiv|inativ|hidden|ocult|disab|display:\s*none', re.I)

    def marcacoes(nome_aba):
        return [m.group(2) for m in
                re.finditer(r'<(\w+)([^>]*)>\s*' + re.escape(nome_aba) + r'\s*<', html)]

    atributos_alunos = marcacoes('ALUNOS')
    atributos_docentes = marcacoes('DOCENTES')
    docentes_ativa = any(marca_ativa.search(a) for a in atributos_docentes)
    assert not docentes_ativa, 'a aba DOCENTES aparece marcada como ativa no HTML inicial'
    alunos_ativa = any(marca_ativa.search(a) for a in atributos_alunos)
    docentes_inativa = any(marca_inativa.search(a) for a in atributos_docentes)
    if not (alunos_ativa or docentes_inativa):
        pytest.skip('o HTML estatico nao deixa explicita a aba ativa inicial')


def test_envio_valido_de_aluno_devolve_o_oficio_preenchido():
    cfg = _resolver('alunos')
    texto = cfg['texto']
    for linha in LINHAS_ALUNOS:
        assert linha in texto, f'linha do oficio ausente: {linha!r}'
    assert 'Verba do programa' not in texto
    confirmacao = texto + _html() + _js()
    assert 'Solicitação registrada' in confirmacao


def test_envio_valido_de_docente_devolve_o_oficio_preenchido():
    cfg = _resolver('docentes')
    texto = cfg['texto']
    for linha in LINHAS_DOCENTES:
        assert linha in texto, f'linha do oficio ausente: {linha!r}'
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto
    assert re.search(r'^Programa: Estatística$', texto, re.M), \
        'o oficio do docente nao deve trazer nivel no Programa'


def test_envio_totalmente_vazio_so_pede_preencher_os_campos():
    _resolver('alunos')
    overrides = {rotulo: '' for rotulo in DADOS_ALUNOS}
    texto = _enviar('alunos', overrides)
    assert 'Preencha todos os campos' in texto
    assert texto.count('Preencha todos os campos') == 1
    for mensagem in ('N. USP deve conter apenas números', 'E-mail inválido',
                     'Valor solicitado deve ser maior que 0', 'CPF inválido',
                     'Data de nascimento inválida', LINHA_OFICIO):
        assert mensagem not in texto


def test_envio_invalido_acumula_todas_as_mensagens_aplicaveis():
    cfg = _resolver('alunos')
    if cfg['estilo'] == 'bruto':
        cpf, cep, data, valor = '1234567890', 'abc', '31-02-1990', '0'
    else:
        cpf, cep, data, valor = '123.456.789-0', '0550-8090', '1/2/1980', 'R$ 0,00'
    texto = _enviar('alunos', {
        'N. USP': 'USP12345',
        'E-MAIL': 'maria.souza em usp.br',
        'VALOR SOLICITADO (R$)': valor,
        'CPF (SEPARADOS POR PONTOS E TRACO)': cpf,
        'CEP': cep,
        'DATA DE NASCIMENTO': data,
        'NUMERO DA AGENCIA': 'A183',
        'BAIRRO': '',
    })
    for mensagem in MENSAGENS_FORMATO:
        assert mensagem in texto, f'mensagem ausente: {mensagem}'
    assert texto.count('Preencha todos os campos') == 1
    assert LINHA_OFICIO not in texto, 'o oficio nao pode ser gerado com erro'


def test_cpf_no_formato_certo_com_digito_verificador_errado():
    cfg = _resolver('alunos')
    cpf = '12345678900' if cfg['estilo'] == 'bruto' else '123.456.789-00'
    texto = _enviar('alunos', {'CPF (SEPARADOS POR PONTOS E TRACO)': cpf})
    assert 'CPF inválido' in texto
    assert 'CPF deve estar no formato 000.000.000-00' not in texto
    assert LINHA_OFICIO not in texto


def test_data_de_nascimento_com_dia_que_nao_existe():
    cfg = _resolver('alunos')
    data = '31021990' if cfg['estilo'] == 'bruto' else '31/02/1990'
    texto = _enviar('alunos', {'DATA DE NASCIMENTO': data})
    assert 'Data de nascimento inválida' in texto
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' not in texto
    assert LINHA_OFICIO not in texto
