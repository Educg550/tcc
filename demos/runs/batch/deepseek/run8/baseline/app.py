import os
import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação do IME-USP')

ASSETS = os.path.join(BASE, 'assets')
if os.path.isdir(ASSETS):
    app.mount('/assets', StaticFiles(directory=ASSETS), name='assets')

CAMPOS_COMUNS = [
    'nome', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro',
    'cep', 'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
]

RE_DIGITOS = re.compile(r'[0-9]+')
RE_MOEDA = re.compile(r'(?:R\$\s*)?([0-9]+(?:\.[0-9]{3})*),([0-9]{2})')
RE_EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
RE_CPF = re.compile(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}')
RE_CEP = re.compile(r'[0-9]{5}-[0-9]{3}')
RE_DATA = re.compile(r'([0-9]{2})/([0-9]{2})/([0-9]{4})')


def texto(dados, nome):
    return str(dados.get(nome) or '').strip()


def apenas_digitos(valor):
    return bool(valor) and RE_DIGITOS.fullmatch(valor) is not None


def valor_em_centavos(valor):
    if RE_DIGITOS.fullmatch(valor):
        centavos = int(valor)
    else:
        achado = RE_MOEDA.fullmatch(valor)
        if not achado:
            return None
        centavos = int(achado.group(1).replace('.', '')) * 100 + int(achado.group(2))
    return centavos if centavos > 0 else None


def cpf_valido(cpf):
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(set(numeros)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(numeros[i] * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[tamanho]:
            return False
    return True


def formatar_moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def validar(aba, dados):
    erros = []
    obrigatorios = list(CAMPOS_COMUNS)
    if aba != 'docentes':
        obrigatorios += ['nivel', 'tipo_auxilio']

    if any(not texto(dados, nome) for nome in obrigatorios):
        erros.append('Preencha todos os campos')

    if texto(dados, 'n_usp') and not apenas_digitos(texto(dados, 'n_usp')):
        erros.append('N. USP deve conter apenas números')

    if texto(dados, 'agencia') and not apenas_digitos(texto(dados, 'agencia')):
        erros.append('Número da agência deve conter apenas números')

    if texto(dados, 'valor') and valor_em_centavos(texto(dados, 'valor')) is None:
        erros.append('Valor solicitado deve ser maior que 0')

    if texto(dados, 'email') and not RE_EMAIL.fullmatch(texto(dados, 'email')):
        erros.append('E-mail inválido')

    cpf = texto(dados, 'cpf')
    if cpf:
        if not RE_CPF.fullmatch(cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = texto(dados, 'cep')
    if cep and not RE_CEP.fullmatch(cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = texto(dados, 'data_nascimento')
    if nascimento:
        achado = RE_DATA.fullmatch(nascimento)
        if not achado:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                date(int(achado.group(3)), int(achado.group(2)), int(achado.group(1)))
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def gerar_oficio(aba, dados):
    def c(nome):
        return texto(dados, nome)

    linhas = [
        'Interessada(o): ' + c('nome') + ' - ' + c('n_usp'),
        'E-mail: ' + c('email'),
    ]

    if aba == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: ' + c('programa'))
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - ' + c('tipo_auxilio'))
        linhas.append('Programa: ' + c('programa') + ' - ' + c('nivel'))

    linhas += [
        '',
        'A CCP-' + c('programa') + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + c('nome_evento'),
        'Período: ' + c('periodo'),
        'Local: ' + c('cidade_evento') + ' - ' + c('estado_evento') + ' - ' + c('pais_evento'),
    ]

    if c('link_evento'):
        linhas.append('Link do evento: ' + c('link_evento'))

    linhas.append('Apresentação de trabalho: ' + c('apresentacao'))
    linhas.append('Valor solicitado: ' + formatar_moeda(valor_em_centavos(c('valor'))))
    linhas.append('Detalhamento: ' + c('detalhamento'))

    linhas += [
        '',
        'Endereço da(o) interessada(o)',
        c('logradouro') + ', ' + c('numero'),
    ]

    if c('complemento'):
        linhas.append('Complemento: ' + c('complemento'))

    linhas += [
        'CEP: ' + c('cep'),
        c('bairro') + ', ' + c('cidade') + ' - ' + c('estado'),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + c('data_nascimento'),
        'CPF: ' + c('cpf'),
        'RG / RNM: ' + c('rg'),
        'Banco: ' + c('banco'),
        'Agência: ' + c('agencia'),
        'Conta: ' + c('conta'),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]

    return '\n'.join(linhas)


@app.get('/')
def pagina_inicial():
    return FileResponse(os.path.join(BASE, 'index.html'))


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(os.path.join(BASE, 'style.css'), media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(os.path.join(BASE, 'app.js'), media_type='application/javascript')


@app.post('/api/solicitacao')
async def solicitar(request: Request):
    if 'application/json' in request.headers.get('content-type', ''):
        dados = await request.json()
    else:
        dados = dict(await request.form())

    aba = str(dados.get('aba') or 'alunos').strip().lower()
    if aba not in ('alunos', 'docentes'):
        aba = 'alunos'

    erros = validar(aba, dados)
    if erros:
        return JSONResponse({'erros': erros, 'oficio': None})
    return JSONResponse({'erros': [], 'oficio': gerar_oficio(aba, dados)})
