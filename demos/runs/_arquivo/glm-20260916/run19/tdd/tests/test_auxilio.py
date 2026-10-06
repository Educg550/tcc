'''Testes do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Cobre o contrato do requisito: página única com as abas ALUNOS e DOCENTES, servida
como arquivos estáticos (index.html, style.css e app.js), e backend FastAPI que
valida a solicitação e devolve o ofício redigido, com rótulos e mensagens exatas.

Sem browser no ambiente, os comportamentos de tela são verificados pelos arquivos
estáticos servidos; os comportamentos de servidor, pela API HTTP. A rota de envio é
descoberta nas rotas POST registradas na aplicação, o corpo é tentado como formulário
e como JSON, e a resposta é lida de forma tolerante ao formato.
'''

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app as aplicacao  # noqa: E402

cliente = TestClient(aplicacao)

# Rótulos e mensagens exatos definidos no requisito.

B_SOLICITANTE = 'SOLICITANTE E EVENTO'
B_ENDERECO = 'ENDEREÇO DO SOLICITANTE'
B_PAGAMENTO = 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO'

L_NOME = 'NOME COMPLETO - SEM ABREVIAR'
L_NUSP = 'N. USP'
L_PROG = 'PROGRAMA'
L_NIVEL = 'NÍVEL'
L_TIPO = 'TIPO DE AUXÍLIO'
L_EMAIL = 'E-MAIL'
L_EVENTO = 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'
L_PERIODO = 'PERÍODO DO EVENTO, EXAME OU DEFESA'
L_CIDADE_EV = 'CIDADE DO EVENTO, EXAME OU DEFESA'
L_ESTADO_EV = 'ESTADO DO EVENTO, EXAME OU DEFESA'
L_PAIS_EV = 'PAÍS DO EVENTO, EXAME OU DEFESA'
L_LINK = 'LINK DO EVENTO, EXAME OU DEFESA'
L_VALOR = 'VALOR SOLICITADO (R$)'
L_DETALHE = 'DETALHAMENTO DO PEDIDO'
L_APRESENTA = 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'
L_DATA = 'DATA DE NASCIMENTO'
L_LOGRA = 'LOGRADOURO'
L_NUM = 'NÚMERO'
L_COMPL = 'COMPLEMENTO'
L_BAIRRO = 'BAIRRO'
L_CEP = 'CEP'
L_CIDADE = 'CIDADE'
L_ESTADO = 'ESTADO'
L_CPF = 'CPF (SEPARADOS POR PONTOS E TRAÇO)'
L_RG = 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'
L_BANCO = 'NOME DO BANCO'
L_AGENCIA = 'NÚMERO DA AGÊNCIA'
L_CONTA = 'NÚMERO DA CONTA'

ROTULOS_ALUNOS = [
    L_NOME, L_NUSP, L_PROG, L_NIVEL, L_TIPO, L_EMAIL, L_EVENTO, L_PERIODO,
    L_CIDADE_EV, L_ESTADO_EV, L_PAIS_EV, L_LINK, L_VALOR, L_DETALHE,
    L_APRESENTA, L_DATA, L_LOGRA, L_NUM, L_COMPL, L_BAIRRO, L_CEP, L_CIDADE,
    L_ESTADO, L_CPF, L_RG, L_BANCO, L_AGENCIA, L_CONTA,
]
ROTULOS_DOCENTES = [r for r in ROTULOS_ALUNOS if r not in (L_NIVEL, L_TIPO)]

VALORES = {
    L_NOME: 'Maria de Souza',
    L_NUSP: '1234567',
    L_PROG: 'Ciência da Computação',
    L_NIVEL: 'Doutorado',
    L_TIPO: 'Participação em evento',
    L_EMAIL: 'maria@usp.br',
    L_EVENTO: 'SBBD 2025',
    L_PERIODO: '1 a 3 de outubro de 2025',
    L_CIDADE_EV: 'São Paulo',
    L_ESTADO_EV: 'SP',
    L_PAIS_EV: 'Brasil',
    L_LINK: 'https://sbbd.org.br',
    L_VALOR: 'R$ 1.500,00',
    L_DETALHE: 'Inscrição e passagem aérea',
    L_APRESENTA: 'Pôster',
    L_DATA: '01/02/1980',
    L_LOGRA: 'Rua do Anfiteatro',
    L_NUM: '181',
    L_COMPL: 'Apto 12',
    L_BAIRRO: 'Butantã',
    L_CEP: '05508-090',
    L_CIDADE: 'São Paulo',
    L_ESTADO: 'SP',
    L_CPF: '123.456.789-09',
    L_RG: '12.345.678-9',
    L_BANCO: 'Banco do Brasil',
    L_AGENCIA: '1234',
    L_CONTA: '98765-4',
}

# O usuário digita só dígitos; a pontuação é da aplicação.
DIGITOS = {
    L_VALOR: '150000',
    L_CPF: '12345678909',
    L_CEP: '05508090',
    L_DATA: '01021980',
}

MENSAGENS = {
    'obrigatorias': 'Preencha todos os campos',
    'nusp': 'N. USP deve conter apenas números',
    'agencia': 'Número da agência deve conter apenas números',
    'valor': 'Valor solicitado deve ser maior que 0',
    'email': 'E-mail inválido',
    'cpf_formato': 'CPF deve estar no formato 000.000.000-00',
    'cep_formato': 'CEP deve estar no formato 00000-000',
    'data_formato': 'Data de nascimento deve estar no formato dd/mm/aaaa',
    'cpf_dv': 'CPF inválido',
    'data_calendario': 'Data de nascimento inválida',
}


# Coleta dos campos da página servida, associando cada controle ao rótulo que o precede.

class _Coletor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.controles = []
        self._label_for = {}
        self._pendente = []
        self._cap_for = None
        self._cap_txt = []
        self._select = None
        self._opcao = None
        self._form = -1

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self._form += 1
        elif tag == 'label':
            self._cap_for = a.get('for')
            self._cap_txt = []
        elif tag in ('input', 'textarea', 'select'):
            rotulo = ' '.join(self._pendente)
            if a.get('id') and a['id'] in self._label_for:
                rotulo = self._label_for[a['id']]
            controle = {'tag': tag, 'attrs': a, 'rotulo': rotulo,
                        'opcoes': [], 'form': self._form}
            self.controles.append(controle)
            self._pendente = []
            if tag == 'select':
                self._select = controle
        elif tag == 'option':
            self._opcao = {'attrs': a, 'texto': []}

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == 'label' and self._cap_for is not None:
            if self._cap_for:
                self._label_for[self._cap_for] = ' '.join(self._cap_txt)
            self._cap_for = None
        elif tag == 'option' and self._opcao is not None:
            if self._select is not None:
                texto = ' '.join(''.join(self._opcao['texto']).split())
                valor = self._opcao['attrs'].get('value', texto)
                self._select['opcoes'].append((valor, texto))
            self._opcao = None
        elif tag == 'select':
            self._select = None
            self._pendente = []
        elif tag == 'textarea':
            self._pendente = []

    def handle_data(self, data):
        if self._cap_for is not None:
            self._cap_txt.append(data)
        if self._opcao is not None:
            self._opcao['texto'].append(data)
        elif self._select is None:
            self._pendente.append(data)


_cache_controles = None


def controles_da_pagina():
    global _cache_controles
    if _cache_controles is None:
        coletor = _Coletor()
        coletor.feed(cliente.get('/').text)
        _cache_controles = coletor.controles
    return _cache_controles


def _norm(texto):
    return ' '.join(texto.split()).casefold()


def mapear(controles, rotulos):
    mapa = {}
    usados = set()
    for rotulo in sorted(rotulos, key=len, reverse=True):
        alvo = _norm(rotulo)
        for i, controle in enumerate(controles):
            if i in usados:
                continue
            if alvo in _norm(controle['rotulo']):
                mapa[rotulo] = controle
                usados.add(i)
                break
    return mapa


def chave_de(controle):
    attrs = controle['attrs']
    return attrs.get('name') or attrs.get('id') or _norm(controle['rotulo'])


def valor_para(controle, desejado):
    if controle['tag'] != 'select':
        return desejado
    alvo = _norm(desejado)
    for _valor, texto in controle['opcoes']:
        if _norm(texto) == alvo:
            return texto
    return desejado


def abas_de_formularios():
    unicos = sorted({c['form'] for c in controles_da_pagina()})
    if len(unicos) == 2:
        return unicos[0], unicos[1]
    return None, None


def payload_para(rotulos, sobrepor=None, digitos=False, form_idx=None):
    todos = controles_da_pagina()
    escopo = [c for c in todos if c['form'] == form_idx] if form_idx is not None else todos
    if not escopo:
        escopo = todos
    mapa = mapear(escopo, rotulos)
    corpo = {}
    for rotulo in rotulos:
        controle = mapa.get(rotulo)
        if controle is None:
            continue
        valor = VALORES[rotulo]
        if digitos and rotulo in DIGITOS:
            valor = DIGITOS[rotulo]
        corpo[chave_de(controle)] = valor_para(controle, valor)
    if form_idx is not None:
        nomes = set(corpo)
        for controle in escopo:
            if (controle['tag'] == 'input'
                    and controle['attrs'].get('type', '').lower() == 'hidden'):
                nome = controle['attrs'].get('name')
                if nome and nome not in nomes:
                    corpo[nome] = controle['attrs'].get('value', '')
    for rotulo, valor in (sobrepor or {}).items():
        controle = mapa.get(rotulo)
        corpo[chave_de(controle) if controle else rotulo] = valor
    return corpo


_cache_rotas = None


def rotas_post():
    global _cache_rotas
    if _cache_rotas is None:
        _cache_rotas = [rota.path for rota in aplicacao.routes
                        if 'POST' in (getattr(rota, 'methods', None) or set())]
    if not _cache_rotas:
        pytest.fail('o backend não registra nenhuma rota POST para receber a solicitação')
    return _cache_rotas


def _achat(objeto, partes):
    if isinstance(objeto, str):
        partes.append(objeto)
    elif isinstance(objeto, dict):
        for valor in objeto.values():
            _achat(valor, partes)
    elif isinstance(objeto, (list, tuple)):
        for valor in objeto:
            _achat(valor, partes)
    else:
        partes.append(str(objeto))


def extrair(resposta):
    try:
        corpo = resposta.()
    except Exception:
        return resposta.text
    partes = []
    _achat(corpo, partes)
    return '\n'.join(partes)


def enviar(tab, expect, sobrepor=None):
    rotulos = ROTULOS_DOCENTES if tab == 'docentes' else ROTULOS_ALUNOS
    form_alunos, form_docentes = abas_de_formularios()
    form_idx = form_docentes if tab == 'docentes' else form_alunos
    ultima = None
    for caminho in rotas_post():
        for digitos in (False, True):
            corpo = payload_para(rotulos, sobrepor=sobrepor, digitos=digitos,
                                 form_idx=form_idx)
            for kwargs in ({'data': {c: str(v) for c, v in corpo.items()}},
                           {'': corpo}):
                ultima = cliente.post(caminho, **kwargs)
                if expect in extrair(ultima):
                    return ultima
    pytest.fail(
        'nenhum envio produziu {esperado!r}; última resposta: {status} {texto}'.format(
            esperado=expect,
            status=getattr(ultima, 'status_code', 'sem resposta'),
            texto=(ultima.text[:300] if ultima is not None else '')))


# Arquivos estáticos e contrato visual da página.


def test_pagina_inicial_tem_abas_blocos_rotulos_e_cabecalho_usp():
    resposta = cliente.get('/')
    assert resposta.status_code == 200
    html = resposta.text
    assert 'ALUNOS' in html and 'DOCENTES' in html
    assert html.find('ALUNOS') < html.find('DOCENTES')
    for bloco in (B_SOLICITANTE, B_ENDERECO, B_PAGAMENTO):
        assert bloco in html
    posicao = 0
    for rotulo in ROTULOS_ALUNOS:
        achou = html.find(rotulo, posicao)
        assert achou != -1, 'rótulo ausente ou fora de ordem: {0!r}'.format(rotulo)
        posicao = achou + 1
    assert html.count('NÍVEL') == 1
    assert html.count('TIPO DE AUXÍLIO') == 1
    for opcao in ('Mestrado', 'Doutorado', 'Participação em evento',
                  'Banca de exame ou defesa', 'Outro', 'Pôster',
                  'Apresentação oral', 'Outra', 'Não irá apresentar trabalho'):
        assert opcao in html
    assert html.count('Enviar solicitação') >= 2
    assert 'assets/usp-logo.png' in html
    assert 'Universidade de São Paulo' in html
    evidencia_aba_ativa = any(
        marcador in arquivo
        for arquivo in (html, cliente.get('/app.js').text,
                        cliente.get('/style.css').text)
        for marcador in ('active', 'checked', 'aria-selected="true"'))
    assert evidencia_aba_ativa
    assert 'Solicitação registrada' in (html + cliente.get('/app.js').text)


def test_campos_de_digitar_tem_placeholder_de_exemplo():
    controles = controles_da_pagina()
    sem_placeholder = {'submit', 'button', 'hidden', 'checkbox', 'radio',
                       'file', 'image', 'reset'}
    digitacao = [c for c in controles
                 if c['tag'] == 'textarea'
                 or (c['tag'] == 'input'
                     and c['attrs'].get('type', 'text').lower() not in sem_placeholder)]
    assert digitacao, 'nenhum campo de digitação encontrado na página'
    for controle in digitacao:
        placeholder = _norm(controle['attrs'].get('placeholder') or '')
        rotulo = _norm(controle['rotulo'])
        assert placeholder, 'campo sem placeholder: {0}'.format(controle['attrs'])
        assert placeholder != rotulo, 'placeholder repete o rótulo: {0}'.format(
            controle['attrs'])
    assert len([c for c in controles if c['tag'] == 'select']) >= 3


def test_css_usa_identidade_usp_sem_recursos_remotos():
    resposta = cliente.get('/style.css')
    assert resposta.status_code == 200
    css = resposta.text
    assert '#1094ab' in css
    assert '#64c4d2' in css
    assert '#fcb421' in css
    assert 'Open Sans' in css
    assert 'sans-serif' in css
    assert '@import' not in css
    assert 'http://' not in css and 'https://' not in css
    assert 'flex' in css or 'grid' in css
    assert 'pre-line' in css or 'pre-wrap' in css
    assert any(m in css for m in ('active', 'checked', 'aria-selected'))


def test_js_cuida_da_tela_e_chama_o_backend_sem_rede_externa():
    resposta = cliente.get('/app.js')
    assert resposta.status_code == 200
    js = resposta.text
    assert len(js) > 200
    assert 'http://' not in js and 'https://' not in js
    assert 'fetch(' in js or 'XMLHttpRequest' in js
    assert any(ev in js for ev in ('blur', 'change', 'focusout', 'input'))
    assert any(m in js for m in ('R$', 'toLocaleString', 'currency', 'Intl'))


def test_logotipo_servido_e_unico_elemento_grafico():
    resposta = cliente.get('/assets/usp-logo.png')
    assert resposta.status_code == 200
    assert resposta.headers.get('content-type', '').startswith('image/')
    juntos = (cliente.get('/').text + cliente.get('/app.js').text
              + cliente.get('/style.css').text)
    referencias = re.findall(r'assets/\S+', juntos)
    assert referencias, 'nenhuma referência a assets/ na página'
    for referencia in referencias:
        assert 'usp-logo' in referencia
    assert 'brasao' not in juntos.lower()


# Comportamento do backend: validação e geração do ofício.


def test_envio_valido_de_alunos_devolve_oficio_completo():
    marcador = 'Interessada(o): Maria de Souza - 1234567'
    resposta = enviar('alunos', marcador)
    texto = extrair(resposta)
    fragmentos = [
        marcador,
        'E-mail: maria@usp.br',
        'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
        'Programa: Ciência da Computação - Doutorado',
        'A CCP-Ciência da Computação aprovou na data de hoje',
        'Dados do evento',
        'Evento: SBBD 2025',
        'Período: 1 a 3 de outubro de 2025',
        'Local: São Paulo - SP - Brasil',
        'Link do evento: https://sbbd.org.br',
        'Apresentação de trabalho: Pôster',
        'Valor solicitado: R$ 1.500,00',
        'Detalhamento: Inscrição e passagem aérea',
        'Endereço da(o) interessada(o)',
        'Rua do Anfiteatro, 181',
        'Complemento: Apto 12',
        'CEP: 05508-090',
        'Butantã, São Paulo - SP',
        'Dados para pagamento',
        'Data de nascimento: 01/02/1980',
        'CPF: 123.456.789-09',
        'RG / RNM: 12.345.678-9',
        'Banco: Banco do Brasil',
        'Agência: 1234',
        'Conta: 98765-4',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    for fragmento in fragmentos:
        assert fragmento in texto, 'ausente no ofício: {0!r}'.format(fragmento)


def test_envio_valido_de_docentes_devolve_oficio_de_verba_do_programa():
    marcador = 'Interessada(o): Maria de Souza - 1234567'
    resposta = enviar('docentes', marcador)
    texto = extrair(resposta)
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'A CCP-Ciência da Computação aprovou na data de hoje' in texto
    assert 'Doutorado' not in texto
    assert 'Participação em evento' not in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto


def test_campos_opcionais_vazios_tiram_as_linhas_do_oficio():
    resposta = enviar('alunos', 'Interessada(o):',
                      sobrepor={L_LINK: '', L_COMPL: ''})
    texto = extrair(resposta)
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto
    assert 'Valor solicitado: R$ 1.500,00' in texto


def test_campo_obrigatorio_vazio_gera_mensagem_unica_e_nao_gera_oficio():
    resposta = enviar('alunos', MENSAGENS['obrigatorias'],
                      sobrepor={L_NOME: '', L_BAIRRO: ''})
    texto = extrair(resposta)
    assert texto.count('Preencha todos os campos') == 1
    assert 'Interessada(o):' not in texto
    resposta = enviar('alunos', MENSAGENS['obrigatorias'], sobrepor={L_PROG: ''})
    assert extrair(resposta).count('Preencha todos os campos') == 1


def test_todas_as_mensagens_aplicaveis_aparecem_juntas():
    sobrepor = {
        L_NUSP: '12a45',
        L_AGENCIA: 'ag',
        L_VALOR: '0',
        L_EMAIL: 'mariausp.br',
        L_CPF: '123.456.789',
        L_CEP: '0550809',
        L_DATA: '01-02-1980',
    }
    resposta = enviar('alunos', MENSAGENS['cep_formato'], sobrepor=sobrepor)
    texto = extrair(resposta)
    for mensagem in (
            MENSAGENS['nusp'],
            MENSAGENS['agencia'],
            MENSAGENS['valor'],
            MENSAGENS['email'],
            MENSAGENS['cpf_formato'],
            MENSAGENS['cep_formato'],
            MENSAGENS['data_formato'],
    ):
        assert mensagem in texto
    assert 'Interessada(o):' not in texto


def test_email_sem_dominio_e_rejeitado():
    resposta = enviar('alunos', MENSAGENS['email'], sobrepor={L_EMAIL: 'maria@'})
    assert MENSAGENS['email'] in extrair(resposta)


def test_cpf_no_formato_certo_com_digito_verificador_errado_e_rejeitado():
    resposta = enviar('alunos', MENSAGENS['cpf_dv'],
                      sobrepor={L_CPF: '123.456.789-00'})
    texto = extrair(resposta)
    assert MENSAGENS['cpf_dv'] in texto
    assert 'Interessada(o):' not in texto


def test_data_de_nascimento_inexistente_e_rejeitada():
    for data in ('31/02/1980', '10/13/1980'):
        resposta = enviar('alunos', MENSAGENS['data_calendario'],
                          sobrepor={L_DATA: data})
        assert MENSAGENS['data_calendario'] in extrair(resposta)
