"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')
app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')

CAMPOS_OBRIGATORIOS = (
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo', 'cidade',
    'estado', 'pais', 'valor', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade_sol',
    'estado_sol', 'cpf', 'rg', 'banco', 'agencia', 'conta',
)
CAMPOS_ALUNO = ('nivel', 'tipo_auxilio')
CAMPOS = CAMPOS_OBRIGATORIOS + CAMPOS_ALUNO + ('link', 'complemento')

SO_DIGITOS = re.compile(r'[0-9]+')
EMAIL = re.compile(r'[^@\s]+@[^@\s]+\.[^@\s]+')
CPF_FORMATO = re.compile(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}')
CEP_FORMATO = re.compile(r'[0-9]{5}-[0-9]{3}')
DATA_FORMATO = re.compile(r'[0-9]{2}/[0-9]{2}/[0-9]{4}')


@app.get('/')
def index():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js', media_type='application/javascript')


def texto(dados, nome):
    valor = dados.get(nome, '')
    return '' if valor is None else str(valor).strip()


def valor_em_reais(valor):
    limpo = valor.replace('R$', '').replace(' ', '')
    if ',' in limpo:
        limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return None


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * (i + 1 - j) for j in range(i))
        if soma * 10 % 11 % 10 != digitos[i]:
            return False
    return True


def data_existente(data):
    dia, mes, ano = (int(parte) for parte in data.split('/'))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(dados, aba):
    erros = []
    obrigatorios = CAMPOS_OBRIGATORIOS + (() if aba == 'docentes' else CAMPOS_ALUNO)
    if any(not dados[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if dados['n_usp'] and not SO_DIGITOS.fullmatch(dados['n_usp']):
        erros.append('N. USP deve conter apenas números')
    if dados['agencia'] and not SO_DIGITOS.fullmatch(dados['agencia']):
        erros.append('Número da agência deve conter apenas números')
    if dados['valor']:
        valor = valor_em_reais(dados['valor'])
        if valor is None or valor <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if dados['email'] and not EMAIL.fullmatch(dados['email']):
        erros.append('E-mail inválido')
    if dados['cpf']:
        if not CPF_FORMATO.fullmatch(dados['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(dados['cpf']):
            erros.append('CPF inválido')
    if dados['cep'] and not CEP_FORMATO.fullmatch(dados['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if dados['data_nascimento']:
        if not DATA_FORMATO.fullmatch(dados['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_existente(dados['data_nascimento']):
            erros.append('Data de nascimento inválida')
    return erros


def montar_oficio(dados, aba):
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
    ]
    if aba == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f"Programa: {dados['programa']}")
    else:
        linhas.append(
            f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    linhas += [
        '',
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade']} - {dados['estado']} - {dados['pais']}",
    ]
    if dados['link']:
        linhas.append(f"Link do evento: {dados['link']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {dados['valor']}",
        f"Detalhamento: {dados['detalhamento']}",
        '',
        'Endereço da(o) interessada(o)',
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados['complemento']:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade_sol']} - {dados['estado_sol']}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitacao')
def solicitar(dados: dict):
    aba = texto(dados, 'aba').lower() or 'alunos'
    if aba not in ('alunos', 'docentes'):
        aba = 'alunos'
    limpos = {campo: texto(dados, campo) for campo in CAMPOS}
    erros = validar(limpos, aba)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    return {'oficio': montar_oficio(limpos, aba)}
