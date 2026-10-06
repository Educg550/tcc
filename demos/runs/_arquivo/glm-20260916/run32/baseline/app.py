import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent


class Solicitacao(BaseModel):
    aba: str = 'ALUNOS'
    nome: str = ''
    n_usp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    evento: str = ''
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
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor',
    'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
    'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg',
    'banco', 'agencia', 'conta',
]
OBRIGATORIOS_ALUNO = ['nivel', 'tipo_auxilio']


def cpf_valido(cpf: str) -> bool:
    num = [int(c) for c in re.sub(r'\D', '', cpf)]
    if len(num) != 11:
        return False
    dv1 = (sum(num[i] * (10 - i) for i in range(9)) * 10) % 11
    dv1 = 0 if dv1 == 10 else dv1
    dv2 = (sum(num[i] * (11 - i) for i in range(10)) * 10) % 11
    dv2 = 0 if dv2 == 10 else dv2
    return dv1 == num[9] and dv2 == num[10]


def validar(d: Solicitacao) -> list:
    erros = []
    obrigatorios = OBRIGATORIOS if d.aba == 'DOCENTES' else OBRIGATORIOS + OBRIGATORIOS_ALUNO
    if any(not getattr(d, campo).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if d.n_usp.strip() and not re.fullmatch(r'\d+', d.n_usp.strip()):
        erros.append('N. USP deve conter apenas números')

    if d.agencia.strip() and not re.fullmatch(r'\d+', d.agencia.strip()):
        erros.append('Número da agência deve conter apenas números')

    if d.valor.strip():
        limpo = re.sub(r'[R$\s.,]', '', d.valor)
        if not re.fullmatch(r'\d+', limpo) or int(limpo) == 0:
            erros.append('Valor solicitado deve ser maior que 0')

    email = d.email.strip()
    if email:
        partes = email.split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')

    cpf = d.cpf.strip()
    formato_cpf = re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf)
    if cpf and not formato_cpf:
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif formato_cpf and not cpf_valido(cpf):
        erros.append('CPF inválido')

    if d.cep.strip() and not re.fullmatch(r'\d{5}-\d{3}', d.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')

    data = d.data_nascimento.strip()
    if data and not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data:
        try:
            datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def moeda(valor: str) -> str:
    digitos = re.sub(r'\D', '', valor)
    if not digitos:
        return valor.strip()
    reais, centavos = divmod(int(digitos), 100)
    inteiro = f'{reais:,}'.replace(',', '.')
    return f'R$ {inteiro},{centavos:02d}'


def construir_oficio(d: Solicitacao) -> str:
    docente = d.aba == 'DOCENTES'
    linhas = [
        f'Interessada(o): {d.nome} - {d.n_usp}',
        f'E-mail: {d.email}',
    ]
    if docente:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {d.programa}')
    else:
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}')
        linhas.append(f'Programa: {d.programa} - {d.nivel}')
    linhas += [
        '',
        f'A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {d.evento}',
        f'Período: {d.periodo}',
        f'Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}',
    ]
    if d.link_evento.strip():
        linhas.append(f'Link do evento: {d.link_evento}')
    linhas += [
        f'Apresentação de trabalho: {d.apresentacao}',
        f'Valor solicitado: {moeda(d.valor)}',
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
        f'RG / RNM: {d.rg}',
        f'Banco: {d.banco}',
        f'Agência: {d.agencia}',
        f'Conta: {d.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI()


@app.post('/solicitacao')
def receber_solicitacao(d: Solicitacao):
    erros = validar(d)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': construir_oficio(d)}


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/index.html')
def pagina_index():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets', check_dir=False), name='assets')
