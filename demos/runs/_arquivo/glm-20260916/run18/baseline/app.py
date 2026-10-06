import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo_evento',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor_solicitado', 'detalhamento',
    'apresentacao_trabalho', 'data_nascimento', 'logradouro', 'numero', 'bairro',
    'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'conta',
]


def texto(dados, chave):
    valor = dados.get(chave)
    return valor.strip() if isinstance(valor, str) else ''


def digitos(valor):
    return re.sub(r'\D', '', valor)


def cpf_valido(cpf):
    d = [int(c) for c in digitos(cpf)]
    dv1 = (sum(d[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(d[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return d[9] == dv1 and d[10] == dv2


def data_valida(data):
    try:
        datetime.strptime(data, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def email_valido(email):
    partes = email.split('@')
    return len(partes) == 2 and partes[0] != '' and partes[1] != ''


def formatar_valor(valor):
    centavos = int(digitos(valor) or '0')
    reais = f'{centavos // 100:,}'.replace(',', '.')
    return f'R$ {reais},{centavos % 100:02d}'


def validar(dados, tipo):
    obrigatorios = OBRIGATORIOS + (['nivel', 'tipo_auxilio'] if tipo == 'alunos' else [])
    erros = []
    if any(texto(dados, chave) == '' for chave in obrigatorios):
        erros.append('Preencha todos os campos')
    n_usp = texto(dados, 'n_usp')
    if n_usp and not re.fullmatch(r'[0-9]+', n_usp):
        erros.append('N. USP deve conter apenas números')
    agencia = texto(dados, 'agencia')
    if agencia and not re.fullmatch(r'[0-9]+', agencia):
        erros.append('Número da agência deve conter apenas números')
    valor = texto(dados, 'valor_solicitado')
    if valor and int(digitos(valor) or '0') <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    email = texto(dados, 'email')
    if email and not email_valido(email):
        erros.append('E-mail inválido')
    cpf = texto(dados, 'cpf')
    cpf_no_formato = bool(re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf))
    if cpf and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')
    cep = texto(dados, 'cep')
    if cep and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')
    data_nascimento = texto(dados, 'data_nascimento')
    data_no_formato = bool(re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', data_nascimento))
    if data_nascimento and not data_no_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_no_formato and not cpf_valido(cpf):
        erros.append('CPF inválido')
    if data_no_formato and not data_valida(data_nascimento):
        erros.append('Data de nascimento inválida')
    return erros


def redigir_oficio(dados, tipo):
    def v(chave):
        return texto(dados, chave)

    nome = v('nome_completo')
    n_usp = v('n_usp')
    programa = v('programa')
    email = v('email')
    nivel = v('nivel')
    tipo_auxilio = v('tipo_auxilio')
    nome_evento = v('nome_evento')
    periodo = v('periodo_evento')
    cidade_evento = v('cidade_evento')
    estado_evento = v('estado_evento')
    pais_evento = v('pais_evento')
    link = v('link_evento')
    apresentacao = v('apresentacao_trabalho')
    valor = formatar_valor(v('valor_solicitado'))
    detalhamento = v('detalhamento')
    logradouro = v('logradouro')
    numero = v('numero')
    complemento = v('complemento')
    bairro = v('bairro')
    cidade = v('cidade')
    estado = v('estado')
    data_nascimento = v('data_nascimento')
    cpf = v('cpf')
    rg_rnm = v('rg_rnm')
    banco = v('nome_banco')
    agencia = v('agencia')
    conta = v('conta')

    if tipo == 'alunos':
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}'
        linha_programa = f'Programa: {programa} - {nivel}'
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'

    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {nome_evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ]
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f'CEP: {cep}',
        f'{bairro}, {cidade} - {estado}',
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
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
@app.post('/solicitacao')
async def receber_solicitacao(request: Request):
    try:
        dados = await request.()
    except ValueError:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    tipo = dados.get('tipo')
    if tipo not in ('alunos', 'docentes'):
        tipo = 'alunos'
    erros = validar(dados, tipo)
    if erros:
        return {'status': 'erro', 'erros': erros, 'oficio': None}
    return {'status': 'ok', 'erros': [], 'oficio': redigir_oficio(dados, tipo)}


app.mount('/', StaticFiles(directory=BASE, html=True), name='raiz')
