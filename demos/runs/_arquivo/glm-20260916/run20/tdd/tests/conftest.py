import html as htmllib
import 
import os
import re
import sys
import unicodedata

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402

ROTULOS_EM_ORDEM = [
    'alunos',
    'docentes',
    'solicitante e evento',
    'nome completo - sem abreviar',
    'n. usp',
    'programa',
    'nível',
    'tipo de auxílio',
    'e-mail',
    'nome do evento / banca de exame ou defesa',
    'período do evento, exame ou defesa',
    'cidade do evento, exame ou defesa',
    'estado do evento, exame ou defesa',
    'país do evento, exame ou defesa',
    'link do evento, exame ou defesa',
    'valor solicitado (r$)',
    'detalhamento do pedido',
    'irá apresentar trabalho no evento? que tipo?',
    'endereço do solicitante',
    'data de nascimento',
    'logradouro',
    'número',
    'complemento',
    'bairro',
    'cep',
    'cidade',
    'estado',
    'informações para pagamento / reembolso',
    'cpf (separados por pontos e traço)',
    'rg / rnm (separados por pontos e traço)',
    'nome do banco',
    'número da agência',
    'número da conta',
]

VALORES = {
    'nome': 'Maria da Silva',
    'n_usp': '9876543',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria@usp.br',
    'evento': 'Simpósio Brasileiro de Banco de Dados',
    'periodo': '23 a 26 de setembro de 2025',
    'cidade_evento': 'São Paulo',
    'estado_evento': 'SP',
    'pais_evento': 'Brasil',
    'link': 'https://sbbd.org.br',
    'valor': 'R$ 1.500,00',
    'detalhamento': 'Passagem aérea e inscrição no evento.',
    'apresentacao': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero': '181',
    'complemento': 'Letra D',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg_rnm': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '98765-4',
}

CAMPOS = {
    'nome': ('NOME COMPLETO - SEM ABREVIAR',
             ['nome', 'nome_completo', 'nomeCompleto', 'nome_completo_sem_abreviar']),
    'n_usp': ('N. USP',
              ['n_usp', 'nUsp', 'nusp', 'numero_usp', 'num_usp', 'numeroUSP', 'numusp']),
    'programa': ('PROGRAMA', ['programa']),
    'nivel': ('NÍVEL', ['nivel', 'nível', 'grau']),
    'tipo_auxilio': ('TIPO DE AUXÍLIO',
                     ['tipo_auxilio', 'tipo_de_auxilio', 'tipoAuxilio', 'auxilio']),
    'email': ('E-MAIL', ['email', 'e_mail', 'e-mail', 'eMail']),
    'evento': ('NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
               ['evento', 'nome_evento', 'nome_do_evento', 'nomeEvento']),
    'periodo': ('PERÍODO DO EVENTO, EXAME OU DEFESA',
                ['periodo', 'periodo_evento', 'periodo_do_evento', 'periodoEvento']),
    'cidade_evento': ('CIDADE DO EVENTO, EXAME OU DEFESA',
                      ['cidade_evento', 'cidade_do_evento', 'cidadeEvento']),
    'estado_evento': ('ESTADO DO EVENTO, EXAME OU DEFESA',
                      ['estado_evento', 'estado_do_evento', 'estadoEvento', 'uf_evento']),
    'pais_evento': ('PAÍS DO EVENTO, EXAME OU DEFESA',
                    ['pais_evento', 'pais_do_evento', 'paisEvento', 'pais']),
    'link': ('LINK DO EVENTO, EXAME OU DEFESA',
             ['link', 'link_evento', 'link_do_evento', 'url', 'url_evento']),
    'valor': ('VALOR SOLICITADO (R$)',
              ['valor', 'valor_solicitado', 'valorSolicitado', 'valor_solicitado_rs']),
    'detalhamento': ('DETALHAMENTO DO PEDIDO',
                     ['detalhamento', 'detalhamento_pedido', 'detalhamento_do_pedido',
                      'detalhamentoPedido', 'descricao']),
    'apresentacao': ('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
                     ['apresentacao', 'apresentacao_trabalho', 'apresentacao_de_trabalho',
                      'ira_apresentar_trabalho', 'trabalho']),
    'data_nascimento': ('DATA DE NASCIMENTO',
                        ['data_nascimento', 'data_de_nascimento', 'nascimento',
                         'dataDeNascimento']),
    'logradouro': ('LOGRADOURO', ['logradouro', 'endereco']),
    'numero': ('NÚMERO', ['numero', 'numero_endereco', 'num_endereco', 'numeroEndereco']),
    'complemento': ('COMPLEMENTO', ['complemento']),
    'bairro': ('BAIRRO', ['bairro']),
    'cep': ('CEP', ['cep']),
    'cidade': ('CIDADE', ['cidade']),
    'estado': ('ESTADO', ['estado', 'uf']),
    'cpf': ('CPF (SEPARADOS POR PONTOS E TRAÇO)',
            ['cpf', 'numero_cpf', 'numero_de_cpf']),
    'rg_rnm': ('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
               ['rg_rnm', 'rg', 'rnm', 'rg_ou_rnm', 'rgRnm']),
    'banco': ('NOME DO BANCO', ['banco', 'nome_banco', 'nome_do_banco', 'nomeBanco']),
    'agencia': ('NÚMERO DA AGÊNCIA',
                ['agencia', 'numero_agencia', 'num_agencia', 'numero_da_agencia',
                 'numeroAgencia']),
    'conta': ('NÚMERO DA CONTA',
              ['conta', 'numero_conta', 'num_conta', 'numero_da_conta', 'numeroConta']),
}

CHAVES_ABA = [
    'aba', 'formulario', 'form', 'origem', 'perfil', 'categoria', 'papel',
    'modo', 'secao', 'tipo_solicitacao', 'tipo_formulario',
    'tipo_de_solicitacao', 'tipo_solicitante',
]

VAZIOS = {campo: '' for campo in CAMPOS}


def _variantes(rotulo):
    sem_acento = unicodedata.normalize('NFKD', rotulo).encode('ascii', 'ignore').decode()
    base = re.sub(r'[^0-9a-z]+', '_', sem_acento.lower()).strip('_')
    return list({rotulo, rotulo.lower(), sem_acento, sem_acento.lower(), base, base.upper()})


def _montar_payload(dados, aba, valor_bruto=False):
    payload = {chave: aba for chave in CHAVES_ABA}
    for campo, (rotulo, apelidos) in CAMPOS.items():
        if aba == 'DOCENTES' and campo in ('nivel', 'tipo_auxilio'):
            continue
        valor = dados.get(campo, VALORES[campo])
        if valor_bruto and campo == 'valor':
            valor = '150000'
        for chave in _variantes(rotulo) + apelidos:
            payload.setdefault(chave, valor)
    return payload


def _alvos(pagina, js, cliente):
    achados = []
    achados += re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", js)
    achados += re.findall(r"\.open\(\s*['\"]POST['\"]\s*,\s*['\"]([^'\"]+)['\"]", js)
    achados += re.findall(r"action=[\"']([^\"']*)[\"']", pagina)
    achados += re.findall(r"['\"](/[A-Za-z0-9_][A-Za-z0-9_/\-.]*)['\"]", js)
    achados += re.findall(r'`(/[^`{]+)`', js)
    alvos = []
    for achado in achados:
        if achado.startswith(('http://', 'https://', '//')):
            continue
        if achado in ('', '#'):
            continue
        if re.search(r'\.(html?|css|js||png|jpe?g|svg|gif|ico|txt|map)$', achado, re.I):
            continue
        if not achado.startswith('/'):
            achado = '/' + achado
        if achado not in alvos:
            alvos.append(achado)
    if alvos:
        return alvos
    for candidato in ('/api/solicitacao', '/solicitacao', '/api/solicitar', '/solicitar',
                      '/api/solicitacoes', '/solicitacoes', '/api/auxilio', '/auxilio',
                      '/api/enviar', '/enviar', '/api/submit', '/submit',
                      '/api/formulario', '/formulario', '/api/validar', '/validar'):
        if cliente.post(candidato, ={}).status_code != 404:
            alvos.append(candidato)
    return alvos


def texto_da_resposta(resposta):
    try:
        return .dumps(resposta.(), ensure_ascii=False)
    except ValueError:
        return resposta.text


def algum(respostas, trecho):
    return any(trecho in texto_da_resposta(r) for r in respostas)


def nenhum(respostas, trecho):
    return all(trecho not in texto_da_resposta(r) for r in respostas)


def mensagem_unica(respostas, trecho):
    com_o_trecho = [r for r in respostas if trecho in texto_da_resposta(r)]
    return bool(com_o_trecho) and all(
        texto_da_resposta(r).count(trecho) == 1 for r in com_o_trecho
    )


@pytest.fixture(scope='session')
def cliente():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope='session')
def pagina(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 200, 'a página não está sendo servida em /'
    return htmllib.unescape(resposta.text)


@pytest.fixture(scope='session')
def texto(pagina):
    return re.sub(r'\s+', ' ', pagina).lower()


@pytest.fixture(scope='session')
def css(cliente, pagina):
    caminhos = re.findall(r"<link[^>]+href=\"([^\"]+\.css[^\"]*)\"", pagina, re.I)
    if not caminhos:
        caminhos = ['/style.css']
    for caminho in caminhos:
        if not caminho.startswith('/'):
            caminho = '/' + caminho
        resposta = cliente.get(caminho)
        if resposta.status_code == 200:
            return resposta.text
    pytest.fail('nenhuma folha de estilo foi servida')


@pytest.fixture(scope='session')
def js(cliente, pagina):
    caminhos = re.findall(r"<script[^>]+src=\"([^\"]+)\"", pagina, re.I)
    if not caminhos:
        caminhos = ['/app.js']
    for caminho in reversed(caminhos):
        if not caminho.startswith('/'):
            caminho = '/' + caminho
        resposta = cliente.get(caminho)
        if resposta.status_code == 200:
            return resposta.text
    pytest.fail('nenhum arquivo de JavaScript foi servido')


@pytest.fixture(scope='session')
def enviar(cliente, pagina, js):
    alvos = _alvos(pagina, js, cliente)
    assert alvos, 'não encontrei para onde o formulário envia a solicitação'
    escolhido = []

    def _enviar(dados=None, aba='ALUNOS'):
        base = dados or {}
        tentativas = [
            _montar_payload(base, aba, False),
            _montar_payload(base, aba, True),
        ]
        for marcador in (aba, aba.lower(), aba.lower().rstrip('s')):
            payload = _montar_payload(base, aba, False)
            for chave in CHAVES_ABA:
                payload[chave] = marcador
            tentativas.append(payload)
        respostas = []
        for payload in tentativas:
            for alvo in (escolhido or alvos):
                for resposta in (cliente.post(alvo, =payload),
                                 cliente.post(alvo, data=payload)):
                    if resposta.status_code in (200, 400, 422):
                        respostas.append(resposta)
                if respostas and not escolhido:
                    escolhido.append(alvo)
                if escolhido:
                    break
            if algum(respostas, 'Interessada(o):'):
                break
        return respostas

    return _enviar
