import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

CAMPOS = [
    'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
    'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento',
    'pais_evento', 'link_evento', 'valor_solicitado', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'complemento',
    'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco',
    'agencia', 'conta',
]
OPCIONAIS = {'link_evento', 'complemento'}


class Solicitacao(BaseModel):
    aba: str
    campos: dict[str, str]


def moeda(digitos: str) -> str:
    reais, centavos = divmod(int(digitos or '0'), 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{centavos:02d}'


def cpf_valido(cpf: str) -> bool:
    numeros = [int(c) for c in cpf if c.isdigit()]
    if len(numeros) != 11:
        return False
    for i in range(9, 11):
        soma = sum(numeros[k] * ((i + 1) - k) for k in range(i))
        if (soma * 10) % 11 % 10 != numeros[i]:
            return False
    return True


def validar(aba: str, d: dict[str, str]) -> list[str]:
    obrigatorios = [c for c in CAMPOS if c not in OPCIONAIS]
    if aba == 'docentes':
        obrigatorios = [c for c in obrigatorios if c not in ('nivel', 'tipo_auxilio')]
    erros = []
    if any(not d[c] for c in obrigatorios):
        erros.append('Preencha todos os campos')
    if d['n_usp'] and not d['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if d['agencia'] and not d['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if d['valor_solicitado']:
        digitos = re.sub(r'\D', '', d['valor_solicitado'])
        if not digitos or int(digitos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')
    partes = d['email'].split('@')
    if d['email'] and (len(partes) != 2 or not partes[0] or not partes[1]):
        erros.append('E-mail inválido')
    cpf_ok = bool(re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', d['cpf']))
    if d['cpf'] and not cpf_ok:
        erros.append('CPF deve estar no formato 000.000.000-00')
    if d['cep'] and not re.fullmatch(r'\d{5}-\d{3}', d['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    data_ok = bool(re.fullmatch(r'\d{2}/\d{2}/\d{4}', d['data_nascimento']))
    if d['data_nascimento'] and not data_ok:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_ok and not cpf_valido(d['cpf']):
        erros.append('CPF inválido')
    if data_ok:
        try:
            datetime.strptime(d['data_nascimento'], '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')
    return erros


def gerar_oficio(aba: str, d: dict[str, str]) -> str:
    nome = d['nome_completo']
    n_usp = d['n_usp']
    email = d['email']
    programa = d['programa']
    nome_evento = d['nome_evento']
    periodo = d['periodo_evento']
    cidade_evento = d['cidade_evento']
    estado_evento = d['estado_evento']
    pais_evento = d['pais_evento']
    link = d['link_evento']
    apresentacao = d['apresentacao']
    detalhamento = d['detalhamento']
    logradouro = d['logradouro']
    numero = d['numero']
    complemento = d['complemento']
    bairro = d['bairro']
    cep = d['cep']
    cidade = d['cidade']
    estado = d['estado']
    nascimento = d['data_nascimento']
    cpf = d['cpf']
    rg = d['rg_rnm']
    banco = d['nome_banco']
    agencia = d['agencia']
    conta = d['conta']
    valor = moeda(re.sub(r'\D', '', d['valor_solicitado']))
    if aba == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'
    else:
        tipo = d['tipo_auxilio']
        nivel = d['nivel']
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {tipo}'
        linha_programa = f'Programa: {programa} - {nivel}'
    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {nome_evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend([
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ])
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend([
        f'CEP: {cep}',
        f'{bairro}, {cidade} - {estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg}',
        f'Banco: {banco}',
        f'Agência: {agencia}',
        f'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/solicitar')
def solicitar(s: Solicitacao):
    d = {c: (s.campos.get(c) or '').strip() for c in CAMPOS}
    erros = validar(s.aba, d)
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(s.aba, d)}


@app.get('/')
def pagina():
    return FileResponse('index.html')


@app.get('/style.css')
def estilo():
    return FileResponse('style.css')


@app.get('/app.js')
def script():
    return FileResponse('app.js')


app.mount('/assets', StaticFiles(directory='assets'), name='assets')
