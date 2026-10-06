import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
RAIZ = Path(__file__).resolve().parent

CAMPOS = [
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
OPCIONAIS = {'LINK DO EVENTO, EXAME OU DEFESA', 'COMPLEMENTO'}
CAMPOS_ALUNOS = CAMPOS
CAMPOS_DOCENTES = [c for c in CAMPOS if c not in ('NÍVEL', 'TIPO DE AUXÍLIO')]


def texto(dados, campo):
    return str(dados.get(campo) or '').strip()


def validar(dados, campos):
    erros = []
    if any(not texto(dados, c) for c in campos if c not in OPCIONAIS):
        erros.append('Preencha todos os campos')

    n_usp = texto(dados, 'N. USP')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = texto(dados, 'NÚMERO DA AGÊNCIA')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = texto(dados, 'VALOR SOLICITADO (R$)')
    if valor:
        numero = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
        try:
            positivo = float(numero) > 0
        except ValueError:
            positivo = False
        if not positivo:
            erros.append('Valor solicitado deve ser maior que 0')

    email = texto(dados, 'E-MAIL')
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+', email):
        erros.append('E-mail inválido')

    cpf = texto(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        else:
            digitos = [int(c) for c in re.sub(r'\D', '', cpf)]
            d1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
            d2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
            if [d1, d2] != digitos[9:]:
                erros.append('CPF inválido')

    cep = texto(dados, 'CEP')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = texto(dados, 'DATA DE NASCIMENTO')
    if nascimento:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                dia, mes, ano = (int(p) for p in nascimento.split('/'))
                date(ano, mes, dia)
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def gerar_oficio(dados, aba):
    programa = texto(dados, 'PROGRAMA')
    linhas = [
        f"Interessada(o): {texto(dados, 'NOME COMPLETO - SEM ABREVIAR')} - {texto(dados, 'N. USP')}",
        f"E-mail: {texto(dados, 'E-MAIL')}",
    ]
    if aba == 'DOCENTES':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {programa}')
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {texto(dados, 'TIPO DE AUXÍLIO')}")
        linhas.append(f"Programa: {programa} - {texto(dados, 'NÍVEL')}")
    linhas += [
        '',
        'A CCP-' + programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {texto(dados, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {texto(dados, 'PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {texto(dados, 'CIDADE DO EVENTO, EXAME OU DEFESA')} - {texto(dados, 'ESTADO DO EVENTO, EXAME OU DEFESA')} - {texto(dados, 'PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ]
    link = texto(dados, 'LINK DO EVENTO, EXAME OU DEFESA')
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f"Apresentação de trabalho: {texto(dados, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {texto(dados, 'VALOR SOLICITADO (R$)')}",
        f"Detalhamento: {texto(dados, 'DETALHAMENTO DO PEDIDO')}",
        '',
        'Endereço da(o) interessada(o)',
        f"{texto(dados, 'LOGRADOURO')}, {texto(dados, 'NÚMERO')}",
    ]
    complemento = texto(dados, 'COMPLEMENTO')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f"CEP: {texto(dados, 'CEP')}",
        f"{texto(dados, 'BAIRRO')}, {texto(dados, 'CIDADE')} - {texto(dados, 'ESTADO')}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {texto(dados, 'DATA DE NASCIMENTO')}",
        f"CPF: {texto(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"RG / RNM: {texto(dados, 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"Banco: {texto(dados, 'NOME DO BANCO')}",
        f"Agência: {texto(dados, 'NÚMERO DA AGÊNCIA')}",
        f"Conta: {texto(dados, 'NÚMERO DA CONTA')}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


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


@app.post('/api/solicitacao')
async def solicitacao(request: Request):
    dados = await request.()
    aba = dados.get('aba', 'ALUNOS')
    campos = CAMPOS_DOCENTES if aba == 'DOCENTES' else CAMPOS_ALUNOS
    erros = validar(dados, campos)
    if erros:
        return JSONResponse({'errors': erros})
    return JSONResponse({'oficio': gerar_oficio(dados, aba)})
