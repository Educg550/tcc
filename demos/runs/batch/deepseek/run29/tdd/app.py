import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')


@app.get('/')
def pagina_inicial():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(BASE / 'style.css')


@app.get('/app.js')
def comportamento():
    return FileResponse(BASE / 'app.js')


OBRIGATORIOS = (
    'nome_completo', 'n_usp', 'programa', 'email',
    'nome_evento', 'periodo', 'cidade_evento', 'estado_evento', 'pais_evento',
    'valor_solicitado', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
)

OBRIGATORIOS_ALUNOS = ('nivel', 'tipo_auxilio')

CPF_FORMATO = '[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}'
CEP_FORMATO = '[0-9]{5}-[0-9]{3}'
DATA_FORMATO = '[0-9]{2}/[0-9]{2}/[0-9]{4}'
EMAIL_FORMATO = '[^@ ]+@[^@ ]+[.][^@ ]+'


def campo(dados, nome):
    return str(dados.get(nome) or '').strip()


def cpf_valido(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    primeiro = sum(numeros[i] * (10 - i) for i in range(9))
    digito1 = 0 if primeiro % 11 < 2 else 11 - primeiro % 11
    segundo = sum(numeros[i] * (11 - i) for i in range(10))
    digito2 = 0 if segundo % 11 < 2 else 11 - segundo % 11
    return numeros[9] == digito1 and numeros[10] == digito2


def data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split('/'))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(dados):
    obrigatorios = list(OBRIGATORIOS)
    if campo(dados, 'aba') == 'ALUNOS':
        obrigatorios += OBRIGATORIOS_ALUNOS

    erros = []
    if any(not campo(dados, nome) for nome in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = campo(dados, 'n_usp')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = campo(dados, 'agencia')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor_solicitado = campo(dados, 'valor_solicitado')
    if valor_solicitado:
        digitos = re.sub('[^0-9]', '', valor_solicitado)
        if not digitos or int(digitos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')

    email = campo(dados, 'email')
    if email and not re.fullmatch(EMAIL_FORMATO, email):
        erros.append('E-mail inválido')

    cpf = campo(dados, 'cpf')
    cpf_no_formato = bool(re.fullmatch(CPF_FORMATO, cpf))
    if cpf and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')

    cep = campo(dados, 'cep')
    if cep and not re.fullmatch(CEP_FORMATO, cep):
        erros.append('CEP deve estar no formato 00000-000')

    data_nascimento = campo(dados, 'data_nascimento')
    data_no_formato = bool(re.fullmatch(DATA_FORMATO, data_nascimento))
    if data_nascimento and not data_no_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append('CPF inválido')

    if data_no_formato and not data_valida(data_nascimento):
        erros.append('Data de nascimento inválida')

    return erros


def formata_valor(texto):
    digitos = re.sub('[^0-9]', '', texto or '')
    if not digitos:
        return texto
    reais, resto = divmod(int(digitos), 100)
    inteiro = f'{reais:,}'.replace(',', '.')
    return f'R$ {inteiro},{resto:02d}'


def gerar_oficio(dados):
    nome_completo = campo(dados, 'nome_completo')
    n_usp = campo(dados, 'n_usp')
    email = campo(dados, 'email')
    programa = campo(dados, 'programa')
    nivel = campo(dados, 'nivel')
    tipo_auxilio = campo(dados, 'tipo_auxilio')
    nome_evento = campo(dados, 'nome_evento')
    periodo = campo(dados, 'periodo')
    cidade_evento = campo(dados, 'cidade_evento')
    estado_evento = campo(dados, 'estado_evento')
    pais_evento = campo(dados, 'pais_evento')
    link_evento = campo(dados, 'link_evento')
    valor_solicitado = formata_valor(campo(dados, 'valor_solicitado'))
    detalhamento = campo(dados, 'detalhamento')
    apresentacao = campo(dados, 'apresentacao')
    data_nascimento = campo(dados, 'data_nascimento')
    logradouro = campo(dados, 'logradouro')
    numero = campo(dados, 'numero')
    complemento = campo(dados, 'complemento')
    bairro = campo(dados, 'bairro')
    cep = campo(dados, 'cep')
    cidade = campo(dados, 'cidade')
    estado = campo(dados, 'estado')
    cpf = campo(dados, 'cpf')
    rg = campo(dados, 'rg')
    banco = campo(dados, 'banco')
    agencia = campo(dados, 'agencia')
    conta = campo(dados, 'conta')

    linhas = [
        f'Interessada(o): {nome_completo} - {n_usp}',
        f'E-mail: {email}',
    ]

    if campo(dados, 'aba') == 'DOCENTES':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {programa}')
    else:
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}')
        linhas.append(f'Programa: {programa} - {nivel}')

    linhas += [
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {nome_evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
    ]

    if link_evento:
        linhas.append(f'Link do evento: {link_evento}')

    linhas += [
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor_solicitado}',
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
        f'Data de nascimento: {data_nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg}',
        f'Banco: {banco}',
        f'Agência: {agencia}',
        f'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]

    return chr(10).join(linhas)


@app.post('/solicitar')
def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return PlainTextResponse(chr(10).join(erros), status_code=400)
    return PlainTextResponse(gerar_oficio(dados))
