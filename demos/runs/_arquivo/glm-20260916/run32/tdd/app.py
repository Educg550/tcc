import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

RAIZ = Path(__file__).resolve().parent

app = FastAPI()

OBRIGATORIOS_COMUNS = (
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
)

CPF_NO_FORMATO = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
CEP_NO_FORMATO = re.compile(r'\d{5}-\d{3}')
DATA_NO_FORMATO = re.compile(r'\d{2}/\d{2}/\d{4}')


@app.get('/')
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html')


@app.get('/app.js')
def script_da_pagina():
    return FileResponse(RAIZ / 'app.js')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css')


@app.get('/assets/usp-logo.png')
def logotipo():
    return FileResponse(RAIZ / 'assets' / 'usp-logo.png')


@app.post('/solicitacao')
async def receber_solicitacao(request: Request):
    campos = await request.()
    erros = _validar(campos)
    return {'erros': erros, 'oficio': None if erros else _montar_oficio(campos)}


def _texto(campos, rotulo):
    return str(campos.get(rotulo) or '').strip()


def _validar(campos):
    erros = []

    obrigatorios = list(OBRIGATORIOS_COMUNS)
    if campos.get('aba') == 'ALUNOS':
        obrigatorios += ['NÍVEL', 'TIPO DE AUXÍLIO']
    if any(_texto(campos, rotulo) == '' for rotulo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _texto(campos, 'N. USP')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = _texto(campos, 'NÚMERO DA AGÊNCIA')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = _texto(campos, 'VALOR SOLICITADO (R$)')
    if valor and (not valor.isdigit() or int(valor) == 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = _texto(campos, 'E-MAIL')
    if email and ('@' not in email or not email.split('@', 1)[1]):
        erros.append('E-mail inválido')

    cpf = _texto(campos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf and not CPF_NO_FORMATO.fullmatch(cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not _cpf_valido(cpf):
        erros.append('CPF inválido')

    cep = _texto(campos, 'CEP')
    if cep and not CEP_NO_FORMATO.fullmatch(cep):
        erros.append('CEP deve estar no formato 00000-000')

    data = _texto(campos, 'DATA DE NASCIMENTO')
    if data and not DATA_NO_FORMATO.fullmatch(data):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data:
        try:
            datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def _cpf_valido(cpf):
    numero = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(numero) != 11:
        return False

    def digito_verificador(pesos):
        resto = sum(digito * peso for digito, peso in zip(numero, pesos)) % 11
        return 0 if resto < 2 else 11 - resto

    return numero[9] == digito_verificador(range(10, 1, -1)) and numero[10] == digito_verificador(range(11, 2, -1))


def _moeda(digitos_do_valor):
    centavos = int(digitos_do_valor)
    reais = f'{centavos // 100:,}'.replace(',', '.')
    return f'R$ {reais},{centavos % 100:02d}'


def _montar_oficio(campos):
    def texto(rotulo):
        return _texto(campos, rotulo)

    if campos.get('aba') == 'DOCENTES':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f'Programa: {texto("PROGRAMA")}'
    else:
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {texto("TIPO DE AUXÍLIO")}'
        programa = f'Programa: {texto("PROGRAMA")} - {texto("NÍVEL")}'

    linhas = [
        f'Interessada(o): {texto("NOME COMPLETO - SEM ABREVIAR")} - {texto("N. USP")}',
        f'E-mail: {texto("E-MAIL")}',
        assunto,
        programa,
        '',
        f'A CCP-{texto("PROGRAMA")} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {texto("NOME DO EVENTO / BANCA DE EXAME OU DEFESA")}',
        f'Período: {texto("PERÍODO DO EVENTO, EXAME OU DEFESA")}',
        'Local: ' + ' - '.join([
            texto('CIDADE DO EVENTO, EXAME OU DEFESA'),
            texto('ESTADO DO EVENTO, EXAME OU DEFESA'),
            texto('PAÍS DO EVENTO, EXAME OU DEFESA'),
        ]),
    ]
    link = texto('LINK DO EVENTO, EXAME OU DEFESA')
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f'Apresentação de trabalho: {texto("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?")}',
        f'Valor solicitado: {_moeda(texto("VALOR SOLICITADO (R$)"))}',
        f'Detalhamento: {texto("DETALHAMENTO DO PEDIDO")}',
        '',
        'Endereço da(o) interessada(o)',
        f'{texto("LOGRADOURO")}, {texto("NÚMERO")}',
    ]
    complemento = texto('COMPLEMENTO')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f'CEP: {texto("CEP")}',
        f'{texto("BAIRRO")}, {texto("CIDADE")} - {texto("ESTADO")}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {texto("DATA DE NASCIMENTO")}',
        f'CPF: {texto("CPF (SEPARADOS POR PONTOS E TRAÇO)")}',
        f'RG / RNM: {texto("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)")}',
        f'Banco: {texto("NOME DO BANCO")}',
        f'Agência: {texto("NÚMERO DA AGÊNCIA")}',
        f'Conta: {texto("NÚMERO DA CONTA")}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)
