import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

CAMPOS_OBRIGATORIOS = [
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
CAMPOS_OBRIGATORIOS_ALUNOS = CAMPOS_OBRIGATORIOS + ['NÍVEL', 'TIPO DE AUXÍLIO']


def campo(dados, nome):
    return str(dados.get(nome, '')).strip()


def centavos_do_valor(texto):
    digitos = re.sub(r'\D', '', texto)
    return int(digitos) if digitos else 0


def valor_formatado(texto):
    total = centavos_do_valor(texto)
    reais, centavos = divmod(total, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{centavos:02d}'


def cpf_valido(cpf):
    numeros = [int(digito) for digito in cpf if digito.isdigit()]
    if len(numeros) != 11:
        return False
    digito1 = sum(n * p for n, p in zip(numeros[:9], range(10, 1, -1))) % 11
    digito1 = 0 if digito1 < 2 else 11 - digito1
    digito2 = sum(n * p for n, p in zip(numeros[:10], range(11, 1, -1))) % 11
    digito2 = 0 if digito2 < 2 else 11 - digito2
    return numeros[9] == digito1 and numeros[10] == digito2


def validar(dados):
    erros = []
    obrigatorios = (
        CAMPOS_OBRIGATORIOS
        if campo(dados, 'ABA') == 'DOCENTES'
        else CAMPOS_OBRIGATORIOS_ALUNOS
    )
    if any(not campo(dados, nome) for nome in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = campo(dados, 'N. USP')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = campo(dados, 'NÚMERO DA AGÊNCIA')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = campo(dados, 'VALOR SOLICITADO (R$)')
    if valor and centavos_do_valor(valor) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    email = campo(dados, 'E-MAIL')
    partes = email.split('@')
    if email and (len(partes) != 2 or not partes[0] or not partes[1]):
        erros.append('E-mail inválido')

    cpf = campo(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not cpf_valido(cpf):
        erros.append('CPF inválido')

    cep = campo(dados, 'CEP')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = campo(dados, 'DATA DE NASCIMENTO')
    if nascimento and not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif nascimento:
        try:
            datetime.strptime(nascimento, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def montar_oficio(dados):
    docente = campo(dados, 'ABA') == 'DOCENTES'
    assunto = (
        'Solicitação de Auxílio Financeiro - Verba do programa'
        if docente
        else f"Solicitação de Auxílio Financeiro - {campo(dados, 'TIPO DE AUXÍLIO')}"
    )
    programa = (
        campo(dados, 'PROGRAMA')
        if docente
        else f"{campo(dados, 'PROGRAMA')} - {campo(dados, 'NÍVEL')}"
    )

    linhas = [
        f"Interessada(o): {campo(dados, 'NOME COMPLETO - SEM ABREVIAR')} - {campo(dados, 'N. USP')}",
        f"E-mail: {campo(dados, 'E-MAIL')}",
        f'Assunto: {assunto}',
        f'Programa: {programa}',
        '',
        f"A CCP-{campo(dados, 'PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {campo(dados, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {campo(dados, 'PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {campo(dados, 'CIDADE DO EVENTO, EXAME OU DEFESA')} - {campo(dados, 'ESTADO DO EVENTO, EXAME OU DEFESA')} - {campo(dados, 'PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ]
    link = campo(dados, 'LINK DO EVENTO, EXAME OU DEFESA')
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend(
        [
            f"Apresentação de trabalho: {campo(dados, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
            f"Valor solicitado: {valor_formatado(campo(dados, 'VALOR SOLICITADO (R$)'))}",
            f"Detalhamento: {campo(dados, 'DETALHAMENTO DO PEDIDO')}",
            '',
            'Endereço da(o) interessada(o)',
            f"{campo(dados, 'LOGRADOURO')}, {campo(dados, 'NÚMERO')}",
        ]
    )
    complemento = campo(dados, 'COMPLEMENTO')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend(
        [
            f"CEP: {campo(dados, 'CEP')}",
            f"{campo(dados, 'BAIRRO')}, {campo(dados, 'CIDADE')} - {campo(dados, 'ESTADO')}",
            '',
            'Dados para pagamento',
            f"Data de nascimento: {campo(dados, 'DATA DE NASCIMENTO')}",
            f"CPF: {campo(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
            f"RG / RNM: {campo(dados, 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
            f"Banco: {campo(dados, 'NOME DO BANCO')}",
            f"Agência: {campo(dados, 'NÚMERO DA AGÊNCIA')}",
            f"Conta: {campo(dados, 'NÚMERO DA CONTA')}",
            '',
            'Encaminhe-se ao Serviço Financeiro para providências.',
        ]
    )
    return '\n'.join(linhas)


@app.post('/solicitacao')
def receber_solicitacao(dados: dict):
    erros = validar(dados)
    return {'erros': erros, 'oficio': None if erros else montar_oficio(dados)}


@app.get('/')
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html', media_type='text/html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script_da_pagina():
    return FileResponse(RAIZ / 'app.js', media_type='application/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
