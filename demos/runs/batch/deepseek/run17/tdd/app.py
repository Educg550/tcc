import re
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI()
app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')

CAMPOS_ALUNO = (
    'nome_completo',
    'n_usp',
    'programa',
    'nivel',
    'tipo_auxilio',
    'email',
    'nome_evento',
    'periodo_evento',
    'cidade_evento',
    'estado_evento',
    'pais_evento',
    'valor_solicitado',
    'detalhamento',
    'apresentacao_trabalho',
    'data_nascimento',
    'logradouro',
    'numero',
    'bairro',
    'cep',
    'cidade',
    'estado',
    'cpf',
    'rg_rnm',
    'nome_banco',
    'numero_agencia',
    'numero_conta',
)
CAMPOS_DOCENTE = tuple(c for c in CAMPOS_ALUNO if c not in ('nivel', 'tipo_auxilio'))


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html', media_type='text/html')


@app.get('/style.css')
def estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js', media_type='application/javascript')


@app.post('/api/solicitacao')
def solicitar(dados: dict = Body(...)):
    erros = validar(dados)
    if erros:
        return {'erros': erros}
    return {'erros': [], 'oficio': montar_oficio(dados)}


def texto(valor):
    return '' if valor is None else str(valor)


def validar(dados):
    aba = dados.get('aba', 'ALUNOS')
    obrigatorios = CAMPOS_ALUNO if aba == 'ALUNOS' else CAMPOS_DOCENTE
    erros = []

    if any(not texto(dados.get(campo)).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = texto(dados.get('n_usp')).strip()
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = texto(dados.get('numero_agencia')).strip()
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = texto(dados.get('valor_solicitado')).strip()
    if valor:
        numero = valor_em_reais(valor)
        if numero is None or numero <= 0:
            erros.append('Valor solicitado deve ser maior que 0')

    email = texto(dados.get('email')).strip()
    if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        erros.append('E-mail inválido')

    cpf = texto(dados.get('cpf')).strip()
    if cpf:
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = texto(dados.get('cep')).strip()
    if cep and not re.match(r'^\d{5}-\d{3}$', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = texto(dados.get('data_nascimento')).strip()
    if nascimento:
        partes = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', nascimento)
        if not partes:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(partes.group(1), partes.group(2), partes.group(3)):
            erros.append('Data de nascimento inválida')

    return erros


def valor_em_reais(valor):
    limpo = re.sub(r'[^\d,.]', '', valor).replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return None


def cpf_valido(cpf):
    digitos = re.sub(r'\D', '', cpf)
    if len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[n]) * (posicao + 1 - n) for n in range(posicao))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if esperado != int(digitos[posicao]):
            return False
    return True


def data_valida(mes, dia, ano):
    try:
        date(int(ano), int(mes), int(dia))
    except ValueError:
        return False
    return True


def montar_oficio(dados):
    nome_completo = texto(dados.get('nome_completo'))
    n_usp = texto(dados.get('n_usp'))
    email = texto(dados.get('email'))
    programa = texto(dados.get('programa'))
    nivel = texto(dados.get('nivel'))
    tipo_auxilio = texto(dados.get('tipo_auxilio'))
    nome_evento = texto(dados.get('nome_evento'))
    periodo = texto(dados.get('periodo_evento'))
    cidade_evento = texto(dados.get('cidade_evento'))
    estado_evento = texto(dados.get('estado_evento'))
    pais_evento = texto(dados.get('pais_evento'))
    link_evento = texto(dados.get('link_evento'))
    apresentacao = texto(dados.get('apresentacao_trabalho'))
    valor = texto(dados.get('valor_solicitado'))
    detalhamento = texto(dados.get('detalhamento'))
    logradouro = texto(dados.get('logradouro'))
    numero = texto(dados.get('numero'))
    complemento = texto(dados.get('complemento'))
    cep = texto(dados.get('cep'))
    bairro = texto(dados.get('bairro'))
    cidade = texto(dados.get('cidade'))
    estado = texto(dados.get('estado'))
    data_nascimento = texto(dados.get('data_nascimento'))
    cpf = texto(dados.get('cpf'))
    rg_rnm = texto(dados.get('rg_rnm'))
    nome_banco = texto(dados.get('nome_banco'))
    numero_agencia = texto(dados.get('numero_agencia'))
    numero_conta = texto(dados.get('numero_conta'))

    if dados.get('aba', 'ALUNOS') == 'DOCENTES':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'
    else:
        assunto = f'Solicitação de Auxílio Financeiro - {tipo_auxilio}'
        linha_programa = f'Programa: {programa} - {nivel}'

    linhas = [
        f'Interessada(o): {nome_completo} - {n_usp}',
        f'E-mail: {email}',
        f'Assunto: {assunto}',
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {nome_evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
        f'Link do evento: {link_evento}',
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
        f'Complemento: {complemento}',
        f'CEP: {cep}',
        f'{bairro}, {cidade} - {estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {data_nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg_rnm}',
        f'Banco: {nome_banco}',
        f'Agência: {numero_agencia}',
        f'Conta: {numero_conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]

    if not link_evento.strip():
        linhas = [linha for linha in linhas if not linha.startswith('Link do evento')]
    if not complemento.strip():
        linhas = [linha for linha in linhas if not linha.startswith('Complemento')]

    return '\n'.join(linhas)
