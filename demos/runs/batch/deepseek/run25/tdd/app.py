from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()


def apenas_digitos(texto):
    return ''.join(c for c in texto if c.isdigit())


def email_valido(email):
    if '@' not in email:
        return False
    local, _, dominio = email.partition('@')
    return bool(local) and '.' in dominio and ' ' not in dominio


def cpf_formato(cpf):
    return (
        len(cpf) == 14
        and cpf[3] == '.'
        and cpf[7] == '.'
        and cpf[11] == '-'
        and len(apenas_digitos(cpf)) == 11
    )


def cpf_valido(cpf):
    numeros = [int(c) for c in apenas_digitos(cpf)]
    for peso in (10, 11):
        soma = sum(numeros[i] * (peso - i) for i in range(peso - 1))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != numeros[peso - 1]:
            return False
    return True


def formatar_moeda(digitos):
    reais, centavos = divmod(int(digitos), 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{centavos:02d}'


OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
    'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
]


def validar(dados, aba):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba != 'docentes':
        obrigatorios += ['nivel', 'tipo_auxilio']
    if any(not str(dados.get(campo, '')).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = str(dados.get('n_usp', ''))
    if n_usp.strip() and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = str(dados.get('agencia', ''))
    if agencia.strip() and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = str(dados.get('valor', ''))
    digitos_valor = apenas_digitos(valor)
    if valor.strip() and (not digitos_valor or int(digitos_valor) <= 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = str(dados.get('email', ''))
    if email.strip() and not email_valido(email):
        erros.append('E-mail inválido')

    cpf = str(dados.get('cpf', ''))
    if cpf.strip():
        if not cpf_formato(cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = str(dados.get('cep', ''))
    if cep.strip() and not (len(cep) == 9 and cep[5] == '-' and apenas_digitos(cep) == cep[:5] + cep[6:]):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = str(dados.get('data_nascimento', ''))
    if nascimento.strip():
        formato_ok = (
            len(nascimento) == 10
            and nascimento[2] == '/'
            and nascimento[5] == '/'
            and apenas_digitos(nascimento) == nascimento[:2] + nascimento[3:5] + nascimento[6:]
        )
        if not formato_ok:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                date(int(nascimento[6:]), int(nascimento[3:5]), int(nascimento[0:2]))
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def gerar_oficio(dados, aba):
    def campo(nome):
        return str(dados.get(nome, '')).strip()

    programa = campo('programa')
    linhas = [
        'Interessada(o): ' + campo('nome_completo') + ' - ' + campo('n_usp'),
        'E-mail: ' + campo('email'),
    ]
    if aba == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: ' + programa)
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - ' + campo('tipo_auxilio'))
        linhas.append('Programa: ' + programa + ' - ' + campo('nivel'))
    linhas.append('')
    linhas.append('A CCP-' + programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a')
    linhas.append('interessada(o) acima, conforme segue:')
    linhas.append('')
    linhas.append('Dados do evento')
    linhas.append('Evento: ' + campo('nome_evento'))
    linhas.append('Período: ' + campo('periodo'))
    linhas.append('Local: ' + campo('cidade_evento') + ' - ' + campo('estado_evento') + ' - ' + campo('pais_evento'))
    if campo('link_evento'):
        linhas.append('Link do evento: ' + campo('link_evento'))
    linhas.append('Apresentação de trabalho: ' + campo('apresentacao'))
    linhas.append('Valor solicitado: ' + formatar_moeda(apenas_digitos(campo('valor'))))
    linhas.append('Detalhamento: ' + campo('detalhamento'))
    linhas.append('')
    linhas.append('Endereço da(o) interessada(o)')
    linhas.append(campo('logradouro') + ', ' + campo('numero'))
    if campo('complemento'):
        linhas.append('Complemento: ' + campo('complemento'))
    linhas.append('CEP: ' + campo('cep'))
    linhas.append(campo('bairro') + ', ' + campo('cidade') + ' - ' + campo('estado'))
    linhas.append('')
    linhas.append('Dados para pagamento')
    linhas.append('Data de nascimento: ' + campo('data_nascimento'))
    linhas.append('CPF: ' + campo('cpf'))
    linhas.append('RG / RNM: ' + campo('rg'))
    linhas.append('Banco: ' + campo('banco'))
    linhas.append('Agência: ' + campo('agencia'))
    linhas.append('Conta: ' + campo('conta'))
    linhas.append('')
    linhas.append('Encaminhe-se ao Serviço Financeiro para providências.')
    return '\n'.join(linhas)


async def solicitar(request: Request):
    dados = await request.json()
    aba = dados.get('aba') or 'alunos'
    erros = validar(dados, aba)
    if erros:
        return PlainTextResponse('\n'.join(erros), status_code=400)
    return PlainTextResponse(gerar_oficio(dados, aba))


for caminho in (
    '/api/alunos', '/api/docentes', '/alunos', '/docentes',
    '/api/solicitacao', '/solicitacao', '/api/solicitar', '/solicitar',
    '/api/enviar', '/enviar',
):
    app.add_api_route(caminho, solicitar, methods=['POST'])


@app.get('/')
def pagina():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js')


app.mount('/static', StaticFiles(directory=BASE), name='static')
