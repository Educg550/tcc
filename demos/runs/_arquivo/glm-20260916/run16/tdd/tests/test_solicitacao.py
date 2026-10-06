import 
import re
import unicodedata

import pytest

VALOR = 'VALOR SOLICITADO (R$)'

DADOS = {
    'NOME COMPLETO - SEM ABREVIAR': 'Maria Souza Silva',
    'N. USP': '1234567',
    'PROGRAMA': 'Ciência da Computação',
    'NÍVEL': 'Doutorado',
    'TIPO DE AUXÍLIO': 'Participação em evento',
    'E-MAIL': 'maria.silva@usp.br',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA': 'SBBD 2025',
    'PERÍODO DO EVENTO, EXAME OU DEFESA': 'de 29 de setembro a 2 de outubro de 2025',
    'CIDADE DO EVENTO, EXAME OU DEFESA': 'Rio de Janeiro',
    'ESTADO DO EVENTO, EXAME OU DEFESA': 'RJ',
    'PAÍS DO EVENTO, EXAME OU DEFESA': 'Brasil',
    'LINK DO EVENTO, EXAME OU DEFESA': 'https://sbbd.org.br',
    VALOR: 'R$ 1.500,00',
    'DETALHAMENTO DO PEDIDO': 'Inscrição no evento e passagem aérea.',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?': 'Pôster',
    'DATA DE NASCIMENTO': '01/02/1980',
    'LOGRADOURO': 'Rua do Anfiteatro',
    'NÚMERO': '181',
    'COMPLEMENTO': 'Sala 222',
    'BAIRRO': 'Cidade Universitária',
    'CEP': '05508-090',
    'CIDADE': 'São Paulo',
    'ESTADO': 'SP',
    'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-09',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)': '12.345.678-9',
    'NOME DO BANCO': 'Banco do Brasil',
    'NÚMERO DA AGÊNCIA': '1234',
    'NÚMERO DA CONTA': '98765-4',
}

TRECHOS_DO_OFICIO = [
    'Interessada(o): Maria Souza Silva - 1234567',
    'E-mail: maria.silva@usp.br',
    'Assunto: Solicitação de Auxílio Financeiro - Participação em evento',
    'Programa: Ciência da Computação - Doutorado',
    'A CCP-Ciência da Computação aprovou',
    'Dados do evento',
    'Evento: SBBD 2025',
    'Período: de 29 de setembro a 2 de outubro de 2025',
    'Local: Rio de Janeiro - RJ - Brasil',
    'Link do evento: https://sbbd.org.br',
    'Apresentação de trabalho: Pôster',
    'Valor solicitado: R$ 1.500,00',
    'Detalhamento: Inscrição no evento e passagem aérea.',
    'Endereço da(o) interessada(o)',
    'Rua do Anfiteatro, 181',
    'Complemento: Sala 222',
    'CEP: 05508-090',
    'Cidade Universitária, São Paulo - SP',
    'Dados para pagamento',
    'Data de nascimento: 01/02/1980',
    'CPF: 123.456.789-09',
    'RG / RNM: 12.345.678-9',
    'Banco: Banco do Brasil',
    'Agência: 1234',
    'Conta: 98765-4',
    'Encaminhe-se ao Serviço Financeiro para providências.',
]

ALIASES = {
    'nusp': 'N. USP',
    'numusp': 'N. USP',
    'numerousp': 'N. USP',
    'numerodenusp': 'N. USP',
    'codigousp': 'N. USP',
    'nomecompleto': 'NOME COMPLETO - SEM ABREVIAR',
    'nomedosolicitante': 'NOME COMPLETO - SEM ABREVIAR',
    'solicitante': 'NOME COMPLETO - SEM ABREVIAR',
    'nome': 'NOME COMPLETO - SEM ABREVIAR',
    'tipodeauxilio': 'TIPO DE AUXÍLIO',
    'auxilio': 'TIPO DE AUXÍLIO',
    'nomedoevento': 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'nomeevento': 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'evento': 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'periododoevento': 'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'periodo': 'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'valorsolicitado': VALOR,
    'valor': VALOR,
    'linkdoevento': 'LINK DO EVENTO, EXAME OU DEFESA',
    'link': 'LINK DO EVENTO, EXAME OU DEFESA',
    'detalhamento': 'DETALHAMENTO DO PEDIDO',
    'datadenascimento': 'DATA DE NASCIMENTO',
    'datanascimento': 'DATA DE NASCIMENTO',
    'nascimento': 'DATA DE NASCIMENTO',
    'endereco': 'LOGRADOURO',
    'rua': 'LOGRADOURO',
    'cidadeevento': 'CIDADE DO EVENTO, EXAME OU DEFESA',
    'estadoevento': 'ESTADO DO EVENTO, EXAME OU DEFESA',
    'paisdoevento': 'PAÍS DO EVENTO, EXAME OU DEFESA',
    'paisevento': 'PAÍS DO EVENTO, EXAME OU DEFESA',
    'cpfseparadosporpontosetraco': 'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'rgrnm': 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'rg': 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'rnm': 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'nomedobanco': 'NOME DO BANCO',
    'nomebanco': 'NOME DO BANCO',
    'banco': 'NOME DO BANCO',
    'numerodaagencia': 'NÚMERO DA AGÊNCIA',
    'numeroagencia': 'NÚMERO DA AGÊNCIA',
    'numagencia': 'NÚMERO DA AGÊNCIA',
    'agencia': 'NÚMERO DA AGÊNCIA',
    'numerodaconta': 'NÚMERO DA CONTA',
    'numeroconta': 'NÚMERO DA CONTA',
    'numconta': 'NÚMERO DA CONTA',
    'conta': 'NÚMERO DA CONTA',
    'iraapresentartrabalho': 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'apresentacaodetrabalho': 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'apresentacao': 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'trabalho': 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
}


def _norm(texto):
    texto = unicodedata.normalize('NFD', texto)
    sem_acento = ''.join(letra for letra in texto if not unicodedata.combining(letra))
    return re.sub('[^a-z0-9]', '', sem_acento.lower())


def _rotulo_da_propriedade(nome):
    norm = _norm(nome)
    for rotulo in DADOS:
        if _norm(rotulo) == norm:
            return rotulo
    for chave, rotulo in sorted(ALIASES.items(), key=lambda item: -len(item[0])):
        if norm == chave or norm.startswith(chave):
            return rotulo
    prefixos = [rotulo for rotulo in DADOS if _norm(rotulo).startswith(norm)]
    if len(prefixos) == 1:
        return prefixos[0]
    contidos = [rotulo for rotulo in DADOS if norm in _norm(rotulo)]
    if len(contidos) == 1:
        return contidos[0]
    return None


def _campo_da_aba(nome):
    norm = _norm(nome)
    pistas = ('aba', 'tiposolicitante', 'tipodesolicitante', 'tipousuario', 'tipodeformulario')
    return (any(pista in norm for pista in pistas)
            or norm in ('formulario', 'form', 'perfil', 'origem', 'papel')
            or ('aluno' in norm and 'docente' in norm))


def _propriedades_do_modelo(especificacao, esquema):
    if '$ref' in esquema:
        nome = esquema['$ref'].rsplit('/', 1)[-1]
        modelos = (especificacao.get('components') or {}).get('schemas') or {}
        return (modelos.get(nome) or {}).get('properties') or {}
    if esquema.get('type') == 'object':
        return esquema.get('properties') or {}
    return {}


def _rota_de_envio(client):
    try:
        especificacao = client.get('/openapi.').()
    except ValueError:
        especificacao = {}
    rotas = []
    for caminho, metodos in (especificacao.get('paths') or {}).items():
        post = metodos.get('post') or {}
        conteudos = (post.get('requestBody') or {}).get('content') or {}
        tipo = ('application/' if 'application/' in conteudos
                else next(iter(conteudos), 'application/'))
        esquema = conteudos.get(tipo, {}).get('schema') or {}
        rotas.append((caminho, tipo, _propriedades_do_modelo(especificacao, esquema)))
    if not rotas:
        for caminho in ('/api/solicitacao', '/solicitacao', '/api/solicitar', '/solicitar',
                        '/api/auxilio', '/auxilio', '/enviar', '/api/enviar',
                        '/api/solicitacoes', '/solicitacoes', '/submit', '/'):
            resposta = client.post(caminho, ={})
            if resposta.status_code not in (404, 405):
                return caminho, 'application/', {}
        pytest.fail('backend não expõe rota para envio da solicitação')

    def preferencia(item):
        caminho = item[0]
        pistas = ('solicit', 'auxil', 'form', 'envi')
        return (not any(pista in caminho for pista in pistas), caminho)

    return sorted(rotas, key=preferencia)[0]


def _valor_de_enum(esquema, aba):
    valores = esquema.get('enum')
    if not valores:
        for parte in esquema.get('allOf') or []:
            valores = parte.get('enum')
            if valores:
                break
    if not valores:
        return None
    alvo = _norm(aba)
    for valor in valores:
        norm = _norm(str(valor))
        if norm == alvo or alvo.startswith(norm):
            return valor
    return valores[0]


def _valor_para_esquema(texto, esquema):
    digitos = re.sub('[^0-9]', '', texto) or '0'
    tipo = (esquema or {}).get('type')
    if tipo == 'integer':
        return int(digitos)
    if tipo == 'number':
        return int(digitos) / 100
    return texto


def _valor_em_digitos(esquema):
    tipo = (esquema or {}).get('type')
    if tipo == 'integer':
        return 150000
    if tipo == 'number':
        return 1500.0
    return '150000'


def _tentativas(payload, propriedades, campo_aba, aba):
    corpos = [payload]
    if campo_aba:
        formas = [aba, aba.capitalize(), aba.lower(),
                  aba[:-1], aba[:-1].capitalize(), aba[:-1].lower()]
        membro = _valor_de_enum(propriedades.get(campo_aba) or {}, aba)
        if membro is not None:
            formas.insert(0, membro)
        for forma in formas:
            corpos.append({**payload, campo_aba: forma})
    chaves = set(propriedades) | {'aba'}
    corpos.append({chave: valor for chave, valor in payload.items() if chave in chaves})
    referencias = [nome for nome, esquema in propriedades.items()
                   if isinstance(esquema, dict) and '$ref' in esquema]
    if len(propriedades) == 1 and referencias:
        interno = {chave: valor for chave, valor in payload.items() if chave != referencias[0]}
        corpos.append({referencias[0]: interno})
    unicos = []
    for corpo in corpos:
        if corpo not in unicos:
            unicos.append(corpo)
    return unicos


def _montar(client, dados, aba):
    caminho, tipo, propriedades = _rota_de_envio(client)
    payload = dict(dados)
    payload['aba'] = aba
    campo_aba = None
    campo_valor = None
    for nome, esquema in propriedades.items():
        if _campo_da_aba(nome):
            campo_aba = nome
            payload[nome] = aba
            continue
        rotulo = _rotulo_da_propriedade(nome)
        if rotulo is None:
            continue
        if rotulo == VALOR:
            campo_valor = nome
            payload[nome] = _valor_para_esquema(str(dados[VALOR]), esquema)
        else:
            payload[nome] = dados[rotulo]
    if campo_aba is None:
        for alternativa in ('aba', 'formulario', 'perfil'):
            payload.setdefault(alternativa, aba)
    return caminho, tipo, propriedades, payload, campo_aba, campo_valor


def _texto(resposta):
    try:
        corpo = resposta.()
    except ValueError:
        return resposta.text
    return .dumps(corpo, ensure_ascii=False)


def enviar(client, dados, aba='ALUNOS', reenviar_valor_em_digitos=True):
    caminho, tipo, propriedades, payload, campo_aba, campo_valor = _montar(client, dados, aba)

    def postar(corpo):
        if tipo == 'application/':
            return client.post(caminho, =corpo)
        return client.post(caminho, data=corpo)

    resposta = postar(payload)
    if resposta.status_code == 422:
        for corpo in _tentativas(payload, propriedades, campo_aba, aba)[1:]:
            resposta = postar(corpo)
            if resposta.status_code != 422:
                break
    texto = _texto(resposta)
    insistir = reenviar_valor_em_digitos and ('maior que 0' in texto or resposta.status_code == 422)
    if insistir:
        corpo = {**payload, VALOR: '150000'}
        if campo_valor:
            corpo[campo_valor] = _valor_em_digitos(propriedades.get(campo_valor) or {})
        resposta = postar(corpo)
    return resposta


def test_oficio_da_aba_alunos_preenchido(client):
    texto = _texto(enviar(client, DADOS, aba='ALUNOS'))
    posicoes = []
    for trecho in TRECHOS_DO_OFICIO:
        assert trecho in texto, 'faltou no ofício: ' + trecho
        posicoes.append(texto.find(trecho))
    assert posicoes == sorted(posicoes)
    assert 'Preencha todos os campos' not in texto


def test_oficio_da_aba_docentes_usa_verba_do_programa(client):
    dados = {rotulo: valor for rotulo, valor in DADOS.items()
             if rotulo not in ('NÍVEL', 'TIPO DE AUXÍLIO')}
    texto = _texto(enviar(client, dados, aba='DOCENTES'))
    assert 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa' in texto
    assert 'Programa: Ciência da Computação' in texto
    assert 'Doutorado' not in texto
    assert 'Participação em evento' not in texto
    assert 'Interessada(o): Maria Souza Silva - 1234567' in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto


def test_linhas_de_campos_opcionais_vazios_saem_do_oficio(client):
    dados = {**DADOS,
             'LINK DO EVENTO, EXAME OU DEFESA': '',
             'COMPLEMENTO': ''}
    texto = _texto(enviar(client, dados))
    assert 'Link do evento:' not in texto
    assert 'Complemento:' not in texto
    assert 'Evento: SBBD 2025' in texto
    assert 'CEP: 05508-090' in texto
    assert 'Encaminhe-se ao Serviço Financeiro para providências.' in texto


def test_todas_as_mensagens_de_erro_aparecem_juntas_no_topo(client):
    dados = {**DADOS,
             'PROGRAMA': '',
             'N. USP': '12a45',
             'NÚMERO DA AGÊNCIA': '12a4',
             VALOR: 'R$ 0,00',
             'E-MAIL': 'maria.silva.usp.br',
             'CPF (SEPARADOS POR PONTOS E TRAÇO)': '123.456.789-00'}
    texto = _texto(enviar(client, dados, reenviar_valor_em_digitos=False))
    assert 'Preencha todos os campos' in texto
    assert texto.count('Preencha todos os campos') == 1
    assert 'N. USP deve conter apenas números' in texto
    assert 'Número da agência deve conter apenas números' in texto
    assert 'Valor solicitado deve ser maior que 0' in texto
    assert 'E-mail inválido' in texto
    assert 'CPF inválido' in texto
    assert 'CPF deve estar no formato 000.000.000-00' not in texto
    assert 'Interessada(o):' not in texto


def test_mensagens_de_formato_de_cpf_cep_e_data(client):
    dados = {**DADOS,
             'CPF (SEPARADOS POR PONTOS E TRAÇO)': '1234567890',
             'CEP': '0550809',
             'DATA DE NASCIMENTO': '01021980'}
    texto = _texto(enviar(client, dados, reenviar_valor_em_digitos=False))
    assert 'CPF deve estar no formato 000.000.000-00' in texto
    assert 'CEP deve estar no formato 00000-000' in texto
    assert 'Data de nascimento deve estar no formato dd/mm/aaaa' in texto
    assert 'Interessada(o):' not in texto


def test_data_de_nascimento_com_dia_que_nao_existe(client):
    dados = {**DADOS, 'DATA DE NASCIMENTO': '31/02/1990'}
    texto = _texto(enviar(client, dados, reenviar_valor_em_digitos=False))
    assert 'Data de nascimento inválida' in texto
    assert 'deve estar no formato dd/mm/aaaa' not in texto
    assert 'Interessada(o):' not in texto


def test_data_de_nascimento_com_mes_fora_do_intervalo(client):
    dados = {**DADOS, 'DATA DE NASCIMENTO': '05/13/1990'}
    texto = _texto(enviar(client, dados, reenviar_valor_em_digitos=False))
    assert 'Data de nascimento inválida' in texto
    assert 'deve estar no formato dd/mm/aaaa' not in texto
    assert 'Interessada(o):' not in texto
