import calendar
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


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
    apresentacao_trabalho: str = ''
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
    numero_conta: str = ''


OBRIGATORIOS = {
    'alunos': [
        'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
        'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento',
        'pais_evento', 'valor_solicitado', 'detalhamento', 'apresentacao_trabalho',
        'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
        'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'numero_conta',
    ],
    'docentes': [
        'nome_completo', 'n_usp', 'programa', 'email',
        'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento',
        'pais_evento', 'valor_solicitado', 'detalhamento', 'apresentacao_trabalho',
        'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
        'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'numero_conta',
    ],
}


def so_digitos(texto: str) -> bool:
    return bool(re.fullmatch(r'[0-9]+', texto))


def cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in re.sub(r'[^0-9]', '', cpf)]
    if len(digitos) != 11:
        return False
    dv1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return digitos[9] == dv1 and digitos[10] == dv2


def validar(aba: str, d: dict) -> list[str]:
    erros = []
    if any(not d[campo] for campo in OBRIGATORIOS.get(aba, OBRIGATORIOS['alunos'])):
        erros.append('Preencha todos os campos')
    if d['n_usp'] and not so_digitos(d['n_usp']):
        erros.append('N. USP deve conter apenas números')
    if d['agencia'] and not so_digitos(d['agencia']):
        erros.append('Número da agência deve conter apenas números')
    centavos = re.sub(r'[^0-9]', '', d['valor_solicitado'])
    if d['valor_solicitado'] and (not centavos or int(centavos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')
    if d['email']:
        usuario, arroba, dominio = d['email'].partition('@')
        if not arroba or not usuario or not dominio:
            erros.append('E-mail inválido')
    cpf_no_formato = bool(re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', d['cpf']))
    if d['cpf'] and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')
    if d['cep'] and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', d['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    data = re.fullmatch(r'([0-9]{2})/([0-9]{2})/([0-9]{4})', d['data_nascimento'])
    if d['data_nascimento'] and not data:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_no_formato and not cpf_valido(d['cpf']):
        erros.append('CPF inválido')
    if data:
        dia, mes, ano = (int(parte) for parte in data.groups())
        if not 1 <= mes <= 12 or not 1 <= dia <= calendar.monthrange(ano, mes)[1]:
            erros.append('Data de nascimento inválida')
    return erros


def formatar_valor(centavos: str) -> str:
    reais, resto = divmod(int(centavos), 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def gerar_oficio(aba: str, d: dict) -> str:
    if aba == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {d["programa"]}'
    else:
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {d["tipo_auxilio"]}'
        linha_programa = f'Programa: {d["programa"]} - {d["nivel"]}'
    linhas = [
        f'Interessada(o): {d["nome_completo"]} - {d["n_usp"]}',
        f'E-mail: {d["email"]}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{d["programa"]} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {d["nome_evento"]}',
        f'Período: {d["periodo_evento"]}',
        f'Local: {d["cidade_evento"]} - {d["estado_evento"]} - {d["pais_evento"]}',
    ]
    if d['link_evento']:
        linhas.append(f'Link do evento: {d["link_evento"]}')
    linhas += [
        f'Apresentação de trabalho: {d["apresentacao_trabalho"]}',
        'Valor solicitado: ' + formatar_valor(re.sub(r'[^0-9]', '', d['valor_solicitado'])),
        f'Detalhamento: {d["detalhamento"]}',
        '',
        'Endereço da(o) interessada(o)',
        f'{d["logradouro"]}, {d["numero"]}',
    ]
    if d['complemento']:
        linhas.append(f'Complemento: {d["complemento"]}')
    linhas += [
        f'CEP: {d["cep"]}',
        f'{d["bairro"]}, {d["cidade"]} - {d["estado"]}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {d["data_nascimento"]}',
        f'CPF: {d["cpf"]}',
        f'RG / RNM: {d["rg_rnm"]}',
        f'Banco: {d["nome_banco"]}',
        f'Agência: {d["agencia"]}',
        f'Conta: {d["numero_conta"]}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'static' / 'index.html')


@app.post('/api/solicitacao')
def receber_solicitacao(solicitacao: Solicitacao):
    d = {campo: getattr(solicitacao, campo).strip() for campo in Solicitacao.model_fields}
    aba = d['aba'].strip().lower()
    erros = validar(aba, d)
    if erros:
        return {'erros': erros, 'oficio': None}
    return {'erros': [], 'oficio': gerar_oficio(aba, d)}


app.mount('/static', StaticFiles(directory=RAIZ / 'static'), name='static')
app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
