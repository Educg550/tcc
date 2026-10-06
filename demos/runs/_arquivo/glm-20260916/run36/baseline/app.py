import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

CHAVES = [
    'nome', 'nusp', 'programa', 'nivel', 'tipo_auxilio', 'email', 'evento',
    'periodo', 'cidade_evento', 'estado_evento', 'pais_evento', 'link_evento',
    'valor', 'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
    'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg',
    'banco', 'agencia', 'conta',
]
OBRIGATORIOS = [c for c in CHAVES if c not in ('link_evento', 'complemento')]

SO_DIGITOS = re.compile(r'[0-9]+')
CPF_FORMATO = re.compile(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}')
CEP_FORMATO = re.compile(r'[0-9]{5}-[0-9]{3}')
DATA_FORMATO = re.compile(r'[0-9]{2}/[0-9]{2}/[0-9]{4}')


def texto(valor) -> str:
    if isinstance(valor, str):
        return valor.strip()
    if valor is None:
        return ''
    return str(valor).strip()


def cpf_conferido(cpf: str) -> bool:
    digitos = [int(c) for c in re.sub(r'[^0-9]', '', cpf)]
    dv1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return dv1 == digitos[9] and dv2 == digitos[10]


def formatar_moeda(valor: str) -> str:
    digitos = re.sub(r'[^0-9]', '', valor).lstrip('0') or '0'
    reais = re.sub(r'\B(?=(\d{3})+(?!\d))', '.', digitos[:-2] or '0')
    return f'R$ {reais},{digitos[-2:].zfill(2)}'


def validar(s: dict, tipo: str) -> list:
    erros = []
    exigidos = [c for c in OBRIGATORIOS
                if not (tipo == 'docentes' and c in ('nivel', 'tipo_auxilio'))]
    if any(not s[c] for c in exigidos):
        erros.append('Preencha todos os campos')
    if s['nusp'] and not SO_DIGITOS.fullmatch(s['nusp']):
        erros.append('N. USP deve conter apenas números')
    if s['email']:
        dominio = s['email'].split('@')[1:]
        if not dominio or not dominio[0]:
            erros.append('E-mail inválido')
    if s['valor']:
        digitos = re.sub(r'[^0-9]', '', s['valor'])
        if not digitos or not digitos.strip('0'):
            erros.append('Valor solicitado deve ser maior que 0')
    if s['data_nascimento']:
        if not DATA_FORMATO.fullmatch(s['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(s['data_nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    if s['cpf']:
        if not CPF_FORMATO.fullmatch(s['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_conferido(s['cpf']):
            erros.append('CPF inválido')
    if s['cep'] and not CEP_FORMATO.fullmatch(s['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if s['agencia'] and not SO_DIGITOS.fullmatch(s['agencia']):
        erros.append('Número da agência deve conter apenas números')
    return erros


def gerar_oficio(s: dict, tipo: str) -> str:
    if tipo == 'docentes':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f"Programa: {s['programa']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {s['tipo_auxilio']}"
        linha_programa = f"Programa: {s['programa']} - {s['nivel']}"
    linhas = [
        f"Interessada(o): {s['nome']} - {s['nusp']}",
        f"E-mail: {s['email']}",
        assunto,
        linha_programa,
        '',
        f"A CCP-{s['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {s['evento']}",
        f"Período: {s['periodo']}",
        f"Local: {s['cidade_evento']} - {s['estado_evento']} - {s['pais_evento']}",
    ]
    if s['link_evento']:
        linhas.append(f"Link do evento: {s['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {s['apresentacao']}",
        f"Valor solicitado: {formatar_moeda(s['valor'])}",
        f"Detalhamento: {s['detalhamento']}",
        '',
        'Endereço da(o) interessada(o)',
        f"{s['logradouro']}, {s['numero']}",
    ]
    if s['complemento']:
        linhas.append(f"Complemento: {s['complemento']}")
    linhas += [
        f"CEP: {s['cep']}",
        f"{s['bairro']}, {s['cidade']} - {s['estado']}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {s['data_nascimento']}",
        f"CPF: {s['cpf']}",
        f"RG / RNM: {s['rg']}",
        f"Banco: {s['banco']}",
        f"Agência: {s['agencia']}",
        f"Conta: {s['conta']}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitar')
async def solicitar(request: Request):
    try:
        dados = await request.json()
    except ValueError:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    tipo = texto(dados.get('tipo_formulario', 'alunos'))
    if tipo != 'docentes':
        tipo = 'alunos'
    s = {chave: texto(dados.get(chave)) for chave in CHAVES}
    erros = validar(s, tipo)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': gerar_oficio(s, tipo)}


@app.get('/')
async def pagina():
    return FileResponse(BASE / 'index.html', media_type='text/html')


@app.get('/style.css')
async def folha_de_estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js')
async def script():
    return FileResponse(BASE / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=BASE / 'assets', check_dir=False), name='assets')
