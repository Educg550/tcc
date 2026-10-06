import datetime
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

OBRIGATORIOS_COMUNS = [
    'nome', 'nusp', 'programa', 'email', 'evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor',
    'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
    'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm',
    'banco', 'agencia', 'conta',
]


@app.get('/')
def index():
    return FileResponse('index.html')


@app.get('/style.css')
def estilo():
    return FileResponse('style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse('app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory='assets'), name='assets')


@app.post('/api/solicitacao')
def solicitacao(payload: dict):
    formulario = payload.get('formulario', '')
    campos_brutos = payload.get('campos')
    if not isinstance(campos_brutos, dict):
        campos_brutos = {c: v for c, v in payload.items() if c != 'formulario'}
    campos = {c: str(v).strip() for c, v in campos_brutos.items() if v is not None}
    erros = validar(campos, formulario)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': gerar_oficio(campos, formulario)}


def validar(campos, formulario):
    erros = []
    obrigatorios = OBRIGATORIOS_COMUNS
    if formulario == 'alunos':
        obrigatorios = obrigatorios + ['nivel', 'tipo_auxilio']
    if any(not campos.get(campo, '') for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    nusp = campos.get('nusp', '')
    if nusp and not nusp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = campos.get('agencia', '')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = campos.get('valor', '')
    digitos_valor = ''.join(c for c in valor if c.isdigit())
    if not digitos_valor or int(digitos_valor) == 0:
        erros.append('Valor solicitado deve ser maior que 0')

    email = campos.get('email', '')
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+', email):
        erros.append('E-mail inválido')

    cpf = campos.get('cpf', '')
    cpf_formato = re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf)
    if cpf and not cpf_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')

    cep = campos.get('cep', '')
    cep_formato = re.fullmatch(r'\d{5}-\d{3}', cep)
    if cep and not cep_formato:
        erros.append('CEP deve estar no formato 00000-000')

    data = campos.get('data_nascimento', '')
    data_formato = re.fullmatch(r'\d{2}/\d{2}/\d{4}', data)
    if data and not data_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    if cpf and cpf_formato and not digitos_verificadores_cpf(cpf):
        erros.append('CPF inválido')

    if data and data_formato:
        try:
            datetime.datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def digitos_verificadores_cpf(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    soma = sum(numeros[i] * (10 - i) for i in range(9))
    dv1 = (soma * 10) % 11
    if dv1 == 10:
        dv1 = 0
    if numeros[9] != dv1:
        return False
    soma = sum(numeros[i] * (11 - i) for i in range(10))
    dv2 = (soma * 10) % 11
    if dv2 == 10:
        dv2 = 0
    return numeros[10] == dv2


def formatar_moeda(valor):
    digitos = ''.join(c for c in valor if c.isdigit())
    centavos = int(digitos) if digitos else 0
    inteiro, resto = divmod(centavos, 100)
    milhar = f'{inteiro:,}'.replace(',', '.')
    return f'R$ {milhar},{resto:02d}'


def gerar_oficio(campos, formulario):
    def g(campo):
        return campos.get(campo, '')

    if formulario == 'alunos':
        assunto = 'Solicitação de Auxílio Financeiro - ' + g('tipo_auxilio')
        programa = g('programa') + ' - ' + g('nivel')
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        programa = g('programa')

    nome = g('nome')
    nusp = g('nusp')
    email = g('email')
    ccp = g('programa')
    evento = g('evento')
    periodo = g('periodo')
    local = g('cidade_evento') + ' - ' + g('estado_evento') + ' - ' + g('pais_evento')
    link = g('link')
    apresentacao = g('apresentacao')
    valor = formatar_moeda(g('valor'))
    detalhamento = g('detalhamento')
    logradouro = g('logradouro')
    numero = g('numero')
    complemento = g('complemento')
    cep = g('cep')
    endereco = g('bairro') + ', ' + g('cidade') + ' - ' + g('estado')
    data_nascimento = g('data_nascimento')
    cpf = g('cpf')
    rg_rnm = g('rg_rnm')
    banco = g('banco')
    agencia = g('agencia')
    conta = g('conta')

    linhas = [
        f'Interessada(o): {nome} - {nusp}',
        f'E-mail: {email}',
        f'Assunto: {assunto}',
        f'Programa: {programa}',
        '',
        f'A CCP-{ccp} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {evento}',
        f'Período: {periodo}',
        f'Local: {local}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend([
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ])
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend([
        f'CEP: {cep}',
        endereco,
        '',
        'Dados para pagamento',
        f'Data de nascimento: {data_nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg_rnm}',
        f'Banco: {banco}',
        f'Agência: {agencia}',
        f'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)
