import 
import unicodedata

import pytest

BR = chr(92) + 'n'

VALOR_CANDIDATOS = ['R$ 1.500,00', '150000', 1500, '1500,00', '1.500,00']

_EXIGIR_ALUNOS = (
    'Encaminhe-se ao Serviço Financeiro',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Valor solicitado: R$ 1.500,00',
)

_EXIGIR_DOCENTES = (
    'Encaminhe-se ao Serviço Financeiro',
    'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
)

_SEM = object()


def _norm(nome):
    s = unicodedata.normalize('NFKD', str(nome)).encode('ascii', 'ignore').decode()
    return ''.join(c for c in s.lower() if 'a' <= c <= 'z')


def _corpo(r):
    texto = r.text
    if '' in r.headers.get('content-type', ''):
        try:
            texto = .dumps(r.(), ensure_ascii=False)
        except ValueError:
            pass
    return texto.replace(BR, chr(10))


def _rotas_post(client):
    r = client.get('/openapi.')
    if r.status_code == 200:
        return [c for c, op in r.().get('paths', {}).items() if 'post' in op]
    rotas = []
    for rota in getattr(client.app, 'routes', []):
        if 'POST' in (getattr(rota, 'methods', None) or set()):
            rotas.append(rota.path)
    return rotas


def _props_corpo(client, caminho):
    r = client.get('/openapi.')
    if r.status_code != 200:
        return {}
    doc = r.()
    op = doc.get('paths', {}).get(caminho, {}).get('post', {})
    conteudo = (op.get('requestBody') or {}).get('content', {})
    sch = conteudo.get('application/', {}).get('schema')
    if sch is None:
        sch = conteudo.get('application/x-www-form-urlencoded', {}).get('schema')
    if not sch:
        return {}
    comps = doc.get('components', {}).get('schemas', {})
    if '$ref' in sch:
        sch = comps.get(sch['$ref'].split('/')[-1], {})
    props = {}
    for nome, info in sch.get('properties', {}).items():
        if isinstance(info, dict) and '$ref' in info:
            info = comps.get(info['$ref'].split('/')[-1], info)
        props[nome] = info if isinstance(info, dict) else {}
    return props


def _valor_enum(info, *palavras):
    for v in info.get('enum') or []:
        vn = _norm(v)
        if any(p in vn for p in palavras):
            return v
    return None


def _prop_disc(props):
    for nome, info in props.items():
        vals = [_norm(v) for v in (info.get('enum') or [])]
        if vals and any('alun' in v for v in vals) and any('docen' in v or 'prof' in v for v in vals):
            return nome
    for nome, info in props.items():
        if info.get('enum'):
            continue
        n = _norm(nome)
        if ('aba' in n or 'perfil' in n or 'origem' in n or 'modo' in n or 'categoria' in n
                or 'tiposolicit' in n or 'tipodeform' in n
                or n in ('tipo', 'formulario', 'form', 'solicitacao')):
            return nome
    return None


def _valor_para(nome, info):
    n = _norm(nome)
    if info.get('enum'):
        if 'nivel' in n:
            return _valor_enum(info, 'mestr') or 'Mestrado'
        if 'auxilio' in n:
            return _valor_enum(info, 'particip') or 'Participação em evento'
        if 'apresent' in n or 'trabalho' in n:
            return _valor_enum(info, 'oster') or 'Pôster'
        v = _valor_enum(info, 'alun')
        return v if v is not None else info['enum'][0]
    if 'usp' in n:
        return '1234567'
    if 'cpf' in n:
        return '529.982.247-25'
    if 'cep' in n:
        return '05508-090'
    if 'email' in n:
        return 'maria.silva@usp.br'
    if 'nasc' in n:
        return '01/02/1980'
    if 'agencia' in n:
        return '1234'
    if 'conta' in n:
        return '12345-6'
    if 'banco' in n:
        return 'Banco do Brasil'
    if 'rg' in n:
        return '12.345.678-9'
    if 'valor' in n:
        return None
    if 'evento' in n or 'exame' in n or 'defesa' in n or 'banca' in n:
        if 'link' in n or 'url' in n:
            return 'https://ime.usp.br/evento'
        if 'periodo' in n or 'data' in n:
            return '10/03/2025 a 14/03/2025'
        if 'cidade' in n:
            return 'Campinas'
        if 'estado' in n or n.endswith('uf'):
            return 'SP'
        if 'pais' in n:
            return 'Brasil'
        return 'Simpósio de Sistemas Distribuídos'
    if 'periodo' in n:
        return '10/03/2025 a 14/03/2025'
    if 'link' in n or 'url' in n:
        return 'https://ime.usp.br/evento'
    if 'cidade' in n:
        return 'São Paulo'
    if 'estado' in n:
        return 'SP'
    if 'pais' in n:
        return 'Brasil'
    if 'bairro' in n:
        return 'Butantã'
    if 'logradouro' in n or 'endereco' in n:
        return 'Rua do Anfiteatro'
    if 'complemento' in n:
        return 'Prédio A'
    if 'numero' in n or n == 'num':
        return '375'
    if 'programa' in n:
        return 'Ciência da Computação'
    if 'nivel' in n:
        return 'Mestrado'
    if 'auxilio' in n:
        return 'Participação em evento'
    if 'apresent' in n or 'trabalho' in n:
        return 'Pôster'
    if 'detalh' in n or 'justific' in n or 'descric' in n or 'obs' in n:
        return 'Passagens aéreas e diárias'
    if 'nome' in n:
        return 'Maria da Silva'
    return 'teste'


def _candidatos(props, modo):
    disc = _prop_disc(props)
    vals = []
    if disc is not None and props[disc].get('enum'):
        chave = 'alun' if modo == 'alunos' else 'docen'
        for v in props[disc]['enum']:
            vn = _norm(v)
            if chave in vn or (modo == 'docentes' and 'prof' in vn):
                vals.append(v)
    if modo == 'alunos':
        vals += ['alunos', 'ALUNOS', 'aluno']
    else:
        vals += ['docentes', 'DOCENTES', 'docente', 'DOCENTE', 'professor', 'Professor']
    unicos = []
    for v in vals:
        if v not in unicos:
            unicos.append(v)
    return unicos


def _post(client, url, payload):
    r = client.post(url, =payload)
    if r.status_code == 422:
        dados = {k: ('' if v is None else str(v)) for k, v in payload.items()}
        r2 = client.post(url, data=dados)
        if r2.status_code != 422:
            return r2
    return r


def _enviar(client, modo, mutacoes=None, exigir=('Encaminhe-se ao Serviço Financeiro',)):
    mut = dict(mutacoes or {})
    for caminho in _rotas_post(client):
        props = _props_corpo(client, caminho)
        disc = _prop_disc(props)
        base = {}
        for nome, info in props.items():
            v = _valor_para(nome, info)
            if v is not None:
                base[nome] = v
        vp = None
        for nome in props:
            if 'valor' in _norm(nome):
                vp = nome
                break
        vals_disc = _candidatos(props, modo) if disc is not None else [None]
        for dv in vals_disc:
            url = caminho
            if '{' in caminho:
                ini = caminho.find('{')
                fim = caminho.find('}', ini)
                url = caminho[:ini] + (dv or modo) + caminho[fim + 1:]
            for vc in (VALOR_CANDIDATOS if (vp is not None and vp not in mut) else [None]):
                payload = dict(base)
                if disc is not None and dv is not None:
                    payload[disc] = dv
                for k, v in mut.items():
                    if v is _SEM:
                        payload.pop(k, None)
                    else:
                        payload[k] = v
                if vp is not None and vp not in mut:
                    payload[vp] = vc
                r = _post(client, url, payload)
                c = _corpo(r)
                if all(x in c for x in exigir) and 'Preencha todos os campos' not in c:
                    return {'url': url, 'payload': payload, 'corpo': c}
    return None


def _acha(props, *palavras):
    for nome in props:
        n = _norm(nome)
        if all(p in n for p in palavras):
            return nome
    return None


def _unica(client, alunos, **mut):
    payload = dict(alunos['payload'])
    for k, v in mut.items():
        if v is _SEM:
            payload.pop(k, None)
        else:
            payload[k] = v
    r = _post(client, alunos['url'], payload)
    return _corpo(r)


@pytest.fixture(scope='module')
def alunos(client):
    e = _enviar(client, 'alunos', exigir=_EXIGIR_ALUNOS)
    assert e is not None, 'o backend não aceitou uma solicitação válida da aba ALUNOS'
    return e


@pytest.fixture(scope='module')
def docentes(client):
    e = _enviar(client, 'docentes', exigir=_EXIGIR_DOCENTES)
    if e is None:
        for caminho in _rotas_post(client):
            props = _props_corpo(client, caminho)
            aux = _acha(props, 'auxilio')
            nivel = _acha(props, 'nivel')
            if aux is not None:
                e = _enviar(client, 'docentes', mutacoes={aux: 'Verba do programa'}, exigir=_EXIGIR_DOCENTES)
                if e is not None:
                    break
            if aux is not None and nivel is not None:
                e = _enviar(client, 'docentes', mutacoes={nivel: _SEM, aux: _SEM}, exigir=_EXIGIR_DOCENTES)
                if e is not None:
                    break
    assert e is not None, 'o backend não aceitou uma solicitação válida da aba DOCENTES'
    return e


def test_oficio_da_aba_alunos_traz_os_dados_no_lugar(alunos):
    c = alunos['corpo']
    linhas = [
        'Interessada(o): Maria da Silva - 1234567',
        'E-mail: maria.silva@usp.br',
        'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
        'Programa: Ciência da Computação - Mestrado',
        'A CCP-Ciência da Computação aprovou na data de hoje',
        'Dados do evento',
        'Evento: Simpósio de Sistemas Distribuídos',
        'Período: 10/03/2025 a 14/03/2025',
        'Local: Campinas - SP - Brasil',
        'Link do evento: https://ime.usp.br/evento',
        'Apresentação de trabalho: Pôster',
        'Valor solicitado: R$ 1.500,00',
        'Detalhamento: Passagens aéreas e diárias',
        'Endereço da(o) interessada(o)',
        'Rua do Anfiteatro, 375',
        'Complemento: Prédio A',
        'CEP: 05508-090',
        'Butantã, São Paulo - SP',
        'Dados para pagamento',
        'Data de nascimento: 01/02/1980',
        'CPF: 529.982.247-25',
        'RG / RNM: 12.345.678-9',
        'Banco: Banco do Brasil',
        'Agência: 1234',
        'Conta: 12345-6',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    for linha in linhas:
        assert linha in c, 'linha ausente do ofício: ' + linha
    assert '<<' not in c


def test_oficio_preserva_as_quebras_de_linha(alunos):
    c = alunos['corpo']
    duas_linhas = 'Interessada(o): Maria da Silva - 1234567' + chr(10) + 'E-mail: maria.silva@usp.br'
    assert duas_linhas in c


def test_oficio_da_aba_docentes_usa_verba_do_programa(docentes):
    c = docentes['corpo']
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in c
    assert 'Programa: Ciência da Computação' in c
    assert ' - Mestrado' not in c
    assert 'Interessada(o): Maria da Silva - 1234567' in c
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in c


def test_opcionais_vazios_saem_do_oficio(client, alunos):
    props = _props_corpo(client, alunos['url'])
    link = _acha(props, 'link') or _acha(props, 'url')
    comp = _acha(props, 'complemento')
    assert link is not None and comp is not None
    e = _enviar(client, 'alunos', mutacoes={link: '', comp: ''}, exigir=(
        'Encaminhe-se ao Serviço Financeiro',
        'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    ))
    assert e is not None, 'envio sem os opcionais deveria ser válido'
    c = e['corpo']
    assert 'Link do evento:' not in c
    assert 'Complemento:' not in c
    assert 'Local: Campinas - SP - Brasil' in c
    assert 'CEP: 05508-090' in c


def test_campo_obrigatorio_vazio_gera_mensagem_unica(client, alunos):
    props = _props_corpo(client, alunos['url'])
    nome = _acha(props, 'completo') or _acha(props, 'nome')
    assert nome is not None, 'campo de nome não identificado'
    c = _unica(client, alunos, **{nome: ''})
    assert 'Preencha todos os campos' in c
    assert c.count('Preencha todos os campos') == 1
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_n_usp_deve_conter_apenas_numeros(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'usp')
    assert p is not None
    c = _unica(client, alunos, **{p: 'abc123'})
    assert 'N. USP deve conter apenas números' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_agencia_deve_conter_apenas_numeros(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'agencia')
    assert p is not None
    c = _unica(client, alunos, **{p: '12a4'})
    assert 'Número da agência deve conter apenas números' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_valor_solicitado_deve_ser_maior_que_zero(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'valor')
    assert p is not None
    c = ''
    for v in ('0', 'R$ 0,00', '0,00', '-1'):
        c = _unica(client, alunos, **{p: v})
        if 'Valor solicitado deve ser maior que 0' in c:
            break
    assert 'Valor solicitado deve ser maior que 0' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_email_sem_arroba_ou_dominio(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'email')
    assert p is not None
    c = _unica(client, alunos, **{p: 'maria.silva'})
    assert 'E-mail inválido' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_cpf_fora_do_formato(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'cpf')
    assert p is not None
    c = _unica(client, alunos, **{p: '52998224725'})
    assert 'CPF deve estar no formato 000.000.000-00' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_cpf_com_digito_verificador_errado(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'cpf')
    assert p is not None
    c = _unica(client, alunos, **{p: '529.982.247-24'})
    assert 'CPF inválido' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_cep_fora_do_formato(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'cep')
    assert p is not None
    c = _unica(client, alunos, **{p: '05508090'})
    assert 'CEP deve estar no formato 00000-000' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_data_de_nascimento_fora_do_formato(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'nasc')
    assert p is not None
    c = _unica(client, alunos, **{p: '01021980'})
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_data_de_nascimento_inexistente(client, alunos):
    props = _props_corpo(client, alunos['url'])
    p = _acha(props, 'nasc')
    assert p is not None
    c = _unica(client, alunos, **{p: '31/02/1980'})
    assert 'Data de nascimento inválida' in c
    assert 'Encaminhe-se ao Serviço Financeiro' not in c


def test_mensagens_de_erro_acumulam(client, alunos):
    props = _props_corpo(client, alunos['url'])
    usp = _acha(props, 'usp')
    ag = _acha(props, 'agencia')
    mail = _acha(props, 'email')
    assert usp is not None and ag is not None and mail is not None
    c = _unica(client, alunos, **{usp: 'abc', ag: 'x1', mail: 'maria.silva'})
    assert 'N. USP deve conter apenas números' in c
    assert 'Número da agência deve conter apenas números' in c
    assert 'E-mail inválido' in c
