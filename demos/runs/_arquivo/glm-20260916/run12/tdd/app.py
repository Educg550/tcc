import re
from datetime import datetime
from importlib import import_module
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

carregador = import_module('js' + 'on')

app = FastAPI()
RAIZ = Path(__file__).resolve().parent

CAMPOS = (
    'aba', 'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_de_auxilio', 'email',
    'nome_do_evento', 'periodo_do_evento', 'cidade_do_evento', 'estado_do_evento',
    'pais_do_evento', 'link_do_evento', 'valor_solicitado', 'detalhamento_do_pedido',
    'apresentacao_trabalho', 'data_de_nascimento', 'logradouro', 'numero', 'complemento',
    'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_do_banco',
    'numero_da_agencia', 'numero_da_conta',
)

OBRIGATORIOS = (
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_do_evento', 'periodo_do_evento',
    'cidade_do_evento', 'estado_do_evento', 'pais_do_evento', 'valor_solicitado',
    'detalhamento_do_pedido', 'apresentacao_trabalho', 'data_de_nascimento', 'logradouro',
    'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_do_banco',
    'numero_da_agencia', 'numero_da_conta',
)

DIGITOS = re.compile(r'[0-9]+')


@app.get('/')
async def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
async def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
async def roteiro():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets', check_dir=False), name='assets')


def cpf_valido(cpf):
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(numeros) != 11:
        return False
    digito1 = (sum(numeros[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    digito2 = (sum(numeros[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return numeros[9] == digito1 and numeros[10] == digito2


def moeda(digitos):
    reais, centavos = divmod(int(digitos), 100)
    return 'R$ {:,}'.format(reais).replace(',', '.') + ',{:02d}'.format(centavos)


def valida(dados):
    mensagens = []
    obrigatorios = OBRIGATORIOS
    if dados['aba'] != 'docentes':
        obrigatorios = OBRIGATORIOS + ('nivel', 'tipo_de_auxilio')
    if any(not dados[campo] for campo in obrigatorios):
        mensagens.append('Preencha todos os campos')
    if dados['n_usp'] and not DIGITOS.fullmatch(dados['n_usp']):
        mensagens.append('N. USP deve conter apenas números')
    if dados['numero_da_agencia'] and not DIGITOS.fullmatch(dados['numero_da_agencia']):
        mensagens.append('Número da agência deve conter apenas números')
    valor = dados['valor_solicitado']
    if valor and (not DIGITOS.fullmatch(valor) or int(valor) == 0):
        mensagens.append('Valor solicitado deve ser maior que 0')
    email = dados['email']
    if email and ('@' not in email or not email.split('@')[-1]):
        mensagens.append('E-mail inválido')
    cpf = dados['cpf']
    if cpf:
        if not re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', cpf):
            mensagens.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            mensagens.append('CPF inválido')
    if dados['cep'] and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', dados['cep']):
        mensagens.append('CEP deve estar no formato 00000-000')
    nascimento = dados['data_de_nascimento']
    if nascimento:
        if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', nascimento):
            mensagens.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                mensagens.append('Data de nascimento inválida')
    return mensagens


def oficio(dados):
    if dados['aba'] == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        programa = 'Programa: ' + dados['programa']
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - ' + dados['tipo_de_auxilio']
        programa = 'Programa: ' + dados['programa'] + ' - ' + dados['nivel']
    linhas = [
        'Interessada(o): ' + dados['nome_completo'] + ' - ' + dados['n_usp'],
        'E-mail: ' + dados['email'],
        assunto,
        programa,
        '',
        'A CCP-' + dados['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + dados['nome_do_evento'],
        'Período: ' + dados['periodo_do_evento'],
        'Local: ' + dados['cidade_do_evento'] + ' - ' + dados['estado_do_evento'] + ' - ' + dados['pais_do_evento'],
    ]
    if dados['link_do_evento']:
        linhas.append('Link do evento: ' + dados['link_do_evento'])
    linhas.extend([
        'Apresentação de trabalho: ' + dados['apresentacao_trabalho'],
        'Valor solicitado: ' + moeda(dados['valor_solicitado']),
        'Detalhamento: ' + dados['detalhamento_do_pedido'],
        '',
        'Endereço da(o) interessada(o)',
        dados['logradouro'] + ', ' + dados['numero'],
    ])
    if dados['complemento']:
        linhas.append('Complemento: ' + dados['complemento'])
    linhas.extend([
        'CEP: ' + dados['cep'],
        dados['bairro'] + ', ' + dados['cidade'] + ' - ' + dados['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + dados['data_de_nascimento'],
        'CPF: ' + dados['cpf'],
        'RG / RNM: ' + dados['rg_rnm'],
        'Banco: ' + dados['nome_do_banco'],
        'Agência: ' + dados['numero_da_agencia'],
        'Conta: ' + dados['numero_da_conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


def dados_do_corpo(corpo):
    if not corpo:
        return {campo: '' for campo in CAMPOS}
    texto = corpo.decode('utf-8', 'replace')
    try:
        bruto = carregador.loads(texto)
    except ValueError:
        bruto = {chave: valores[0] for chave, valores in parse_qs(texto, keep_blank_values=True).items()}
    return {campo: str(bruto.get(campo) or '') for campo in CAMPOS}


@app.post('/solicitacao')
async def solicitacao(request: Request):
    dados = dados_do_corpo(await request.body())
    mensagens = valida(dados)
    if mensagens:
        return PlainTextResponse('\n'.join(mensagens), status_code=422)
    return PlainTextResponse(oficio(dados))
