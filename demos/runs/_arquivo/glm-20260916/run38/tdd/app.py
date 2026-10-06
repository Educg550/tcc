import pathlib
import re
from datetime import datetime

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = pathlib.Path(__file__).resolve().parent

OBRIGATORIOS = [
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

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


def _valor(dados, campo):
    return str(dados.get(campo) or '').strip()


def _moeda(centavos):
    inteiro = f'{centavos // 100:,}'.replace(',', '.')
    return f'R$ {inteiro},{centavos % 100:02d}'


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r'[^0-9]', '', cpf)]
    if len(digitos) != 11:
        return False
    resto = sum(d * p for d, p in zip(digitos[:9], range(10, 1, -1))) % 11
    digito1 = 0 if resto < 2 else 11 - resto
    resto = sum(d * p for d, p in zip(digitos[:10], range(11, 1, -1))) % 11
    digito2 = 0 if resto < 2 else 11 - resto
    return digitos[9] == digito1 and digitos[10] == digito2


def _validar(dados, docente):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if not docente:
        obrigatorios += ['NÍVEL', 'TIPO DE AUXÍLIO']
    if any(not _valor(dados, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _valor(dados, 'N. USP')
    if n_usp and not re.fullmatch(r'[0-9]+', n_usp):
        erros.append('N. USP deve conter apenas números')

    agencia = _valor(dados, 'NÚMERO DA AGÊNCIA')
    if agencia and not re.fullmatch(r'[0-9]+', agencia):
        erros.append('Número da agência deve conter apenas números')

    valor = _valor(dados, 'VALOR SOLICITADO (R$)')
    if valor and int(re.sub(r'[^0-9]', '', valor) or 0) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    email = _valor(dados, 'E-MAIL')
    if email and ('@' not in email or not email.split('@', 1)[1].strip()):
        erros.append('E-mail inválido')

    cpf = _valor(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    if cpf:
        if not re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = _valor(dados, 'CEP')
    if cep and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = _valor(dados, 'DATA DE NASCIMENTO')
    if nascimento:
        if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def _oficio(dados, docente):
    programa = _valor(dados, 'PROGRAMA')
    nome = _valor(dados, 'NOME COMPLETO - SEM ABREVIAR')
    n_usp = _valor(dados, 'N. USP')
    email = _valor(dados, 'E-MAIL')
    evento = _valor(dados, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA')
    periodo = _valor(dados, 'PERÍODO DO EVENTO, EXAME OU DEFESA')
    cidade_evento = _valor(dados, 'CIDADE DO EVENTO, EXAME OU DEFESA')
    estado_evento = _valor(dados, 'ESTADO DO EVENTO, EXAME OU DEFESA')
    pais_evento = _valor(dados, 'PAÍS DO EVENTO, EXAME OU DEFESA')
    link = _valor(dados, 'LINK DO EVENTO, EXAME OU DEFESA')
    apresentacao = _valor(dados, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')
    centavos = int(re.sub(r'[^0-9]', '', _valor(dados, 'VALOR SOLICITADO (R$)')) or 0)
    detalhamento = _valor(dados, 'DETALHAMENTO DO PEDIDO')
    logradouro = _valor(dados, 'LOGRADOURO')
    numero = _valor(dados, 'NÚMERO')
    complemento = _valor(dados, 'COMPLEMENTO')
    bairro = _valor(dados, 'BAIRRO')
    cep = _valor(dados, 'CEP')
    cidade = _valor(dados, 'CIDADE')
    estado = _valor(dados, 'ESTADO')
    nascimento = _valor(dados, 'DATA DE NASCIMENTO')
    cpf = _valor(dados, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')
    rg = _valor(dados, 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')
    banco = _valor(dados, 'NOME DO BANCO')
    agencia = _valor(dados, 'NÚMERO DA AGÊNCIA')
    conta = _valor(dados, 'NÚMERO DA CONTA')

    if docente:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'
    else:
        assunto = 'Solicitação de Auxílio Financeiro - ' + _valor(dados, 'TIPO DE AUXÍLIO')
        linha_programa = f'Programa: {programa} - {_valor(dados, "NÍVEL")}'

    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        f'Assunto: {assunto}',
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
    linhas.append(f'Apresentação de trabalho: {apresentacao}')
    linhas.append(f'Valor solicitado: {_moeda(centavos)}')
    linhas.append(f'Detalhamento: {detalhamento}')
    linhas += [
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


@app.post('/solicitar')
def solicitar(dados: dict = Body(...)):
    docente = not _valor(dados, 'NÍVEL') and not _valor(dados, 'TIPO DE AUXÍLIO')
    erros = _validar(dados, docente)
    if erros:
        return {'sucesso': False, 'erros': erros}
    return {'sucesso': True, 'oficio': _oficio(dados, docente)}


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html', media_type='text/html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def roteiro():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
