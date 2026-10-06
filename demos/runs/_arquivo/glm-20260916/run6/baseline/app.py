import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent

OBRIGATORIOS = [
    'nome', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo_evento',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro',
    'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'conta',
]


class Dados(BaseModel):
    nome: str = ''
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
    rg_rnm: str = ''
    nome_banco: str = ''
    agencia: str = ''
    conta: str = ''


class Solicitacao(BaseModel):
    tipo: Literal['alunos', 'docentes']
    dados: Dados


def cpf_valido(cpf: str) -> bool:
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(numeros) != 11:
        return False
    digito1 = (sum(n * p for n, p in zip(numeros[:9], range(10, 1, -1))) * 10) % 11 % 10
    digito2 = (sum(n * p for n, p in zip(numeros[:10], range(11, 1, -1))) * 10) % 11 % 10
    return numeros[9] == digito1 and numeros[10] == digito2


def validar(tipo: str, d: Dados) -> list[str]:
    erros = []
    obrigatorios = OBRIGATORIOS + (['nivel', 'tipo_auxilio'] if tipo == 'alunos' else [])
    if any(not getattr(d, campo).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if d.n_usp.strip() and not re.fullmatch(r'[0-9]+', d.n_usp.strip()):
        erros.append('N. USP deve conter apenas números')

    if d.agencia.strip() and not re.fullmatch(r'[0-9]+', d.agencia.strip()):
        erros.append('Número da agência deve conter apenas números')

    centavos = ''.join(c for c in d.valor if c.isdigit())
    if d.valor.strip() and (not centavos or int(centavos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')

    dominio = d.email.rsplit('@', 1)[-1].strip()
    if d.email.strip() and ('@' not in d.email or not dominio):
        erros.append('E-mail inválido')

    if d.cpf.strip():
        if re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', d.cpf.strip()):
            if not cpf_valido(d.cpf):
                erros.append('CPF inválido')
        else:
            erros.append('CPF deve estar no formato 000.000.000-00')

    if d.cep.strip() and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', d.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')

    data = d.data_nascimento.strip()
    if data:
        if re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', data):
            try:
                datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
        else:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    return erros


def moeda(centavos: str) -> str:
    numero = centavos.lstrip('0') or '0'
    cent = numero[-2:].zfill(2)
    reais = numero[:-2] or '0'
    grupos = []
    while len(reais) > 3:
        grupos.insert(0, reais[-3:])
        reais = reais[:-3]
    grupos.insert(0, reais)
    return 'R$ ' + '.'.join(grupos) + ',' + cent


def gerar_oficio(tipo: str, d: Dados) -> str:
    if tipo == 'alunos':
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}'
        programa = f'Programa: {d.programa} - {d.nivel}'
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f'Programa: {d.programa}'

    linhas = [
        f'Interessada(o): {d.nome} - {d.n_usp}',
        f'E-mail: {d.email}',
        assunto,
        programa,
        '',
        f'A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {d.nome_evento}',
        f'Período: {d.periodo_evento}',
        f'Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}',
    ]
    if d.link_evento.strip():
        linhas.append(f'Link do evento: {d.link_evento}')
    linhas += [
        f'Apresentação de trabalho: {d.apresentacao}',
        f"Valor solicitado: {moeda(''.join(c for c in d.valor if c.isdigit()))}",
        f'Detalhamento: {d.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{d.logradouro}, {d.numero}',
    ]
    if d.complemento.strip():
        linhas.append(f'Complemento: {d.complemento}')
    linhas += [
        f'CEP: {d.cep}',
        f'{d.bairro}, {d.cidade} - {d.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {d.data_nascimento}',
        f'CPF: {d.cpf}',
        f'RG / RNM: {d.rg_rnm}',
        f'Banco: {d.nome_banco}',
        f'Agência: {d.agencia}',
        f'Conta: {d.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


@app.post('/api/solicitar')
def solicitar(sol: Solicitacao) -> dict:
    erros = validar(sol.tipo, sol.dados)
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(sol.tipo, sol.dados)}


app.mount('/', StaticFiles(directory=RAIZ, html=True), name='static')
