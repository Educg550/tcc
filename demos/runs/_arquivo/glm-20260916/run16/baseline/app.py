import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')
app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')


class Solicitacao(BaseModel):
    tipo: str = 'alunos'
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


OBRIGATORIOS = [
    'nome', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo_evento',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor_solicitado',
    'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
    'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm',
    'banco', 'agencia', 'conta',
]


def cpf_valido(cpf: str) -> bool:
    numeros = [int(d) for d in re.sub(r'\D', '', cpf)]
    if len(numeros) != 11:
        return False
    resto1 = sum(numeros[i] * (10 - i) for i in range(9)) % 11
    digito1 = 0 if resto1 < 2 else 11 - resto1
    resto2 = sum(numeros[i] * (11 - i) for i in range(10)) % 11
    digito2 = 0 if resto2 < 2 else 11 - resto2
    return numeros[9] == digito1 and numeros[10] == digito2


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    obrigatorios = OBRIGATORIOS + ([] if s.tipo == 'docentes' else ['nivel', 'tipo_auxilio'])
    if any(not getattr(s, campo).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if s.n_usp.strip() and not re.fullmatch(r'[0-9]+', s.n_usp.strip()):
        erros.append('N. USP deve conter apenas números')
    if s.agencia.strip() and not re.fullmatch(r'[0-9]+', s.agencia.strip()):
        erros.append('Número da agência deve conter apenas números')
    if s.valor_solicitado.strip():
        centavos = re.sub(r'\D', '', s.valor_solicitado)
        if not centavos or int(centavos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if s.email.strip() and not re.fullmatch(r'[^@\s]+@[^@\s]+', s.email.strip()):
        erros.append('E-mail inválido')
    cpf_no_formato = False
    if s.cpf.strip():
        if re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', s.cpf.strip()):
            cpf_no_formato = True
        else:
            erros.append('CPF deve estar no formato 000.000.000-00')
    if s.cep.strip() and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', s.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')
    data_no_formato = False
    if s.data_nascimento.strip():
        if re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', s.data_nascimento.strip()):
            data_no_formato = True
        else:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_no_formato and not cpf_valido(s.cpf.strip()):
        erros.append('CPF inválido')
    if data_no_formato:
        try:
            datetime.strptime(s.data_nascimento.strip(), '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')
    return erros


def formatar_valor(campo: str) -> str:
    centavos = int(re.sub(r'\D', '', campo) or '0')
    reais, resto = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def montar_oficio(s: Solicitacao) -> str:
    docentes = s.tipo == 'docentes'
    if docentes:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f'Programa: {s.programa}'
    else:
        assunto = f'Solicitação de Auxílio Financeiro - {s.tipo_auxilio}'
        programa = f'Programa: {s.programa} - {s.nivel}'
    linhas = [
        f'Interessada(o): {s.nome} - {s.n_usp}',
        f'E-mail: {s.email}',
        f'Assunto: {assunto}',
        programa,
        '',
        f'A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {s.nome_evento}',
        f'Período: {s.periodo_evento}',
        f'Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}',
    ]
    if s.link_evento.strip():
        linhas.append(f'Link do evento: {s.link_evento}')
    linhas += [
        f'Apresentação de trabalho: {s.apresentacao}',
        f'Valor solicitado: {formatar_valor(s.valor_solicitado)}',
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
        f'RG / RNM: {s.rg_rnm}',
        f'Banco: {s.banco}',
        f'Agência: {s.agencia}',
        f'Conta: {s.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.get('/')
def index():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js', media_type='text/javascript')


@app.post('/api/solicitacao')
def solicitar(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {'erros': erros, 'oficio': None}
    return {'erros': [], 'oficio': montar_oficio(s)}
