import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

app = FastAPI()

OPCIONAIS = {'LINK DO EVENTO, EXAME OU DEFESA', 'COMPLEMENTO'}

CAMPOS_DOCENTES = [
    'NOME COMPLETO - SEM ABREVIAR',
    'N. USP',
    'PROGRAMA',
    'E-MAIL',
    'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'PERÍODO DO EVENTO, EXAME OU DEFESA',
    'CIDADE DO EVENTO, EXAME OU DEFESA',
    'ESTADO DO EVENTO, EXAME OU DEFESA',
    'PAÍS DO EVENTO, EXAME OU DEFESA',
    'VALOR SOLICITADO (R$)',
    'DETALHAMENTO DO PEDIDO',
    'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
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

CAMPOS_ALUNOS = CAMPOS_DOCENTES + ['NÍVEL', 'TIPO DE AUXÍLIO']


@app.get('/')
def indice():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')


def cpf_valido(cpf):
    n = [int(d) for d in cpf if d.isdigit()]
    if len(n) != 11:
        return False
    dig1 = sum(n[i] * (10 - i) for i in range(9)) % 11
    dig1 = 0 if dig1 < 2 else 11 - dig1
    dig2 = sum(n[i] * (11 - i) for i in range(10)) % 11
    dig2 = 0 if dig2 < 2 else 11 - dig2
    return n[9] == dig1 and n[10] == dig2


def validar(dados, campos):
    erros = []
    if any(not str(dados.get(c, '')).strip() for c in campos if c not in OPCIONAIS):
        erros.append('Preencha todos os campos')

    n_usp = str(dados.get('N. USP', '')).strip()
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = str(dados.get('NÚMERO DA AGÊNCIA', '')).strip()
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = str(dados.get('VALOR SOLICITADO (R$)', '')).strip()
    digitos = ''.join(d for d in valor if d.isdigit())
    if valor and (not digitos or int(digitos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = str(dados.get('E-MAIL', '')).strip()
    if email and ('@' not in email or not email.split('@', 1)[1].strip()):
        erros.append('E-mail inválido')

    cpf = str(dados.get('CPF (SEPARADOS POR PONTOS E TRAÇO)', '')).strip()
    if cpf and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not cpf_valido(cpf):
        erros.append('CPF inválido')

    cep = str(dados.get('CEP', '')).strip()
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    data = str(dados.get('DATA DE NASCIMENTO', '')).strip()
    if data:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def montar_oficio(dados, aba):
    def g(campo):
        return str(dados.get(campo, '')).strip()

    linhas = [
        f"Interessada(o): {g('NOME COMPLETO - SEM ABREVIAR')} - {g('N. USP')}",
        f"E-mail: {g('E-MAIL')}",
    ]
    if aba == 'ALUNOS':
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {g('TIPO DE AUXÍLIO')}")
        linhas.append(f"Programa: {g('PROGRAMA')} - {g('NÍVEL')}")
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f"Programa: {g('PROGRAMA')}")
    linhas.extend([
        '',
        f"A CCP-{g('PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {g('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {g('PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {g('CIDADE DO EVENTO, EXAME OU DEFESA')} - {g('ESTADO DO EVENTO, EXAME OU DEFESA')} - {g('PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ])
    if g('LINK DO EVENTO, EXAME OU DEFESA'):
        linhas.append(f"Link do evento: {g('LINK DO EVENTO, EXAME OU DEFESA')}")
    linhas.extend([
        f"Apresentação de trabalho: {g('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {g('VALOR SOLICITADO (R$)')}",
        f"Detalhamento: {g('DETALHAMENTO DO PEDIDO')}",
        '',
        'Endereço da(o) interessada(o)',
        f"{g('LOGRADOURO')}, {g('NÚMERO')}",
    ])
    if g('COMPLEMENTO'):
        linhas.append(f"Complemento: {g('COMPLEMENTO')}")
    linhas.extend([
        f"CEP: {g('CEP')}",
        f"{g('BAIRRO')}, {g('CIDADE')} - {g('ESTADO')}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {g('DATA DE NASCIMENTO')}",
        f"CPF: {g('CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"RG / RNM: {g('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"Banco: {g('NOME DO BANCO')}",
        f"Agência: {g('NÚMERO DA AGÊNCIA')}",
        f"Conta: {g('NÚMERO DA CONTA')}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/solicitacao')
async def solicitacao(request: Request):
    dados = await request.()
    aba = dados.get('aba')
    campos = CAMPOS_DOCENTES if aba == 'DOCENTES' else CAMPOS_ALUNOS
    erros = validar(dados, campos)
    if erros:
        return JSONResponse({'erros': erros}, status_code=400)
    return {'oficio': montar_oficio(dados, aba)}
