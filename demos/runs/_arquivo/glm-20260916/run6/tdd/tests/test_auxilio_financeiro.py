"""Testes do Requisito 01: formulário de auxílio financeiro da Pós-Graduação do IME-USP."""

import html
import 
import re
import unicodedata

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

_cache = {}

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

VALORES_ENVIO = ('150000', 150000, 'R$ 1.500,00', '1500,00', '1500.00', 1500.0)

TRECHOS_OFICIO = (
    'Interessada(o): Maria de Souza Silva - 9876543',
    'E-mail: maria.silva@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Doutorado',
    'Dados do evento',
    'Evento: Congresso Brasileiro de Computação',
    'Período: 10 a 15 de março de 2026',
    'Local: Campinas - SP - Brasil',
    'Link do evento: https://evento.usp.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Passagem aérea e inscrição no evento.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Appto 41',
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
)


def _norm(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_')


def _formas(trecho):
    variantes = [trecho, re.sub(r'\s+', ' ', trecho)]
    for variante in list(variantes):
        variantes.append(variante.encode('unicode_escape').decode())
        variantes.append(.dumps(variante, ensure_ascii=True)[1:-1])
    return variantes


def _tem(texto, trecho):
    normalizado = re.sub(r'\s+', ' ', texto)
    return any(f in texto or f in normalizado for f in _formas(trecho))


def _texto(resposta):
    return html.unescape(resposta.text)


def _index():
    if 'index' not in _cache:
        resposta = client.get('/')
        assert resposta.status_code == 200, 'GET / deve responder 200'
        _cache['index'] = html.unescape(resposta.text)
    return _cache['index']


def _caminho_estatico(sufixo, padrao):
    refs = re.findall(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']?", _index())
    for ref in refs:
        if ref.split('?')[0].endswith(sufixo):
            return ref if ref.startswith('/') else '/' + ref
    return padrao


def _css():
    if 'css' not in _cache:
        resposta = client.get(_caminho_estatico('.css', '/style.css'))
        assert resposta.status_code == 200, 'a folha de estilo deve ser servida'
        _cache['css'] = resposta.text
    return _cache['css']


def _js():
    if 'js' not in _cache:
        resposta = client.get(_caminho_estatico('.js', '/app.js'))
        assert resposta.status_code == 200, 'app.js deve ser servido'
        _cache['js'] = html.unescape(resposta.text)
    return _cache['js']


def _tela():
    return _index() + '\n' + _js()


def _rotas_post():
    return [r for r in app.routes if 'POST' in getattr(r, 'methods', set())]


def _spec():
    if 'spec' not in _cache:
        try:
            resposta = client.get('/openapi.')
            _cache['spec'] = resposta.() if resposta.status_code == 200 else {}
        except Exception:
            _cache['spec'] = {}
    return _cache['spec']


def _props(rota):
    try:
        operacao = _spec()['paths'][rota.path]['post']
        schema = operacao['requestBody']['content']['application/']['schema']
        if '$ref' in schema:
            schema = _spec()['components']['schemas'][schema['$ref'].split('/')[-1]]
        return list(schema.get('properties', {}))
    except Exception:
        return []


def _templates(rota):
    modelos = []
    props = _props(rota)
    if props:
        modelos.append(list(props))
    modelos.append([_norm(r) for r in ROTULOS])
    modelos.append(list(ROTULOS))
    return modelos


def _valor(chave, val='150000'):
    n = _norm(str(chave))
    if 'nascimento' in n:
        return '01/02/1980'
    if 'cpf' in n:
        return '123.456.789-09'
    if 'cep' in n:
        return '05508-090'
    if 'rg' in n or 'rnm' in n:
        return '12.345.678-9'
    if 'usp' in n:
        return '9876543'
    if 'valor' in n:
        return val
    if 'mail' in n:
        return 'maria.silva@usp.br'
    if 'nivel' in n:
        return 'Doutorado'
    if 'auxilio' in n:
        return 'Participação em evento'
    if 'banco' in n:
        return 'Banco do Brasil'
    if 'agencia' in n:
        return '1234'
    if 'conta' in n:
        return '98765-4'
    if 'link' in n:
        return 'https://evento.usp.br'
    if 'apresenta' in n or 'trabalho' in n:
        return 'Pôster'
    if 'evento' in n:
        if 'cidade' in n:
            return 'Campinas'
        if 'estado' in n:
            return 'SP'
        if 'pais' in n:
            return 'Brasil'
        if 'periodo' in n:
            return '10 a 15 de março de 2026'
        return 'Congresso Brasileiro de Computação'
    if 'periodo' in n:
        return '10 a 15 de março de 2026'
    if 'detalh' in n or 'pedido' in n:
        return 'Passagem aérea e inscrição no evento.'
    if 'nome' in n:
        return 'Maria de Souza Silva'
    if 'logradouro' in n or 'endereco' in n:
        return 'Rua do Anfiteatro'
    if 'numero' in n:
        return '181'
    if 'complemento' in n:
        return 'Appto 41'
    if 'bairro' in n:
        return 'Butantã'
    if 'cidade' in n:
        return 'São Paulo'
    if 'estado' in n:
        return 'SP'
    if 'pais' in n:
        return 'Brasil'
    if ('aba' in n or 'perfil' in n or 'papel' in n or 'form' in n or 'solicitante' in n) and 'nome' not in n:
        return 'alunos'
    if 'tipo' in n:
        return 'Participação em evento'
    return 'texto'


def _post(rota, payload, modo):
    if modo == 'data':
        return client.post(rota.path, data=payload)
    return client.post(rota.path, =payload)


def _tentar(rota, payload):
    for modo, kwargs in (('', {'': payload}), ('data', {'data': payload})):
        try:
            resposta = client.post(rota.path, **kwargs)
        except Exception:
            continue
        if resposta.status_code < 500 and _tem(_texto(resposta), 'Encaminhe-se ao Serviço Financeiro'):
            return resposta, modo
    return None, None


def _obter_alunos():
    if 'alunos' in _cache:
        return _cache['alunos']
    rotas = _rotas_post()
    if not rotas:
        pytest.fail('o backend não tem nenhuma rota POST para receber a solicitação')
    for rota in rotas:
        for modelo in _templates(rota):
            for val in VALORES_ENVIO:
                payload = {k: _valor(k, val) for k in modelo}
                resposta, modo = _tentar(rota, payload)
                if resposta is not None:
                    _cache['alunos'] = (rota, payload, modo)
                    return _cache['alunos']
    pytest.fail('nenhuma rota POST gerou o ofício a partir de um envio completo de aluno')


def _obter_docentes():
    if 'docentes' in _cache:
        return _cache['docentes']
    _, payload_alunos, _ = _obter_alunos()
    val = '150000'
    for k, v in payload_alunos.items():
        if 'valor' in _norm(str(k)):
            val = v
            break
    for rota in _rotas_post():
        for modelo in _templates(rota):
            base = {
                k: _valor(k, val)
                for k in modelo
                if 'nivel' not in _norm(str(k)) and 'auxilio' not in _norm(str(k))
            }
            variantes = [dict(base)]
            for k in base:
                n = _norm(str(k))
                if any(p in n for p in ('aba', 'perfil', 'papel', 'form', 'solicitante', 'categoria', 'origem')):
                    for v in ('docentes', 'docente', 'DOCENTES', 'Docente'):
                        variante = dict(base)
                        variante[k] = v
                        variantes.append(variante)
            for variante in variantes:
                resposta, modo = _tentar(rota, variante)
                if resposta is not None and _tem(_texto(resposta), 'Verba do programa'):
                    _cache['docentes'] = (rota, variante, modo)
                    return _cache['docentes']
    pytest.fail('nenhuma rota POST gerou o ofício de docente')


def _chave(payload, incluir, excluir=()):
    for k in payload:
        n = _norm(str(k))
        if any(p in n for p in incluir) and not any(x in n for x in excluir):
            return k
    return None


def _resposta_modificada(*mudancas):
    rota, payload, modo = _obter_alunos()
    novo = dict(payload)
    for incluir, excluir, valor in mudancas:
        k = _chave(novo, incluir, excluir)
        if k is None:
            pytest.fail(f'campo {incluir} não encontrado no envio descoberto')
        novo[k] = valor
    return _post(rota, novo, modo)


def _resposta_sem(*remocoes):
    rota, payload, modo = _obter_alunos()
    novo = dict(payload)
    for incluir, excluir in remocoes:
        k = _chave(novo, incluir, excluir)
        if k is not None:
            del novo[k]
    return _post(rota, novo, modo)


def _achar(texto, trecho, pos):
    i = texto.find(trecho, pos)
    if i >= 0:
        return i
    for forma in _formas(trecho):
        j = texto.find(forma, pos)
        if j >= 0:
            return j
    return -1


def _placeholder(tag):
    m = (
        re.search(r'placeholder\s*=\s*"([^"]*)"', tag, re.I)
        or re.search(r"placeholder\s*=\s*'([^']*)'", tag, re.I)
        or re.search(r'placeholder\s*=\s*([^\s>]+)', tag, re.I)
    )
    return m.group(1) if m else None


# ----- entrega da tela -----


def test_index_e_servido_como_html():
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert 'text/html' in resposta.headers.get('content-type', '')


def test_arquivos_estaticos_servidos():
    for sufixo, padrao in (('.css', '/style.css'), ('.js', '/app.js'), ('usp-logo', '/assets/usp-logo.png')):
        resposta = client.get(_caminho_estatico(sufixo, padrao))
        assert resposta.status_code == 200, f'recurso {sufixo} deve ser servido'
        assert resposta.content, f'recurso {sufixo} não pode ser vazio'


def test_cabecalho_institucional_da_usp():
    index = _index()
    assert 'usp-logo' in index.lower()
    assert _tem(index, 'Universidade de São Paulo')
    assert 'brasao' not in _norm(index)


def test_abas_alunos_e_docentes_nessa_ordem():
    tela = _tela()
    assert 'ALUNOS' in tela and 'DOCENTES' in tela
    assert tela.index('ALUNOS') < tela.index('DOCENTES')


def test_blocos_com_titulos_visiveis():
    tela = _tela()
    for titulo in ('SOLICITANTE E EVENTO', 'ENDEREÇO DO SOLICITANTE', 'INFORMAÇÕES PARA PAGAMENTO / REEMBOLSO'):
        assert _tem(tela, titulo), titulo


def test_rotulos_presentes_e_na_ordem():
    tela = _tela()
    pos = 0
    for rotulo in ROTULOS:
        i = _achar(tela, rotulo, pos)
        assert i >= 0, f'rótulo ausente ou fora de ordem: {rotulo}'
        pos = i + len(rotulo)


def test_opcoes_das_selecoes():
    tela = _tela()
    for opcao in (
        'Mestrado',
        'Doutorado',
        'Participação em evento',
        'Banca de exame ou defesa',
        'Outro',
        'Pôster',
        'Apresentação oral',
        'Outra',
        'Não irá apresentar trabalho',
    ):
        assert _tem(tela, opcao), opcao


def test_botao_enviar_solicitacao():
    assert _tem(_tela(), 'Enviar solicitação')


def test_titulo_da_confirmacao():
    assert _tem(_tela(), 'Solicitação registrada')


def test_todo_campo_tem_placeholder_exemplo():
    tela = _tela()
    tags = [
        t
        for t in re.findall(r'<(?:input|textarea)\b[^>]*>', tela, re.I)
        if not re.search(r"type\s*=\s*[\"']?(submit|button|hidden|reset|image)\b", t, re.I)
    ]
    if not tags:
        assert 'placeholder' in tela.lower()
        return
    sem = [t for t in tags if _placeholder(t) is None]
    assert not sem, f'campos sem placeholder: {sem}'
    rotulos = {r.lower() for r in ROTULOS}
    for t in tags:
        ph = (_placeholder(t) or '').strip().lower()
        assert ph and ph not in rotulos


def test_identidade_visual_no_css():
    css = _css().lower()
    assert '#1094ab' in css
    assert '#64c4d2' in css
    assert '#fcb421' in css
    assert 'open sans' in css


def test_campos_distribuidos_em_colunas():
    css = _css().lower()
    assert 'grid' in css or 'flex' in css or 'column' in css


def test_oficio_preserva_quebras_de_linha():
    assert (
        'white-space' in _css().lower()
        or '<pre' in _index().lower()
        or 'innertext' in _js().lower()
    )


# ----- backend -----


def test_backend_tem_rota_para_a_solicitacao():
    assert _rotas_post(), 'o backend precisa de uma rota POST para receber a solicitação'


def test_envio_valido_de_aluno_devolve_oficio_preenchido():
    rota, payload, modo = _obter_alunos()
    resposta = _post(rota, payload, modo)
    texto = _texto(resposta)
    for trecho in TRECHOS_OFICIO:
        assert _tem(texto, trecho), f'trecho ausente no ofício: {trecho!r}'


def test_envio_de_docente_devolve_oficio_de_docente():
    rota, payload, modo = _obter_docentes()
    resposta = _post(rota, payload, modo)
    texto = _texto(resposta)
    assert _tem(texto, 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
    assert _tem(texto, 'Programa: Ciência da Computação')
    assert _tem(texto, 'Interessada(o): Maria de Souza Silva - 9876543')
    assert _tem(texto, 'Encaminhe-se ao Serviço Financeiro para providências.')
    assert not _tem(texto, 'Programa: Ciência da Computação - Doutorado')


def test_linhas_opcionais_saem_do_oficio_quando_vazias():
    rota, payload, modo = _obter_alunos()
    novo = dict(payload)
    for incluir in (('link',), ('complemento',)):
        k = _chave(novo, incluir)
        if k is not None:
            novo[k] = ''
    resposta, _modo = _tentar(rota, novo)
    assert resposta is not None, 'envio sem os campos opcionais deve gerar ofício'
    texto = _texto(resposta)
    assert not _tem(texto, 'Link do evento:')
    assert not _tem(texto, 'Complemento:')
    assert _tem(texto, 'Encaminhe-se ao Serviço Financeiro para providências.')


def test_campo_obrigatorio_vazio():
    resposta = _resposta_sem((('nome',), ('evento', 'banco', 'usp')), (('bairro',), ()))
    texto = _texto(resposta)
    assert _tem(texto, 'Preencha todos os campos')
    assert not _tem(texto, 'Encaminhe-se ao Serviço Financeiro')
    assert texto.count('Preencha todos os campos') <= 1


def test_mensagens_que_se_aplicam_aparecem_juntas():
    resposta = _resposta_modificada((('usp',), (), '12a45'), (('mail',), (), 'maria.sem-arroba'))
    texto = _texto(resposta)
    assert _tem(texto, 'N. USP deve conter apenas números')
    assert _tem(texto, 'E-mail inválido')


def test_n_usp_deve_conter_apenas_numeros():
    texto = _texto(_resposta_modificada((('usp',), (), '12a45')))
    assert _tem(texto, 'N. USP deve conter apenas números')


def test_agencia_deve_conter_apenas_numeros():
    texto = _texto(_resposta_modificada((('agencia',), (), '12a4')))
    assert _tem(texto, 'Número da agência deve conter apenas números')


def test_valor_solicitado_deve_ser_maior_que_zero():
    for valor in (0, '0', 'R$ 0,00'):
        texto = _texto(_resposta_modificada((('valor',), (), valor)))
        if _tem(texto, 'Valor solicitado deve ser maior que 0'):
            return
    pytest.fail('valor 0 não produziu a mensagem esperada')


def test_email_invalido():
    texto = _texto(_resposta_modificada((('mail',), (), 'maria.silva.sem-arroba')))
    assert _tem(texto, 'E-mail inválido')


def test_cpf_fora_do_formato():
    texto = _texto(_resposta_modificada((('cpf',), (), '123456789')))
    assert _tem(texto, 'CPF deve estar no formato 000.000.000-00')


def test_cpf_com_digito_verificador_errado():
    texto = _texto(_resposta_modificada((('cpf',), (), '123.456.789-00')))
    assert _tem(texto, 'CPF inválido')


def test_cep_fora_do_formato():
    texto = _texto(_resposta_modificada((('cep',), (), '0550809')))
    assert _tem(texto, 'CEP deve estar no formato 00000-000')


def test_data_fora_do_formato():
    texto = _texto(_resposta_modificada((('nascimento',), (), '1/2/1980')))
    assert _tem(texto, 'Data de nascimento deve estar no formato dd/mm/aaaa')


def test_data_inexistente():
    for valor in ('32/01/1980', '29/02/1981', '10/13/1980'):
        texto = _texto(_resposta_modificada((('nascimento',), (), valor)))
        assert _tem(texto, 'Data de nascimento inválida'), valor
