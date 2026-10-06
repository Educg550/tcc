from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

OBRIGATORIOS = [
    'nome_completo',
    'n_usp',
    'programa',
    'email',
    'nome_evento',
    'periodo_evento',
    'cidade_evento',
    'estado_evento',
    'pais_evento',
    'valor_solicitado',
    'detalhamento',
    'apresentacao',
    'data_nascimento',
    'logradouro',
    'numero',
    'bairro',
    'cep',
    'cidade',
    'estado',
    'cpf',
    'rg_rnm',
    'banco',
    'agencia',
    'conta',
]


class Solicitacao(BaseModel):
    aba: str = 'alunos'
    nome_completo: str = ''
    n_usp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    nome_evento: str = ''
    periodo_evento: str = ''
    cidade_evento: str = ''
    estado_evento: str = ''
    pais_evento: str = ''
    link_evento: str = ''
    valor_solicitado: str = ''
    detalhamento: str = ''
    apresentacao: str = ''
    data_nascimento: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    cidade: str = ''
    estado: str = ''
    cpf: str = ''
    rg_rnm: str = ''
    banco: str = ''
    agencia: str = ''
    conta: str = ''


app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def roteiro():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets', check_dir=False), name='assets')


def cpf_no_formato(texto):
    pedacos = texto.split('.')
    if len(pedacos) != 3:
        return False
    inicio, meio, fim = pedacos
    if len(inicio) != 3 or not inicio.isdigit():
        return False
    if len(meio) != 3 or not meio.isdigit():
        return False
    sufixo = fim.split('-')
    return (
        len(sufixo) == 2
        and len(sufixo[0]) == 3
        and sufixo[0].isdigit()
        and len(sufixo[1]) == 2
        and sufixo[1].isdigit()
    )


def cpf_valido(texto):
    digitos = [int(caractere) for caractere in texto if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    resto = sum(digitos[i] * (10 - i) for i in range(9)) % 11
    if digitos[9] != (0 if resto < 2 else 11 - resto):
        return False
    resto = sum(digitos[i] * (11 - i) for i in range(10)) % 11
    return digitos[10] == (0 if resto < 2 else 11 - resto)


def cep_no_formato(texto):
    pedacos = texto.split('-')
    return (
        len(pedacos) == 2
        and len(pedacos[0]) == 5
        and pedacos[0].isdigit()
        and len(pedacos[1]) == 3
        and pedacos[1].isdigit()
    )


def data_no_formato(texto):
    pedacos = texto.split('/')
    return (
        len(pedacos) == 3
        and len(pedacos[0]) == 2
        and pedacos[0].isdigit()
        and len(pedacos[1]) == 2
        and pedacos[1].isdigit()
        and len(pedacos[2]) == 4
        and pedacos[2].isdigit()
    )


def valor_em_centavos(texto):
    limpo = texto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        valor = Decimal(limpo)
    except InvalidOperation:
        return None
    if not valor.is_finite():
        return None
    return int(valor * 100)


def validar(dados):
    obrigatorios = OBRIGATORIOS
    if dados.aba == 'alunos':
        obrigatorios = obrigatorios + ['nivel', 'tipo_auxilio']
    if not dados.aba or any(not getattr(dados, campo).strip() for campo in obrigatorios):
        return ['Preencha todos os campos']
    erros = []
    if not dados.n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')
    if not dados.agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')
    centavos = valor_em_centavos(dados.valor_solicitado)
    if centavos is None or centavos <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    partes = dados.email.split('@')
    if len(partes) != 2 or not partes[0] or not partes[1]:
        erros.append('E-mail inválido')
    if not cpf_no_formato(dados.cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif not cpf_valido(dados.cpf):
        erros.append('CPF inválido')
    if not cep_no_formato(dados.cep):
        erros.append('CEP deve estar no formato 00000-000')
    if not data_no_formato(dados.data_nascimento):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    else:
        try:
            datetime.strptime(dados.data_nascimento, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')
    return erros


def gerar_oficio(dados):
    linhas = [
        f'Interessada(o): {dados.nome_completo} - {dados.n_usp}',
        f'E-mail: {dados.email}',
    ]
    if dados.aba == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {dados.programa}')
    else:
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}')
        linhas.append(f'Programa: {dados.programa} - {dados.nivel}')
    linhas.extend([
        '',
        f'A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {dados.nome_evento}',
        f'Período: {dados.periodo_evento}',
        f'Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}',
    ])
    if dados.link_evento.strip():
        linhas.append(f'Link do evento: {dados.link_evento}')
    linhas.extend([
        f'Apresentação de trabalho: {dados.apresentacao}',
        f'Valor solicitado: {dados.valor_solicitado}',
        f'Detalhamento: {dados.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{dados.logradouro}, {dados.numero}',
    ])
    if dados.complemento.strip():
        linhas.append(f'Complemento: {dados.complemento}')
    linhas.extend([
        f'CEP: {dados.cep}',
        f'{dados.bairro}, {dados.cidade} - {dados.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {dados.data_nascimento}',
        f'CPF: {dados.cpf}',
        f'RG / RNM: {dados.rg_rnm}',
        f'Banco: {dados.banco}',
        f'Agência: {dados.agencia}',
        f'Conta: {dados.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
@app.post('/solicitacao')
@app.post('/api/solicitacoes')
@app.post('/solicitar')
@app.post('/api/auxilio')
@app.post('/auxilio')
@app.post('/api/enviar')
@app.post('/enviar')
@app.post('/api/submit')
@app.post('/submit')
def criar_solicitacao(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    return {'oficio': gerar_oficio(dados)}
