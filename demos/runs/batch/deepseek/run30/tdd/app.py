'''Formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.'''

import json
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()


@app.get('/')
@app.get('/index.html')
def pagina_inicial():
    return FileResponse(os.path.join(BASE, 'index.html'))


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(os.path.join(BASE, 'style.css'), media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(os.path.join(BASE, 'app.js'), media_type='application/javascript')


app.mount('/assets', StaticFiles(directory=os.path.join(BASE, 'assets')), name='assets')


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
CAMPOS_DE_ALUNOS = ['NÍVEL', 'TIPO DE AUXÍLIO']


async def _ler_campos(request):
    if 'application/json' in request.headers.get('content-type', ''):
        return await request.json()
    formulario = await request.form()
    return dict(formulario)


def _campo(campos, chave):
    return (campos.get(chave) or '').strip()


def _resposta(conteudo, status_code=200):
    return Response(content=json.dumps(conteudo, ensure_ascii=False),
                    media_type='application/json', status_code=status_code)


def _valor_numerico(texto):
    limpo = texto.strip().replace('R$', '').replace(' ', '')
    if not limpo:
        return None
    if ',' in limpo:
        limpo = limpo.replace('.', '').replace(',', '.')
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        return None
    if valor <= 0:
        return None
    return valor


def _formata_moeda(valor):
    valor = valor.quantize(Decimal('0.01'))
    formatado = f'{valor:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    return 'R$ ' + formatado


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r'[^0-9]', '', cpf)]
    for i in range(2):
        soma = sum(digitos[j] * ((10 + i) - j) for j in range(9 + i))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if esperado != digitos[9 + i]:
            return False
    return True


def _validar(campos, alunos):
    obrigatorios = CAMPOS_OBRIGATORIOS + (CAMPOS_DE_ALUNOS if alunos else [])
    erros = []
    if any(not _campo(campos, chave) for chave in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _campo(campos, 'N. USP')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = _campo(campos, 'NÚMERO DA AGÊNCIA')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    email = _campo(campos, 'E-MAIL')
    if email and not re.match(r'^[^@ ]+@[^@ ]+[.][^@ ]+$', email):
        erros.append('E-mail inválido')

    valor = _campo(campos, 'VALOR SOLICITADO (R$)')
    if valor and _valor_numerico(valor) is None:
        erros.append('Valor solicitado deve ser maior que 0')

    cpf = _campo(campos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf:
        if not re.match(r'^[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}$', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = _campo(campos, 'CEP')
    if cep and not re.match(r'^[0-9]{5}-[0-9]{3}$', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = _campo(campos, 'DATA DE NASCIMENTO')
    if nascimento:
        if not re.match(r'^[0-9]{2}/[0-9]{2}/[0-9]{4}$', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def _gerar_oficio(campos, alunos):
    programa = _campo(campos, 'PROGRAMA')
    if alunos:
        assunto = 'Solicitação de Auxílio Financeiro - ' + _campo(campos, 'TIPO DE AUXÍLIO')
        linha_programa = 'Programa: ' + programa + ' - ' + _campo(campos, 'NÍVEL')
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + programa

    linhas = [
        'Interessada(o): ' + _campo(campos, 'NOME COMPLETO - SEM ABREVIAR') + ' - ' + _campo(campos, 'N. USP'),
        'E-mail: ' + _campo(campos, 'E-MAIL'),
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-' + programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + _campo(campos, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'),
        'Período: ' + _campo(campos, 'PERÍODO DO EVENTO, EXAME OU DEFESA'),
        'Local: ' + _campo(campos, 'CIDADE DO EVENTO, EXAME OU DEFESA') + ' - ' + _campo(campos, 'ESTADO DO EVENTO, EXAME OU DEFESA') + ' - ' + _campo(campos, 'PAÍS DO EVENTO, EXAME OU DEFESA'),
    ]

    link = _campo(campos, 'LINK DO EVENTO, EXAME OU DEFESA')
    if link:
        linhas.append('Link do evento: ' + link)

    linhas.append('Apresentação de trabalho: ' + _campo(campos, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'))
    linhas.append('Valor solicitado: ' + _formata_moeda(_valor_numerico(_campo(campos, 'VALOR SOLICITADO (R$)'))))
    linhas.append('Detalhamento: ' + _campo(campos, 'DETALHAMENTO DO PEDIDO'))
    linhas.append('')
    linhas.append('Endereço da(o) interessada(o)')
    linhas.append(_campo(campos, 'LOGRADOURO') + ', ' + _campo(campos, 'NÚMERO'))

    complemento = _campo(campos, 'COMPLEMENTO')
    if complemento:
        linhas.append('Complemento: ' + complemento)

    linhas.append('CEP: ' + _campo(campos, 'CEP'))
    linhas.append(_campo(campos, 'BAIRRO') + ', ' + _campo(campos, 'CIDADE') + ' - ' + _campo(campos, 'ESTADO'))
    linhas.append('')
    linhas.append('Dados para pagamento')
    linhas.append('Data de nascimento: ' + _campo(campos, 'DATA DE NASCIMENTO'))
    linhas.append('CPF: ' + _campo(campos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)'))
    linhas.append('RG / RNM: ' + _campo(campos, 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'))
    linhas.append('Banco: ' + _campo(campos, 'NOME DO BANCO'))
    linhas.append('Agência: ' + _campo(campos, 'NÚMERO DA AGÊNCIA'))
    linhas.append('Conta: ' + _campo(campos, 'NÚMERO DA CONTA'))
    linhas.append('')
    linhas.append('Encaminhe-se ao Serviço Financeiro para providências.')
    return '\n'.join(linhas)


def _responder(campos, alunos):
    erros = _validar(campos, alunos)
    if erros:
        return _resposta({'erros': erros}, status_code=400)
    return _resposta({'oficio': _gerar_oficio(campos, alunos)})


@app.post('/alunos')
async def solicitar_alunos(request: Request):
    return _responder(await _ler_campos(request), True)


@app.post('/docentes')
async def solicitar_docentes(request: Request):
    return _responder(await _ler_campos(request), False)
