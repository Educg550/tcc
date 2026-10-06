import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

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

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
    campos: dict[str, str]


def valor(campos: dict[str, str], rotulo: str) -> str:
    return (campos.get(rotulo) or '').strip()


def cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    if len(digitos) != 11:
        return False
    resto1 = sum(digito * peso for digito, peso in zip(digitos[:9], range(10, 1, -1))) % 11
    dv1 = 0 if resto1 < 2 else 11 - resto1
    resto2 = sum(digito * peso for digito, peso in zip(digitos[:10], range(11, 1, -1))) % 11
    dv2 = 0 if resto2 < 2 else 11 - resto2
    return digitos[9] == dv1 and digitos[10] == dv2


def formatar_valor(digitos: str) -> str:
    reais, centavos = divmod(int(digitos), 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{centavos:02d}'


def validar(aba: str, campos: dict[str, str]) -> list[str]:
    erros = []
    obrigatorios = CAMPOS_OBRIGATORIOS_ALUNOS if aba == 'alunos' else CAMPOS_OBRIGATORIOS
    if any(not valor(campos, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = valor(campos, 'N. USP')
    if n_usp and not re.fullmatch(r'\d+', n_usp):
        erros.append('N. USP deve conter apenas números')

    agencia = valor(campos, 'NÚMERO DA AGÊNCIA')
    if agencia and not re.fullmatch(r'\d+', agencia):
        erros.append('Número da agência deve conter apenas números')

    solicitado = valor(campos, 'VALOR SOLICITADO (R$)')
    if solicitado and (not re.fullmatch(r'\d+', solicitado) or int(solicitado) == 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = valor(campos, 'E-MAIL')
    if email:
        partes = email.split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')

    cpf = valor(campos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = valor(campos, 'CEP')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = valor(campos, 'DATA DE NASCIMENTO')
    if nascimento:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            dia, mes, ano = (int(parte) for parte in nascimento.split('/'))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def gerar_oficio(aba: str, campos: dict[str, str]) -> str:
    nome = valor(campos, 'NOME COMPLETO - SEM ABREVIAR')
    n_usp = valor(campos, 'N. USP')
    email = valor(campos, 'E-MAIL')
    programa = valor(campos, 'PROGRAMA')
    evento = valor(campos, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA')
    periodo = valor(campos, 'PERÍODO DO EVENTO, EXAME OU DEFESA')
    cidade_evento = valor(campos, 'CIDADE DO EVENTO, EXAME OU DEFESA')
    estado_evento = valor(campos, 'ESTADO DO EVENTO, EXAME OU DEFESA')
    pais_evento = valor(campos, 'PAÍS DO EVENTO, EXAME OU DEFESA')
    link = valor(campos, 'LINK DO EVENTO, EXAME OU DEFESA')
    apresentacao = valor(campos, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')
    solicitado = formatar_valor(valor(campos, 'VALOR SOLICITADO (R$)'))
    detalhamento = valor(campos, 'DETALHAMENTO DO PEDIDO')
    logradouro = valor(campos, 'LOGRADOURO')
    numero = valor(campos, 'NÚMERO')
    complemento = valor(campos, 'COMPLEMENTO')
    cep = valor(campos, 'CEP')
    bairro = valor(campos, 'BAIRRO')
    cidade = valor(campos, 'CIDADE')
    estado = valor(campos, 'ESTADO')
    nascimento = valor(campos, 'DATA DE NASCIMENTO')
    cpf = valor(campos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    rg = valor(campos, 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')
    banco = valor(campos, 'NOME DO BANCO')
    agencia = valor(campos, 'NÚMERO DA AGÊNCIA')
    conta = valor(campos, 'NÚMERO DA CONTA')

    if aba == 'alunos':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - ' + valor(campos, 'TIPO DE AUXÍLIO')
        linha_programa = 'Programa: ' + programa + ' - ' + valor(campos, 'NÍVEL')
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + programa

    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {solicitado}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ]
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f'CEP: {cep}',
        f'{bairro}, {cidade} - {estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg}',
        f'Banco: {banco}',
        f'Agência: {agencia}',
        f'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitacao')
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao.aba, solicitacao.campos)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    return {'oficio': gerar_oficio(solicitacao.aba, solicitacao.campos)}


@app.get('/')
def pagina_inicial():
    return FileResponse(BASE_DIR / 'index.html', media_type='text/html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(BASE_DIR / 'style.css', media_type='text/css')


@app.get('/app.js')
def script_js():
    return FileResponse(BASE_DIR / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=BASE_DIR / 'assets'), name='assets')
