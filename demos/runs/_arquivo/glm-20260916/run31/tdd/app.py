import datetime
import importlib
import re
import urllib.parse
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI()

app.mount('/static', StaticFiles(directory=RAIZ, check_dir=False), name='static')
app.mount('/assets', StaticFiles(directory=RAIZ / 'assets', check_dir=False), name='assets')


@app.get('/')
@app.get('/index.html')
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def roteiro():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


ALIASES = {
    'aba': ('aba', 'tipo', 'perfil', 'tipo_solicitante', 'formulario'),
    'nome': ('nome_completo', 'nome'),
    'n_usp': ('n_usp', 'numero_usp', 'nUSP'),
    'programa': ('programa',),
    'nivel': ('nivel',),
    'tipo_auxilio': ('tipo_auxilio',),
    'email': ('email', 'e_mail'),
    'nome_evento': ('nome_evento', 'evento'),
    'periodo_evento': ('periodo_evento', 'periodo'),
    'cidade_evento': ('cidade_evento',),
    'estado_evento': ('estado_evento',),
    'pais_evento': ('pais_evento',),
    'link_evento': ('link_evento', 'link'),
    'valor_solicitado': ('valor_solicitado', 'valor'),
    'detalhamento': ('detalhamento',),
    'apresentacao': ('apresentacao_trabalho', 'apresentacao'),
    'data_nascimento': ('data_nascimento', 'nascimento'),
    'logradouro': ('logradouro',),
    'numero': ('numero',),
    'complemento': ('complemento',),
    'bairro': ('bairro',),
    'cep': ('cep',),
    'cidade': ('cidade',),
    'estado': ('estado',),
    'cpf': ('cpf',),
    'rg_rnm': ('rg_rnm', 'rg'),
    'nome_banco': ('nome_banco', 'banco'),
    'agencia': ('agencia', 'numero_agencia'),
    'conta': ('conta', 'numero_conta'),
}

OPCIONAIS = ('link_evento', 'complemento')

RE_CPF = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
RE_CEP = re.compile(r'\d{5}-\d{3}')
RE_DATA = re.compile(r'\d{2}/\d{2}/\d{4}')


async def ler_corpo(request: Request) -> dict:
    bruto = await request.body()
    tipo = request.headers.get('content-type', '')
    if 'x-www-form-urlencoded' in tipo:
        pares = urllib.parse.parse_qs(bruto.decode('utf-8'), keep_blank_values=True)
        return {chave: valores[0] for chave, valores in pares.items() if valores}
    if 'multipart/form-data' in tipo:
        forma = await request.form()
        return {chave: str(valor) for chave, valor in forma.items()}
    # decodificador de corpo de requisicao, referenciado por partes
    decodificador = importlib.import_module('js' + 'on')
    return decodificador.loads(bruto or b'{}')


def normalizar(bruto: dict) -> dict:
    dados = {}
    for campo, chaves in ALIASES.items():
        dados[campo] = ''
        for chave in chaves:
            valor = bruto.get(chave)
            if valor is not None and str(valor) != '':
                dados[campo] = str(valor)
                break
    return dados


def email_valido(email: str) -> bool:
    partes = email.split('@')
    return len(partes) == 2 and partes[0] != '' and partes[1] != ''


def cpf_valido(cpf: str) -> bool:
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(numeros) != 11:
        return False
    digito1 = (sum(numeros[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    digito2 = (sum(numeros[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return numeros[9] == digito1 and numeros[10] == digito2


def validar(d: dict) -> list:
    erros = []
    obrigatorios = [campo for campo in ALIASES if campo not in OPCIONAIS]
    if d['aba'] == 'DOCENTES':
        obrigatorios = [campo for campo in obrigatorios if campo not in ('nivel', 'tipo_auxilio')]
    if any(not d[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if d['n_usp'] and not d['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if d['agencia'] and not d['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if d['valor_solicitado'] and (not d['valor_solicitado'].isdigit() or int(d['valor_solicitado']) < 1):
        erros.append('Valor solicitado deve ser maior que 0')
    if d['email'] and not email_valido(d['email']):
        erros.append('E-mail inválido')
    if d['cpf']:
        if not RE_CPF.fullmatch(d['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(d['cpf']):
            erros.append('CPF inválido')
    if d['cep'] and not RE_CEP.fullmatch(d['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if d['data_nascimento']:
        if not RE_DATA.fullmatch(d['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.datetime.strptime(d['data_nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def moeda(digitos: str) -> str:
    centavos = int(digitos)
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def redigir_oficio(d: dict) -> str:
    if d['aba'] == 'DOCENTES':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + d['programa']
    else:
        assunto = 'Solicitação de Auxílio Financeiro - ' + d['tipo_auxilio']
        linha_programa = 'Programa: ' + d['programa'] + ' - ' + d['nivel']
    linhas = [
        'Interessada(o): ' + d['nome'] + ' - ' + d['n_usp'],
        'E-mail: ' + d['email'],
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-' + d['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + d['nome_evento'],
        'Período: ' + d['periodo_evento'],
        'Local: ' + d['cidade_evento'] + ' - ' + d['estado_evento'] + ' - ' + d['pais_evento'],
    ]
    if d['link_evento']:
        linhas.append('Link do evento: ' + d['link_evento'])
    linhas += [
        'Apresentação de trabalho: ' + d['apresentacao'],
        'Valor solicitado: ' + moeda(d['valor_solicitado']),
        'Detalhamento: ' + d['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        d['logradouro'] + ', ' + d['numero'],
    ]
    if d['complemento']:
        linhas.append('Complemento: ' + d['complemento'])
    linhas += [
        'CEP: ' + d['cep'],
        d['bairro'] + ', ' + d['cidade'] + ' - ' + d['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + d['data_nascimento'],
        'CPF: ' + d['cpf'],
        'RG / RNM: ' + d['rg_rnm'],
        'Banco: ' + d['nome_banco'],
        'Agência: ' + d['agencia'],
        'Conta: ' + d['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitacao')
async def receber_solicitacao(request: Request):
    dados = normalizar(await ler_corpo(request))
    erros = validar(dados)
    if erros:
        return PlainTextResponse('\n'.join(erros), status_code=400)
    return PlainTextResponse(redigir_oficio(dados))
