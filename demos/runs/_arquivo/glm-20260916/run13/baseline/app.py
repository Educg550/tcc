import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str = 'alunos'
    nome: str = ''
    nusp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    evento: str = ''
    periodo: str = ''
    cidade_evento: str = ''
    estado_evento: str = ''
    pais_evento: str = ''
    link: str = ''
    valor: str = ''
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
    rg: str = ''
    banco: str = ''
    agencia: str = ''
    conta: str = ''


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r'\D', '', cpf)
    if len(digitos) != 11:
        return False
    d = [int(c) for c in digitos]
    dv1 = (sum(d[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(d[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return dv1 == d[9] and dv2 == d[10]


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r'\D', '', valor))
    reais = f'{centavos // 100:,}'.replace(',', '.')
    return f'R$ {reais},{centavos % 100:02d}'


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    obrigatorios = [
        s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
        s.detalhamento, s.apresentacao, s.data_nascimento, s.logradouro,
        s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg,
        s.banco, s.agencia, s.conta,
    ]
    if s.tipo != 'docentes':
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not campo.strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if s.nusp.strip() and not s.nusp.isdigit():
        erros.append('N. USP deve conter apenas números')
    if s.agencia.strip() and not s.agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')
    centavos = re.sub(r'\D', '', s.valor)
    if s.valor.strip() and (not centavos or int(centavos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')
    email = s.email.strip()
    if email:
        partes = email.split('@')
        if len(partes) < 2 or not partes[0] or not partes[-1]:
            erros.append('E-mail inválido')
    cpf = s.cpf.strip()
    if cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')
    if s.cep.strip() and not re.fullmatch(r'\d{5}-\d{3}', s.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')
    data = s.data_nascimento.strip()
    if data:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def gerar_oficio(s: Solicitacao) -> str:
    docente = s.tipo == 'docentes'
    assunto = (
        'Solicitação de Auxílio Financeiro - Verba do programa'
        if docente
        else f'Solicitação de Auxílio Financeiro - {s.tipo_auxilio}'
    )
    programa = f'Programa: {s.programa}' if docente else f'Programa: {s.programa} - {s.nivel}'
    linhas = [
        f'Interessada(o): {s.nome} - {s.nusp}',
        f'E-mail: {s.email}',
        f'Assunto: {assunto}',
        programa,
        '',
        f'A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {s.evento}',
        f'Período: {s.periodo}',
        f'Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}',
    ]
    if s.link.strip():
        linhas.append(f'Link do evento: {s.link}')
    linhas += [
        f'Apresentação de trabalho: {s.apresentacao}',
        f'Valor solicitado: {formatar_moeda(s.valor)}',
        f'Detalhamento: {s.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{s.logradouro}, {s.numero}',
    ]
    if s.complemento.strip():
        linhas.append(f'Complemento: {s.complemento}')
    linhas += [
        f'CEP: {s.cep}',
        f'{s.bairro}, {s.cidade} - {s.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {s.data_nascimento}',
        f'CPF: {s.cpf}',
        f'RG / RNM: {s.rg}',
        f'Banco: {s.banco}',
        f'Agência: {s.agencia}',
        f'Conta: {s.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def receber_solicitacao(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': gerar_oficio(s)}


@app.get('/')
def pagina_inicial():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js')
def script_da_pagina():
    return FileResponse(BASE / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')
