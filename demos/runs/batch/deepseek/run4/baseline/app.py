import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str = 'alunos'
    nome_completo: str = ''
    n_usp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    nome_evento: str = ''
    periodo: str = ''
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
    rg: str = ''
    banco: str = ''
    agencia: str = ''
    conta: str = ''


OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email',
    'nome_evento', 'periodo', 'cidade_evento', 'estado_evento', 'pais_evento',
    'valor', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
]


def valor_monetario(texto):
    limpo = re.sub(r'[^\d,.]', '', texto)
    if ',' in limpo:
        limpo = limpo.replace('.', '').replace(',', '.')
    else:
        limpo = limpo.replace('.', '')
    try:
        return float(limpo)
    except ValueError:
        return None


def cpf_valido(cpf):
    numeros = re.sub(r'\D', '', cpf)
    if len(numeros) != 11:
        return False
    digitos = [int(c) for c in numeros]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[posicao]:
            return False
    return True


def data_valida(texto):
    partes = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', texto)
    if not partes:
        return False
    dia = int(partes.group(1))
    mes = int(partes.group(2))
    ano = int(partes.group(3))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(solicitacao):
    dados = solicitacao.model_dump()
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if solicitacao.aba == 'alunos':
        obrigatorios += ['nivel', 'tipo_auxilio']

    if any(not dados[campo].strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = dados['n_usp'].strip()
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = dados['agencia'].strip()
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = dados['valor'].strip()
    if valor:
        numero = valor_monetario(valor)
        if numero is None or numero <= 0:
            erros.append('Valor solicitado deve ser maior que 0')

    email = dados['email'].strip()
    if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        erros.append('E-mail inválido')

    cpf = dados['cpf'].strip()
    if cpf:
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = dados['cep'].strip()
    if cep and not re.match(r'^\d{5}-\d{3}$', cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = dados['data_nascimento'].strip()
    if nascimento:
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(nascimento):
            erros.append('Data de nascimento inválida')

    return erros


def gerar_oficio(solicitacao):
    d = solicitacao.model_dump()
    linhas = [
        'Interessada(o): {nome_completo} - {n_usp}'.format(**d),
        'E-mail: {email}'.format(**d),
    ]
    if solicitacao.aba == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: {programa}'.format(**d))
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}'.format(**d))
        linhas.append('Programa: {programa} - {nivel}'.format(**d))
    linhas += [
        '',
        'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(**d),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: {nome_evento}'.format(**d),
        'Período: {periodo}'.format(**d),
        'Local: {cidade_evento} - {estado_evento} - {pais_evento}'.format(**d),
    ]
    if d['link_evento'].strip():
        linhas.append('Link do evento: {link_evento}'.format(**d))
    linhas += [
        'Apresentação de trabalho: {apresentacao}'.format(**d),
        'Valor solicitado: {valor}'.format(**d),
        'Detalhamento: {detalhamento}'.format(**d),
        '',
        'Endereço da(o) interessada(o)',
        '{logradouro}, {numero}'.format(**d),
    ]
    if d['complemento'].strip():
        linhas.append('Complemento: {complemento}'.format(**d))
    linhas += [
        'CEP: {cep}'.format(**d),
        '{bairro}, {cidade} - {estado}'.format(**d),
        '',
        'Dados para pagamento',
        'Data de nascimento: {data_nascimento}'.format(**d),
        'CPF: {cpf}'.format(**d),
        'RG / RNM: {rg}'.format(**d),
        'Banco: {banco}'.format(**d),
        'Agência: {agencia}'.format(**d),
        'Conta: {conta}'.format(**d),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def solicitar(solicitacao: Solicitacao):
    erros = validar(solicitacao)
    if erros:
        return {'erros': erros}
    return {'erros': [], 'oficio': gerar_oficio(solicitacao)}


app.mount('/', StaticFiles(directory=BASE, html=True), name='static')
