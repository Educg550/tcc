import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

ALIASES = {
    'nome': ['nome', 'nome_completo', 'nomeCompleto', 'NOME COMPLETO - SEM ABREVIAR'],
    'n_usp': ['n_usp', 'nUsp', 'numero_usp', 'num_usp', 'N. USP'],
    'programa': ['programa', 'PROGRAMA'],
    'nivel': ['nivel', 'NÍVEL'],
    'tipo_auxilio': ['tipo_auxilio', 'tipoAuxilio', 'tipo_de_auxilio', 'auxilio', 'TIPO DE AUXÍLIO'],
    'email': ['email', 'e_mail', 'E-MAIL'],
    'nome_evento': ['nome_evento', 'nome_do_evento', 'evento', 'nomeEvento', 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'],
    'periodo_evento': ['periodo_evento', 'periodo', 'periodo_do_evento', 'PERÍODO DO EVENTO, EXAME OU DEFESA'],
    'cidade_evento': ['cidade_evento', 'cidade_do_evento', 'CIDADE DO EVENTO, EXAME OU DEFESA'],
    'estado_evento': ['estado_evento', 'estado_do_evento', 'ESTADO DO EVENTO, EXAME OU DEFESA'],
    'pais_evento': ['pais_evento', 'pais_do_evento', 'pais', 'PAÍS DO EVENTO, EXAME OU DEFESA'],
    'link_evento': ['link_evento', 'link_do_evento', 'link', 'LINK DO EVENTO, EXAME OU DEFESA'],
    'valor_solicitado': ['valor_solicitado', 'valor', 'valorSolicitado', 'VALOR SOLICITADO (R$)'],
    'detalhamento': ['detalhamento', 'detalhamento_do_pedido', 'detalhamento_pedido', 'DETALHAMENTO DO PEDIDO'],
    'apresentacao': ['apresentacao', 'ira_apresentar_trabalho', 'apresentacao_trabalho', 'trabalho', 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'],
    'data_nascimento': ['data_nascimento', 'dataDeNascimento', 'nascimento', 'DATA DE NASCIMENTO'],
    'logradouro': ['logradouro', 'endereco', 'LOGRADOURO'],
    'numero': ['numero', 'NÚMERO'],
    'complemento': ['complemento', 'COMPLEMENTO'],
    'bairro': ['bairro', 'BAIRRO'],
    'cep': ['cep', 'CEP'],
    'cidade': ['cidade', 'cidade_solicitante', 'CIDADE'],
    'estado': ['estado', 'estado_solicitante', 'ESTADO'],
    'cpf': ['cpf', 'CPF (SEPARADOS POR PONTOS E TRAÇO)'],
    'rg_rnm': ['rg_rnm', 'rg', 'rnm', 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'],
    'nome_banco': ['nome_banco', 'banco', 'NOME DO BANCO'],
    'agencia': ['numero_agencia', 'agencia', 'NÚMERO DA AGÊNCIA'],
    'conta': ['numero_conta', 'conta', 'NÚMERO DA CONTA'],
}

CHAVES_ABA = [
    'aba', 'formulario', 'perfil', 'categoria', 'origem', 'papel', 'modo',
    'tipo_formulario', 'tipo_de_formulario', 'tipo_solicitante',
    'tipo_solicitacao', 'tipo_de_solicitacao',
]

OBRIGATORIOS = [campo for campo in ALIASES if campo not in ('link_evento', 'complemento', 'nivel', 'tipo_auxilio')]

REGEX_CPF = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
REGEX_CEP = re.compile(r'\d{5}-\d{3}')
REGEX_DATA = re.compile(r'\d{2}/\d{2}/\d{4}')

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


def _campo(dados, campo):
    for chave in ALIASES[campo]:
        valor = dados.get(chave)
        if valor is None:
            continue
        texto = str(valor).strip()
        if texto:
            return texto
    return ''


def _aba(dados):
    for chave in CHAVES_ABA:
        valor = str(dados.get(chave) or '').lower()
        if 'docente' in valor:
            return 'docentes'
        if 'aluno' in valor:
            return 'alunos'
    return 'alunos'


def _valor_numerico(texto):
    limpo = texto.replace('R$', '').replace(' ', '')
    if not limpo:
        return None
    if limpo.isdigit():
        return int(limpo) / 100
    limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return None


def _moeda(numero):
    texto = f'{numero:,.2f}'
    return 'R$ ' + texto.replace(',', '@').replace('.', ',').replace('@', '.')


def _digito_cpf(base, peso_inicial):
    soma = sum(int(caractere) * (peso_inicial - posicao) for posicao, caractere in enumerate(base))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def _cpf_valido(cpf):
    digitos = re.sub(r'\D', '', cpf)
    if len(digitos) != 11:
        return False
    return _digito_cpf(digitos[:9], 10) == int(digitos[9]) and _digito_cpf(digitos[:10], 11) == int(digitos[10])


def _validar(campos, docentes):
    erros = []
    obrigatorios = OBRIGATORIOS if docentes else OBRIGATORIOS + ['nivel', 'tipo_auxilio']
    if any(not campos[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if campos['n_usp'] and not campos['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if campos['agencia'] and not campos['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if campos['valor_solicitado']:
        valor = _valor_numerico(campos['valor_solicitado'])
        if valor is None or valor <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if campos['email']:
        partes = campos['email'].split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')
    if campos['cpf']:
        if not REGEX_CPF.fullmatch(campos['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(campos['cpf']):
            erros.append('CPF inválido')
    if campos['cep'] and not REGEX_CEP.fullmatch(campos['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if campos['data_nascimento']:
        if not REGEX_DATA.fullmatch(campos['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(campos['data_nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def _oficio(campos, docentes):
    c = campos
    if docentes:
        assunto = 'Verba do programa'
        programa = f'Programa: {c["programa"]}'
    else:
        assunto = c['tipo_auxilio']
        programa = f'Programa: {c["programa"]} - {c["nivel"]}'
    linhas = [
        f'Interessada(o): {c["nome"]} - {c["n_usp"]}',
        f'E-mail: {c["email"]}',
        f'Assunto: Solicitação de Auxílio Financeiro - {assunto}',
        programa,
        '',
        f'A CCP-{c["programa"]} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {c["nome_evento"]}',
        f'Período: {c["periodo_evento"]}',
        f'Local: {c["cidade_evento"]} - {c["estado_evento"]} - {c["pais_evento"]}',
    ]
    if c['link_evento']:
        linhas.append(f'Link do evento: {c["link_evento"]}')
    linhas.extend([
        f'Apresentação de trabalho: {c["apresentacao"]}',
        f'Valor solicitado: {_moeda(_valor_numerico(c["valor_solicitado"]))}',
        f'Detalhamento: {c["detalhamento"]}',
        '',
        'Endereço da(o) interessada(o)',
        f'{c["logradouro"]}, {c["numero"]}',
    ])
    if c['complemento']:
        linhas.append(f'Complemento: {c["complemento"]}')
    linhas.extend([
        f'CEP: {c["cep"]}',
        f'{c["bairro"]}, {c["cidade"]} - {c["estado"]}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {c["data_nascimento"]}',
        f'CPF: {c["cpf"]}',
        f'RG / RNM: {c["rg_rnm"]}',
        f'Banco: {c["nome_banco"]}',
        f'Agência: {c["agencia"]}',
        f'Conta: {c["conta"]}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/solicitacao')
async def receber_solicitacao(request: Request):
    dados = {}
    try:
        conteudo = await request.()
        if isinstance(conteudo, dict):
            dados = conteudo
    except Exception:
        dados = {}
    if not dados:
        formulario = await request.form()
        dados = dict(formulario)
    campos = {campo: _campo(dados, campo) for campo in ALIASES}
    docentes = _aba(dados) == 'docentes'
    erros = _validar(campos, docentes)
    if erros:
        return JSONResponse({'erros': erros})
    return JSONResponse({'oficio': _oficio(campos, docentes)})


@app.get('/')
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script_da_pagina():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
