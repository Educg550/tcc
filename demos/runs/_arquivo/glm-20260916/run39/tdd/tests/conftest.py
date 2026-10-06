import re
import unicodedata

import pytest
from fastapi.testclient import TestClient

from app import app

_cliente = TestClient(app)

VALORES = {
    'nome': 'Maria Aparecida de Souza Oliveira',
    'n_usp': '1234567',
    'programa': 'Ciência da Computação',
    'nivel': 'Mestrado',
    'tipo_auxilio': 'Participação em evento',
    'email': 'maria.oliveira@usp.br',
    'nome_evento': 'Congresso Brasileiro de Computação',
    'periodo': '10/06/2025 a 14/06/2025',
    'cidade_evento': 'Rio de Janeiro',
    'estado_evento': 'RJ',
    'pais_evento': 'Brasil',
    'link_evento': 'https://congresso.example.br',
    'valor': 'R$ 1.500,00',
    'detalhamento': 'Inscrição no evento e passagem aérea de ida e volta.',
    'apresentacao': 'Pôster',
    'data_nascimento': '01/02/1980',
    'logradouro': 'Rua do Anfiteatro',
    'numero': '375',
    'complemento': 'Sala 12',
    'bairro': 'Butantã',
    'cep': '05508-090',
    'cidade': 'São Paulo',
    'estado': 'SP',
    'cpf': '123.456.789-09',
    'rg': '12.345.678-9',
    'banco': 'Banco do Brasil',
    'agencia': '1234',
    'conta': '98765-4',
}

ALIASES = {
    'nome': ['nome_completo', 'nome'],
    'n_usp': ['n_usp', 'numero_usp'],
    'programa': ['programa'],
    'nivel': ['nivel'],
    'tipo_auxilio': ['tipo_auxilio', 'tipo_de_auxilio'],
    'email': ['email', 'e_mail'],
    'nome_evento': ['nome_evento', 'nome_do_evento', 'evento'],
    'periodo': ['periodo', 'periodo_evento'],
    'cidade_evento': ['cidade_evento', 'cidade_do_evento'],
    'estado_evento': ['estado_evento', 'estado_do_evento'],
    'pais_evento': ['pais_evento', 'pais_do_evento'],
    'link_evento': ['link_evento', 'link_do_evento', 'link'],
    'valor': ['valor_solicitado', 'valor'],
    'detalhamento': ['detalhamento', 'detalhamento_do_pedido'],
    'apresentacao': ['apresentacao', 'apresentacao_trabalho', 'ira_apresentar_trabalho'],
    'data_nascimento': ['data_nascimento', 'nascimento'],
    'logradouro': ['logradouro'],
    'numero': ['numero', 'numero_endereco'],
    'complemento': ['complemento'],
    'bairro': ['bairro'],
    'cep': ['cep'],
    'cidade': ['cidade'],
    'estado': ['estado'],
    'cpf': ['cpf'],
    'rg': ['rg', 'rg_rnm', 'rnm'],
    'banco': ['nome_banco', 'banco'],
    'agencia': ['numero_agencia', 'agencia'],
    'conta': ['numero_conta', 'conta'],
}

CHAVES_DE_ABA = ['aba', 'perfil']
NOMES_DE_ABA = {'aba', 'perfil', 'categoria', 'formulario', 'modalidade', 'guia'}
PISTAS_DE_ABA = ('aba', 'perfil', 'form', 'modalidade', 'guia', 'origem')
PREFERENCIA_ENUM = {
    'nivel': ['mestr'],
    'tipo_auxilio': ['participa'],
    'apresentacao': ['poster'],
}

_cache = {}


def _norm(texto):
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return ''.join(caractere for caractere in texto.lower() if caractere.isalnum())


def _sem_aspas(texto):
    return texto.strip(chr(34)).strip(chr(39))


def _resolver(referencia, esquema):
    alvo = esquema
    for parte in referencia.lstrip('#/').split('/'):
        alvo = alvo[parte]
    return alvo


def _esquema():
    if 'openapi' not in _cache:
        try:
            _cache['openapi'] = app.openapi()
        except Exception:
            _cache['openapi'] = {}
    return _cache['openapi']


def _rotas_post():
    if 'rotas_post' not in _cache:
        rotas = []
        for rota in app.routes:
            metodos = getattr(rota, 'methods', None) or set()
            if 'POST' in {metodo.upper() for metodo in metodos}:
                rotas.append(rota.path)
        _cache['rotas_post'] = rotas
    return _cache['rotas_post']


def _rota_de(aba):
    rotas = _rotas_post()
    if not rotas:
        pytest.fail('A aplicação não expõe rota POST para receber a solicitação.')
    if len(rotas) > 1:
        pista = 'docente' if aba == 'docentes' else 'alun'
        for rota in rotas:
            if pista in _norm(rota):
                return rota
    return rotas[0]


def _campos_da(rota):
    if rota not in _cache:
        campos = None
        tipo_midia = 'application/'
        try:
            esquema = _esquema()
            operacao = (esquema.get('paths', {}).get(rota, {}) or {}).get('post') or {}
            conteudo = (operacao.get('requestBody', {}) or {}).get('content', {}) or {}
            for tipo, midia in conteudo.items():
                tipo_midia = tipo
                pedaco = midia.get('schema', {}) if isinstance(midia, dict) else {}
                if isinstance(pedaco, dict) and '$ref' in pedaco:
                    pedaco = _resolver(pedaco['$ref'], esquema)
                if isinstance(pedaco, dict) and pedaco.get('properties'):
                    campos = dict(pedaco['properties'])
                break
        except Exception:
            campos = None
        _cache[rota] = (campos, tipo_midia)
    return _cache[rota]


def _classificar(nome):
    n = _norm(nome)
    if not n:
        return None
    if 'cpf' in n:
        return 'cpf'
    if 'cep' in n:
        return 'cep'
    if 'nasc' in n:
        return 'data_nascimento'
    if 'agenc' in n:
        return 'agencia'
    if 'conta' in n:
        return 'conta'
    if 'banco' in n:
        return 'banco'
    if 'rg' in n or 'rnm' in n:
        return 'rg'
    if 'mail' in n:
        return 'email'
    if 'valor' in n:
        return 'valor'
    if 'link' in n or 'url' in n or 'site' in n:
        return 'link_evento'
    if 'programa' in n:
        return 'programa'
    if 'nivel' in n:
        return 'nivel'
    if 'usp' in n:
        return 'n_usp'
    if 'auxilio' in n or 'tipo' in n:
        return 'tipo_auxilio'
    if 'periodo' in n:
        return 'periodo'
    if 'detalh' in n:
        return 'detalhamento'
    if 'apresent' in n or 'trabalho' in n:
        return 'apresentacao'
    if 'evento' in n:
        if 'cidade' in n:
            return 'cidade_evento'
        if 'estado' in n:
            return 'estado_evento'
        if 'pais' in n:
            return 'pais_evento'
        return 'nome_evento'
    if 'bairro' in n:
        return 'bairro'
    if 'lograd' in n:
        return 'logradouro'
    if 'complemento' in n:
        return 'complemento'
    if 'numero' in n:
        return 'numero'
    if 'cidade' in n:
        return 'cidade'
    if 'estado' in n:
        return 'estado'
    if 'nome' in n:
        return 'nome'
    return None


def _valor_para(logico, pedaco):
    valores = pedaco.get('enum') or []
    if valores:
        for alvo in PREFERENCIA_ENUM.get(logico, []):
            for valor in valores:
                if alvo in _norm(valor):
                    return valor
        return valores[0]
    if pedaco.get('type') in ('number', 'integer') and logico == 'valor':
        return 1500.0 if pedaco.get('type') == 'number' else 1500
    return VALORES[logico]


def _tipar(pedaco, valor):
    if (
        isinstance(pedaco, dict)
        and pedaco.get('type') in ('number', 'integer')
        and isinstance(valor, str)
    ):
        digitos = ''.join(c for c in valor if c.isdigit())
        numero = (int(digitos) if digitos else 0) / 100
        if pedaco.get('type') == 'integer':
            return int(numero)
        return numero
    return valor


def _montar_payload(rota, aba):
    campos, _ = _campos_da(rota)
    if campos is None:
        payload = {}
        for logico, apelidos in ALIASES.items():
            for apelido in apelidos:
                payload[apelido] = VALORES[logico]
        valor_aba = 'docentes' if aba == 'docentes' else 'alunos'
        for chave in CHAVES_DE_ABA:
            payload[chave] = valor_aba
        if aba == 'docentes':
            for apelido in ALIASES['nivel'] + ALIASES['tipo_auxilio']:
                payload.pop(apelido, None)
        return payload

    esquema = _esquema()
    payload = {}
    discriminador = None
    for nome, pedaco in campos.items():
        if isinstance(pedaco, dict) and '$ref' in pedaco:
            try:
                pedaco = _resolver(pedaco['$ref'], esquema)
            except Exception:
                pedaco = {}
        if not isinstance(pedaco, dict):
            pedaco = {}
        valores = pedaco.get('enum') or []
        normas = {_norm(str(v)) for v in valores}
        if {'alunos', 'docentes'} <= normas or {'aluno', 'docente'} <= normas:
            discriminador = (nome, valores)
            continue
        n = _norm(nome)
        if n in NOMES_DE_ABA or any(pista in n for pista in PISTAS_DE_ABA):
            discriminador = (nome, valores or None)
            continue
        logico = _classificar(nome)
        if logico is None:
            tipo = pedaco.get('type')
            if tipo in ('number', 'integer'):
                payload[nome] = 1
            elif tipo == 'boolean':
                payload[nome] = True
            else:
                payload[nome] = 'Exemplo'
        else:
            payload[nome] = _valor_para(logico, pedaco)
    if discriminador is not None:
        nome, valores = discriminador
        pista = 'docente' if aba == 'docentes' else 'alun'
        if valores:
            payload[nome] = next((v for v in valores if pista in _norm(str(v))), valores[-1])
        else:
            payload[nome] = 'docentes' if aba == 'docentes' else 'alunos'
    if aba == 'docentes':
        for nome in list(payload):
            if _classificar(nome) in ('nivel', 'tipo_auxilio'):
                payload.pop(nome, None)
    return payload


def _enviar(rota, payload, tipo_midia):
    if '' in (tipo_midia or ''):
        resposta = _cliente.post(rota, =payload)
        if resposta.status_code == 422:
            alternativa = _cliente.post(rota, data=payload)
            return alternativa if alternativa.status_code != 422 else resposta
        return resposta
    resposta = _cliente.post(rota, data=payload)
    if resposta.status_code == 422:
        alternativa = _cliente.post(rota, =payload)
        return alternativa if alternativa.status_code != 422 else resposta
    return resposta


def enviar_com(aba='alunos', **alteracoes):
    rota = _rota_de(aba)
    campos, tipo_midia = _campos_da(rota)
    payload = _montar_payload(rota, aba)
    indice = {}
    for nome in payload:
        logico = _classificar(nome)
        if logico and logico not in indice:
            indice[logico] = nome
    for logico, valor in alteracoes.items():
        nome = indice.get(logico)
        if nome is not None:
            pedaco = (campos or {}).get(nome)
            payload[nome] = _tipar(pedaco if isinstance(pedaco, dict) else {}, valor)
        elif campos is None:
            for apelido in ALIASES.get(logico, [logico]):
                payload[apelido] = valor
    return _enviar(rota, payload, tipo_midia)


def textos_da_resposta(resposta):
    try:
        dados = resposta.()
    except Exception:
        return [resposta.text]
    achados = []

    def visitar(parte):
        if isinstance(parte, str):
            achados.append(parte)
        elif isinstance(parte, dict):
            for valor in parte.values():
                visitar(valor)
        elif isinstance(parte, (list, tuple)):
            for item in parte:
                visitar(item)
        elif isinstance(parte, (int, float)):
            achados.append(str(parte))

    visitar(dados)
    return achados or [resposta.text]


def tem_mensagem(resposta, trecho):
    return any(trecho in texto for texto in textos_da_resposta(resposta))


@pytest.fixture(scope='session')
def cliente():
    return _cliente


@pytest.fixture(scope='session')
def norm():
    return _norm


@pytest.fixture(scope='session')
def pagina(cliente):
    resposta = cliente.get('/')
    assert resposta.status_code == 200, 'GET / deveria servir a página do formulário'
    return resposta.text


@pytest.fixture(scope='session')
def pagina_norm(norm, pagina):
    return norm(pagina)


@pytest.fixture(scope='session')
def tela_norm(norm, pagina, js):
    return norm(pagina + js)


@pytest.fixture(scope='session')
def caminho_css(pagina):
    achados = re.findall(r'<link[^>]+href=([^\s>]+)', pagina, re.I)
    folhas = [_sem_aspas(a) for a in achados if '.css' in a.lower()]
    assert folhas, 'a página deveria carregar o style.css'
    return folhas[0]


@pytest.fixture(scope='session')
def caminho_js(pagina):
    achados = re.findall(r'<script[^>]+src=([^\s>]+)', pagina, re.I)
    rotas = [_sem_aspas(a) for a in achados if '.js' in a.lower()]
    assert rotas, 'a página deveria carregar o app.js'
    return rotas[0]


@pytest.fixture(scope='session')
def css(cliente, caminho_css):
    caminho = caminho_css.split('?')[0].split('#')[0]
    if not caminho.startswith('/'):
        caminho = '/' + caminho
    resposta = cliente.get(caminho)
    assert resposta.status_code == 200, f'GET {caminho} deveria servir o CSS'
    return resposta.text


@pytest.fixture(scope='session')
def js(cliente, caminho_js):
    caminho = caminho_js.split('?')[0].split('#')[0]
    if not caminho.startswith('/'):
        caminho = '/' + caminho
    resposta = cliente.get(caminho)
    assert resposta.status_code == 200, f'GET {caminho} deveria servir o JavaScript'
    return resposta.text


@pytest.fixture(scope='session')
def enviar():
    return enviar_com


@pytest.fixture(scope='session')
def textos():
    return textos_da_resposta


@pytest.fixture(scope='session')
def contem():
    return tem_mensagem
