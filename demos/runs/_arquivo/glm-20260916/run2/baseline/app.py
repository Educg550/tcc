import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


class Solicitacao(BaseModel):
    tipo: str
    dados: dict[str, str] = {}


OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email',
    'nome_evento', 'periodo', 'cidade_evento', 'estado_evento', 'pais_evento',
    'valor', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
]

CPF_FORMATO = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
CEP_FORMATO = re.compile(r'\d{5}-\d{3}')
DATA_FORMATO = re.compile(r'\d{2}/\d{2}/\d{4}')
DIGITOS = re.compile(r'[0-9]+')


def cpf_valido(cpf: str) -> bool:
    d = [int(caractere) for caractere in cpf if caractere.isdigit()]
    dv1 = sum(d[i] * (10 - i) for i in range(9)) % 11
    dv1 = 0 if dv1 < 2 else 11 - dv1
    dv2 = sum(d[i] * (11 - i) for i in range(10)) % 11
    dv2 = 0 if dv2 < 2 else 11 - dv2
    return d[9] == dv1 and d[10] == dv2


def moeda(centavos: int) -> str:
    reais, cent = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{cent:02d}'


def validar(tipo: str, d: dict[str, str]) -> tuple[list[str], str | None]:
    erros: list[str] = []

    obrigatorios = OBRIGATORIOS + (['nivel', 'tipo_auxilio'] if tipo == 'alunos' else [])
    if any(not d.get(campo, '').strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = d.get('n_usp', '').strip()
    if n_usp and not DIGITOS.fullmatch(n_usp):
        erros.append('N. USP deve conter apenas números')

    agencia = d.get('agencia', '').strip()
    if agencia and not DIGITOS.fullmatch(agencia):
        erros.append('Número da agência deve conter apenas números')

    valor_fmt = None
    valor = d.get('valor', '').strip()
    if valor:
        digitos = ''.join(re.findall(r'[0-9]', valor))
        if not digitos or int(digitos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')
        else:
            valor_fmt = moeda(int(digitos))

    email = d.get('email', '').strip()
    if email and ('@' not in email or not email.rsplit('@', 1)[1].strip()):
        erros.append('E-mail inválido')

    cpf = d.get('cpf', '').strip()
    cpf_no_formato = bool(CPF_FORMATO.fullmatch(cpf))
    if cpf and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')

    cep = d.get('cep', '').strip()
    if cep and not CEP_FORMATO.fullmatch(cep):
        erros.append('CEP deve estar no formato 00000-000')

    data = d.get('data_nascimento', '').strip()
    data_no_formato = bool(DATA_FORMATO.fullmatch(data))
    if data and not data_no_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append('CPF inválido')

    if data_no_formato:
        try:
            datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros, valor_fmt


def gerar_oficio(tipo: str, d: dict[str, str], valor_fmt: str) -> str:
    def c(campo: str) -> str:
        return d.get(campo, '').strip()

    nome = c('nome_completo')
    n_usp = c('n_usp')
    email = c('email')
    programa = c('programa')
    nivel = c('nivel')
    tipo_auxilio = c('tipo_auxilio')
    evento = c('nome_evento')
    periodo = c('periodo')
    cidade_ev = c('cidade_evento')
    estado_ev = c('estado_evento')
    pais_ev = c('pais_evento')
    link = c('link_evento')
    apresentacao = c('apresentacao')
    detalhamento = c('detalhamento')
    logradouro = c('logradouro')
    numero = c('numero')
    complemento = c('complemento')
    bairro = c('bairro')
    cep = c('cep')
    cidade = c('cidade')
    estado = c('estado')
    data_nascimento = c('data_nascimento')
    cpf = c('cpf')
    rg = c('rg')
    banco = c('banco')
    agencia = c('agencia')
    conta = c('conta')

    if tipo == 'alunos':
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}'
        linha_programa = f'Programa: {programa} - {nivel}'
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'

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
        f'Evento: {evento}',
        f'Período: {periodo}',
        f'Local: {cidade_ev} - {estado_ev} - {pais_ev}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor_fmt}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ]
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f'CEP: {cep}',
        f'{bairro}, {cidade} - {estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {data_nascimento}',
        f'CPF: {cpf}',
        f'RG / RNM: {rg}',
        f'Banco: {banco}',
        f'Agência: {agencia}',
        f'Conta: {conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def registrar(solicitacao: Solicitacao) -> dict:
    erros, valor_fmt = validar(solicitacao.tipo, solicitacao.dados)
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(solicitacao.tipo, solicitacao.dados, valor_fmt or '')}


@app.get('/')
def pagina() -> FileResponse:
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def estilo() -> FileResponse:
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script() -> FileResponse:
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
