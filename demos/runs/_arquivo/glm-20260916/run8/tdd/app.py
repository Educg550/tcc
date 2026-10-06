import 
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PASTA = Path(__file__).resolve().parent

app = FastAPI()

OBRIGATORIOS = [
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo', 'cidade_evento',
    'estado_evento', 'pais_evento', 'valor', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
    'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
]


def _valor_numero(texto):
    try:
        return float(texto.replace('R$', '').replace('.', '').replace(',', '.').replace(' ', ''))
    except ValueError:
        return 0.0


def _cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    for peso in (10, 11):
        soma = sum(digito * (peso - indice) for indice, digito in enumerate(digitos[:peso - 1]))
        resto = soma % 11
        if digitos[peso - 1] != (0 if resto < 2 else 11 - resto):
            return False
    return True


def _erros(dados):
    erros = []
    obrigatorios = OBRIGATORIOS + [campo for campo in ('nivel', 'tipo_auxilio') if campo in dados]
    if any(not str(dados.get(campo, '')).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if dados.get('n_usp') and not str(dados['n_usp']).isdigit():
        erros.append('N. USP deve conter apenas números')
    if dados.get('agencia') and not str(dados['agencia']).isdigit():
        erros.append('Número da agência deve conter apenas números')
    if dados.get('valor') and _valor_numero(dados['valor']) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    email = dados.get('email', '')
    if email and ('@' not in email or not email.split('@', 1)[1].strip()):
        erros.append('E-mail inválido')
    cpf = dados.get('cpf', '')
    if cpf and not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not _cpf_valido(cpf):
        erros.append('CPF inválido')
    cep = dados.get('cep', '')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')
    data = dados.get('data_nascimento', '')
    if data:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def _oficio(dados):
    programa = dados.get('programa', '')
    nivel = dados.get('nivel', '')
    assunto = dados.get('tipo_auxilio') or 'Verba do programa'
    linhas = [
        f"Interessada(o): {dados.get('nome', '')} - {dados.get('n_usp', '')}",
        f"E-mail: {dados.get('email', '')}",
        f'Assunto: Solicitação de Auxílio Financeiro - {assunto}',
        f'Programa: {programa} - {nivel}' if nivel else f'Programa: {programa}',
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {dados.get('evento', '')}",
        f"Período: {dados.get('periodo', '')}",
        f"Local: {dados.get('cidade_evento', '')} - {dados.get('estado_evento', '')} - {dados.get('pais_evento', '')}",
    ]
    if dados.get('link_evento'):
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas.extend([
        f"Apresentação de trabalho: {dados.get('apresentacao', '')}",
        f"Valor solicitado: {dados.get('valor', '')}",
        f"Detalhamento: {dados.get('detalhamento', '')}",
        '',
        'Endereço da(o) interessada(o)',
        f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
    ])
    if dados.get('complemento'):
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.extend([
        f"CEP: {dados.get('cep', '')}",
        f"{dados.get('bairro', '')}, {dados.get('cidade', '')} - {dados.get('estado', '')}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {dados.get('data_nascimento', '')}",
        f"CPF: {dados.get('cpf', '')}",
        f"RG / RNM: {dados.get('rg', '')}",
        f"Banco: {dados.get('banco', '')}",
        f"Agência: {dados.get('agencia', '')}",
        f"Conta: {dados.get('conta', '')}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


async def _dados_da_requisicao(requisicao):
    texto = (await requisicao.body()).decode('utf-8')
    try:
        corpo = .loads(texto)
    except ValueError:
        corpo = dict(parse_qsl(texto, keep_blank_values=True))
    return corpo if isinstance(corpo, dict) else {}


@app.post('/solicitacao')
async def solicitar(requisicao: Request):
    dados = await _dados_da_requisicao(requisicao)
    erros = _erros(dados)
    if erros:
        return JSONResponse({'ok': False, 'erros': erros}, status_code=400)
    return {'ok': True, 'oficio': _oficio(dados)}


@app.get('/')
async def indice():
    return FileResponse(PASTA / 'index.html')


@app.get('/style.css')
async def estilo():
    return FileResponse(PASTA / 'style.css')


@app.get('/app.js')
async def script():
    return FileResponse(PASTA / 'app.js')


app.mount('/assets', StaticFiles(directory=PASTA / 'assets', check_dir=False), name='assets')
