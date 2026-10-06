'''Backend do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Recebe a solicitação, decide se é válida e devolve o ofício redigido ou as
mensagens de erro. Nada é gravado.
'''

import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')

ROTULOS_SOLICITANTE = [
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
]

ROTULOS_ENDERECO = [
    'DATA DE NASCIMENTO',
    'LOGRADOURO',
    'NÚMERO',
    'COMPLEMENTO',
    'BAIRRO',
    'CEP',
    'CIDADE',
    'ESTADO',
]

ROTULOS_PAGAMENTO = [
    'CPF (SEPARADOS POR PONTOS E TRAÇO)',
    'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)',
    'NOME DO BANCO',
    'NÚMERO DA AGÊNCIA',
    'NÚMERO DA CONTA',
]

ROTULOS = ROTULOS_SOLICITANTE + ROTULOS_ENDERECO + ROTULOS_PAGAMENTO
OPCIONAIS = {'LINK DO EVENTO, EXAME OU DEFESA', 'COMPLEMENTO'}
SO_DE_ALUNOS = {'NÍVEL', 'TIPO DE AUXÍLIO'}


def _valor_maior_que_zero(texto):
    numero = texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(numero) > 0
    except ValueError:
        return False


def _cpf_valido(cpf):
    digitos = re.sub(r'\D', '', cpf)
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    dv1 = (soma * 10) % 11 % 10
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    dv2 = (soma * 10) % 11 % 10
    return int(digitos[9]) == dv1 and int(digitos[10]) == dv2


def _data_existe(texto):
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def validar(campos, aba):
    erros = []
    obrigatorios = [
        rotulo
        for rotulo in ROTULOS
        if rotulo not in OPCIONAIS and not (aba != 'alunos' and rotulo in SO_DE_ALUNOS)
    ]
    if any(not campos[rotulo] for rotulo in obrigatorios):
        erros.append('Preencha todos os campos')
    if campos['N. USP'] and not campos['N. USP'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if campos['NÚMERO DA AGÊNCIA'] and not campos['NÚMERO DA AGÊNCIA'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    valor = campos['VALOR SOLICITADO (R$)']
    if valor and not _valor_maior_que_zero(valor):
        erros.append('Valor solicitado deve ser maior que 0')
    if campos['E-MAIL'] and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', campos['E-MAIL']):
        erros.append('E-mail inválido')
    if campos['CEP'] and not re.fullmatch(r'\d{5}-\d{3}', campos['CEP']):
        erros.append('CEP deve estar no formato 00000-000')
    cpf = campos['CPF (SEPARADOS POR PONTOS E TRAÇO)']
    if cpf and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not _cpf_valido(cpf):
        erros.append('CPF inválido')
    data = campos['DATA DE NASCIMENTO']
    if data and not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data and not _data_existe(data):
        erros.append('Data de nascimento inválida')
    return erros


def gerar_oficio(campos, aba):
    if aba == 'alunos':
        assunto = f'Solicitação de Auxílio Financeiro - {campos["TIPO DE AUXÍLIO"]}'
        programa = f'Programa: {campos["PROGRAMA"]} - {campos["NÍVEL"]}'
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f'Programa: {campos["PROGRAMA"]}'
    linhas = [
        f'Interessada(o): {campos["NOME COMPLETO - SEM ABREVIAR"]} - {campos["N. USP"]}',
        f'E-mail: {campos["E-MAIL"]}',
        assunto,
        programa,
        '',
        f'A CCP-{campos["PROGRAMA"]} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {campos["NOME DO EVENTO / BANCA DE EXAME OU DEFESA"]}',
        f'Período: {campos["PERÍODO DO EVENTO, EXAME OU DEFESA"]}',
        f'Local: {campos["CIDADE DO EVENTO, EXAME OU DEFESA"]} - {campos["ESTADO DO EVENTO, EXAME OU DEFESA"]} - {campos["PAÍS DO EVENTO, EXAME OU DEFESA"]}',
    ]
    if campos['LINK DO EVENTO, EXAME OU DEFESA']:
        linhas.append(f'Link do evento: {campos["LINK DO EVENTO, EXAME OU DEFESA"]}')
    linhas += [
        f'Apresentação de trabalho: {campos["IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"]}',
        f'Valor solicitado: {campos["VALOR SOLICITADO (R$)"]}',
        f'Detalhamento: {campos["DETALHAMENTO DO PEDIDO"]}',
        '',
        'Endereço da(o) interessada(o)',
        f'{campos["LOGRADOURO"]}, {campos["NÚMERO"]}',
    ]
    if campos['COMPLEMENTO']:
        linhas.append(f'Complemento: {campos["COMPLEMENTO"]}')
    linhas += [
        f'CEP: {campos["CEP"]}',
        f'{campos["BAIRRO"]}, {campos["CIDADE"]} - {campos["ESTADO"]}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {campos["DATA DE NASCIMENTO"]}',
        f'CPF: {campos["CPF (SEPARADOS POR PONTOS E TRAÇO)"]}',
        f'RG / RNM: {campos["RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"]}',
        f'Banco: {campos["NOME DO BANCO"]}',
        f'Agência: {campos["NÚMERO DA AGÊNCIA"]}',
        f'Conta: {campos["NÚMERO DA CONTA"]}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.get('/')
async def pagina_inicial():
    return FileResponse(RAIZ / 'index.html')


@app.post('/api/solicitacao')
async def receber_solicitacao(request: Request):
    if '' in request.headers.get('content-type', ''):
        payload = await request.()
    else:
        payload = dict(await request.form())
    aba = str(
        payload.get('aba') or payload.get('tipo') or payload.get('tipo_solicitacao') or 'alunos'
    ).strip().lower()
    campos = {rotulo: str(payload.get(rotulo) or '').strip() for rotulo in ROTULOS}
    erros = validar(campos, aba)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': gerar_oficio(campos, aba)}


app.mount('/', StaticFiles(directory=RAIZ), name='estaticos')
