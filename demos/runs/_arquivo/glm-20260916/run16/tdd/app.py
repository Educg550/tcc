import datetime
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

NOME = 'NOME COMPLETO - SEM ABREVIAR'
NUSP = 'N. USP'
PROGRAMA = 'PROGRAMA'
NIVEL = 'NÍVEL'
TIPO = 'TIPO DE AUXÍLIO'
EMAIL = 'E-MAIL'
EVENTO = 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA'
PERIODO = 'PERÍODO DO EVENTO, EXAME OU DEFESA'
CIDADE_EVENTO = 'CIDADE DO EVENTO, EXAME OU DEFESA'
ESTADO_EVENTO = 'ESTADO DO EVENTO, EXAME OU DEFESA'
PAIS_EVENTO = 'PAÍS DO EVENTO, EXAME OU DEFESA'
LINK = 'LINK DO EVENTO, EXAME OU DEFESA'
VALOR = 'VALOR SOLICITADO (R$)'
DETALHAMENTO = 'DETALHAMENTO DO PEDIDO'
APRESENTACAO = 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?'
DATA = 'DATA DE NASCIMENTO'
LOGRADOURO = 'LOGRADOURO'
NUMERO = 'NÚMERO'
COMPLEMENTO = 'COMPLEMENTO'
BAIRRO = 'BAIRRO'
CEP = 'CEP'
CIDADE = 'CIDADE'
ESTADO = 'ESTADO'
CPF = 'CPF (SEPARADOS POR PONTOS E TRAÇO)'
RG_RNM = 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)'
BANCO = 'NOME DO BANCO'
AGENCIA = 'NÚMERO DA AGÊNCIA'
CONTA = 'NÚMERO DA CONTA'

OPCIONAIS = {LINK, COMPLEMENTO}

CAMPOS_ALUNOS = [
    NOME, NUSP, PROGRAMA, NIVEL, TIPO, EMAIL, EVENTO, PERIODO,
    CIDADE_EVENTO, ESTADO_EVENTO, PAIS_EVENTO, LINK, VALOR,
    DETALHAMENTO, APRESENTACAO, DATA, LOGRADOURO, NUMERO,
    COMPLEMENTO, BAIRRO, CEP, CIDADE, ESTADO, CPF, RG_RNM,
    BANCO, AGENCIA, CONTA,
]
CAMPOS_DOCENTES = [campo for campo in CAMPOS_ALUNOS if campo not in (NIVEL, TIPO)]

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


def texto(corpo, rotulo):
    valor = corpo.get(rotulo, '')
    return valor.strip() if isinstance(valor, str) else str(valor).strip()


def centavos(valor):
    digitos = re.sub(r'\D', '', valor)
    return int(digitos) if digitos else 0


def digito_cpf(parte, peso_inicial):
    soma = sum(d * (peso_inicial - i) for i, d in enumerate(parte))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf):
    numeros = [int(d) for d in re.sub(r'\D', '', cpf)]
    return (
        len(numeros) == 11
        and digito_cpf(numeros[:9], 10) == numeros[9]
        and digito_cpf(numeros[:10], 11) == numeros[10]
    )


def validar(corpo, aba):
    campos = CAMPOS_ALUNOS if aba == 'ALUNOS' else CAMPOS_DOCENTES
    valores = {rotulo: texto(corpo, rotulo) for rotulo in campos}
    erros = []
    if any(not valores[rotulo] for rotulo in campos if rotulo not in OPCIONAIS):
        erros.append('Preencha todos os campos')
    if valores[NUSP] and not valores[NUSP].isdigit():
        erros.append('N. USP deve conter apenas números')
    if valores[AGENCIA] and not valores[AGENCIA].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if valores[VALOR] and centavos(valores[VALOR]) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    if valores[EMAIL] and ('@' not in valores[EMAIL]
                           or not valores[EMAIL].split('@', 1)[1].strip()):
        erros.append('E-mail inválido')
    if valores[CPF]:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', valores[CPF]):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(valores[CPF]):
            erros.append('CPF inválido')
    if valores[CEP] and not re.fullmatch(r'\d{5}-\d{3}', valores[CEP]):
        erros.append('CEP deve estar no formato 00000-000')
    if valores[DATA]:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', valores[DATA]):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            dia, mes, ano = (int(parte) for parte in valores[DATA].split('/'))
            try:
                datetime.date(ano, mes, dia)
            except ValueError:
                erros.append('Data de nascimento inválida')
    return valores, erros


def moeda(valor):
    total = centavos(valor)
    reais, resto = divmod(total, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def montar_oficio(valores, aba):
    if aba == 'ALUNOS':
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {valores[TIPO]}'
        linha_programa = f'Programa: {valores[PROGRAMA]} - {valores[NIVEL]}'
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {valores[PROGRAMA]}'
    linhas = [
        f'Interessada(o): {valores[NOME]} - {valores[NUSP]}',
        f'E-mail: {valores[EMAIL]}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{valores[PROGRAMA]} aprovou na data de hoje, a solicitação de auxílio '
        'financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {valores[EVENTO]}',
        f'Período: {valores[PERIODO]}',
        f'Local: {valores[CIDADE_EVENTO]} - {valores[ESTADO_EVENTO]} - {valores[PAIS_EVENTO]}',
    ]
    if valores[LINK]:
        linhas.append(f'Link do evento: {valores[LINK]}')
    linhas.extend([
        f'Apresentação de trabalho: {valores[APRESENTACAO]}',
        f'Valor solicitado: {moeda(valores[VALOR])}',
        f'Detalhamento: {valores[DETALHAMENTO]}',
        '',
        'Endereço da(o) interessada(o)',
        f'{valores[LOGRADOURO]}, {valores[NUMERO]}',
    ])
    if valores[COMPLEMENTO]:
        linhas.append(f'Complemento: {valores[COMPLEMENTO]}')
    linhas.extend([
        f'CEP: {valores[CEP]}',
        f'{valores[BAIRRO]}, {valores[CIDADE]} - {valores[ESTADO]}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {valores[DATA]}',
        f'CPF: {valores[CPF]}',
        f'RG / RNM: {valores[RG_RNM]}',
        f'Banco: {valores[BANCO]}',
        f'Agência: {valores[AGENCIA]}',
        f'Conta: {valores[CONTA]}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/solicitacao')
async def receber_solicitacao(request: Request):
    try:
        corpo = await request.()
    except ValueError:
        corpo = {}
    if not isinstance(corpo, dict):
        corpo = {}
    aba = 'DOCENTES' if str(corpo.get('aba', '')).strip().upper() == 'DOCENTES' else 'ALUNOS'
    valores, erros = validar(corpo, aba)
    if erros:
        return JSONResponse({'erros': erros})
    return JSONResponse({'oficio': montar_oficio(valores, aba)})


RAIZ = Path(__file__).resolve().parent
app.mount('/', StaticFiles(directory=RAIZ, html=True), name='static')
