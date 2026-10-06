import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount('/assets', StaticFiles(directory=BASE / 'assets', check_dir=False), name='assets')


@app.get('/')
def pagina():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js')


def _t(dados, chave):
    valor = dados.get(chave)
    return valor.strip() if isinstance(valor, str) else ''


def _valor_reais(texto):
    texto = texto.strip()
    if not texto:
        return None
    if texto.isdecimal():
        return int(texto) / 100
    limpo = re.sub(r'[^\d,]', '', texto).replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return None


def _formata_reais(valor):
    inteiro, centavos = f'{valor:.2f}'.split('.')
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return 'R$ ' + '.'.join(grupos) + ',' + centavos


def _cpf_valido(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(numeros[i] * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10) % 11 % 10 != numeros[tamanho]:
            return False
    return True


def _data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split('/'))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


OBRIGATORIOS = [
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais', 'valor', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro',
    'cep', 'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
]


def _validar(dados, aba):
    erros = []
    obrigatorios = OBRIGATORIOS + (['nivel', 'tipo_auxilio'] if aba == 'alunos' else [])
    if any(not _t(dados, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _t(dados, 'n_usp')
    if n_usp and not n_usp.isdecimal():
        erros.append('N. USP deve conter apenas números')

    agencia = _t(dados, 'agencia')
    if agencia and not agencia.isdecimal():
        erros.append('Número da agência deve conter apenas números')

    email = _t(dados, 'email')
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        erros.append('E-mail inválido')

    valor = _t(dados, 'valor')
    if valor:
        reais = _valor_reais(valor)
        if reais is None or reais <= 0:
            erros.append('Valor solicitado deve ser maior que 0')

    cpf = _t(dados, 'cpf')
    if cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = _t(dados, 'cep')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = _t(dados, 'data_nascimento')
    if nascimento:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not _data_valida(nascimento):
            erros.append('Data de nascimento inválida')

    return erros


def _gerar_oficio(dados, aba):
    g = lambda campo: _t(dados, campo)
    if aba == 'docentes':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f"Programa: {g('programa')}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {g('tipo_auxilio')}"
        programa = f"Programa: {g('programa')} - {g('nivel')}"

    linhas = [
        f"Interessada(o): {g('nome')} - {g('n_usp')}",
        f"E-mail: {g('email')}",
        f'Assunto: {assunto}',
        programa,
        '',
        f"A CCP-{g('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {g('evento')}",
        f"Período: {g('periodo')}",
        f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais')}",
    ]
    if g('link'):
        linhas.append(f"Link do evento: {g('link')}")
    linhas += [
        f"Apresentação de trabalho: {g('apresentacao')}",
        f"Valor solicitado: {_formata_reais(_valor_reais(g('valor')))}",
        f"Detalhamento: {g('detalhamento')}",
        '',
        'Endereço da(o) interessada(o)',
        f"{g('logradouro')}, {g('numero')}",
    ]
    if g('complemento'):
        linhas.append(f"Complemento: {g('complemento')}")
    linhas += [
        f"CEP: {g('cep')}",
        f"{g('bairro')}, {g('cidade')} - {g('estado')}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {g('data_nascimento')}",
        f"CPF: {g('cpf')}",
        f"RG / RNM: {g('rg')}",
        f"Banco: {g('banco')}",
        f"Agência: {g('agencia')}",
        f"Conta: {g('conta')}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitar')
async def solicitar(request: Request):
    if 'application/json' in request.headers.get('content-type', ''):
        dados = await request.json()
    else:
        dados = dict(await request.form())
    aba = _t(dados, 'aba').lower() or 'alunos'
    if aba not in ('alunos', 'docentes'):
        aba = 'alunos'
    erros = _validar(dados, aba)
    if erros:
        return {'erros': erros}
    return {'oficio': _gerar_oficio(dados, aba)}
