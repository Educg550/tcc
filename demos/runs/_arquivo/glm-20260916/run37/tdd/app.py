import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')
app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')

OPCIONAIS = {'LINK DO EVENTO, EXAME OU DEFESA', 'COMPLEMENTO'}
SOMENTE_ALUNOS = {'NÍVEL', 'TIPO DE AUXÍLIO'}
TODOS_OS_CAMPOS = [
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


def texto(dados, chave):
    return str(dados.get(chave, '')).strip()


def cpf_valido(cpf):
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(numeros) != 11:
        return False
    digito1 = (sum(numeros[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    digito2 = (sum(numeros[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return numeros[9] == digito1 and numeros[10] == digito2


def validar(dados):
    mensagens = []
    obrigatorios = [
        campo
        for campo in TODOS_OS_CAMPOS
        if campo not in OPCIONAIS
        and not (dados.get('ABA') != 'ALUNOS' and campo in SOMENTE_ALUNOS)
    ]
    if any(not texto(dados, campo) for campo in obrigatorios):
        mensagens.append('Preencha todos os campos')

    numero_usp = texto(dados, 'N. USP')
    if numero_usp and not numero_usp.isdigit():
        mensagens.append('N. USP deve conter apenas números')

    agencia = texto(dados, 'NÚMERO DA AGÊNCIA')
    if agencia and not agencia.isdigit():
        mensagens.append('Número da agência deve conter apenas números')

    solicitado = texto(dados, 'VALOR SOLICITADO (R$)')
    if solicitado:
        centavos = re.sub('[^0-9]', '', solicitado)
        if not centavos or int(centavos) == 0:
            mensagens.append('Valor solicitado deve ser maior que 0')

    email = texto(dados, 'E-MAIL')
    if email:
        partes = email.split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            mensagens.append('E-mail inválido')

    cpf = texto(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf and not re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf):
        mensagens.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not cpf_valido(cpf):
        mensagens.append('CPF inválido')

    cep = texto(dados, 'CEP')
    if cep and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', cep):
        mensagens.append('CEP deve estar no formato 00000-000')

    nascimento = texto(dados, 'DATA DE NASCIMENTO')
    if nascimento:
        if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', nascimento):
            mensagens.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                mensagens.append('Data de nascimento inválida')

    return mensagens


def montar_oficio(dados):
    docentes = dados.get('ABA') == 'DOCENTES'
    assunto = (
        'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        if docentes
        else f"Assunto: Solicitação de Auxílio Financeiro - {texto(dados, 'TIPO DE AUXÍLIO')}"
    )
    programa = (
        f"Programa: {texto(dados, 'PROGRAMA')}"
        if docentes
        else f"Programa: {texto(dados, 'PROGRAMA')} - {texto(dados, 'NÍVEL')}"
    )
    linhas = [
        f"Interessada(o): {texto(dados, 'NOME COMPLETO - SEM ABREVIAR')} - {texto(dados, 'N. USP')}",
        f"E-mail: {texto(dados, 'E-MAIL')}",
        assunto,
        programa,
        '',
        f"A CCP-{texto(dados, 'PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {texto(dados, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {texto(dados, 'PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        'Local: {} - {} - {}'.format(
            texto(dados, 'CIDADE DO EVENTO, EXAME OU DEFESA'),
            texto(dados, 'ESTADO DO EVENTO, EXAME OU DEFESA'),
            texto(dados, 'PAÍS DO EVENTO, EXAME OU DEFESA'),
        ),
    ]
    link = texto(dados, 'LINK DO EVENTO, EXAME OU DEFESA')
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend([
        f"Apresentação de trabalho: {texto(dados, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {texto(dados, 'VALOR SOLICITADO (R$)')}",
        f"Detalhamento: {texto(dados, 'DETALHAMENTO DO PEDIDO')}",
        '',
        'Endereço da(o) interessada(o)',
        f"{texto(dados, 'LOGRADOURO')}, {texto(dados, 'NÚMERO')}",
    ])
    complemento = texto(dados, 'COMPLEMENTO')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend([
        f"CEP: {texto(dados, 'CEP')}",
        '{}, {} - {}'.format(texto(dados, 'BAIRRO'), texto(dados, 'CIDADE'), texto(dados, 'ESTADO')),
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
    ])
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def receber_solicitacao(dados: dict):
    erros = validar(dados)
    if erros:
        return {'erros': erros}
    return {'oficio': montar_oficio(dados)}


@app.get('/', include_in_schema=False)
def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css', include_in_schema=False)
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js', include_in_schema=False)
def roteiro():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')
