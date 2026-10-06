import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PASTA = Path(__file__).resolve().parent

OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento',
    'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento',
    'valor_solicitado', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
    'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'conta',
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
    nome_banco: str = ''
    agencia: str = ''
    conta: str = ''


def digito_cpf(base: str, peso_inicial: int) -> str:
    soma = sum(int(d) * (peso_inicial - i) for i, d in enumerate(base))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r'\D', '', cpf)
    if len(digitos) != 11:
        return False
    return (digito_cpf(digitos[:9], 10) == digitos[9]
            and digito_cpf(digitos[:10], 11) == digitos[10])


def data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def formatar_moeda(texto: str) -> str:
    centavos = int(re.sub(r'\D', '', texto))
    reais, centavos = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{centavos:02d}'


def validar(s: Solicitacao) -> list[str]:
    campos = s.model_dump()
    obrigatorios = OBRIGATORIOS if s.aba == 'docentes' else OBRIGATORIOS + ['nivel', 'tipo_auxilio']
    erros = []
    if any(not campos[c].strip() for c in obrigatorios):
        erros.append('Preencha todos os campos')

    if campos['n_usp'] and not re.fullmatch(r'\d+', campos['n_usp']):
        erros.append('N. USP deve conter apenas números')
    if campos['agencia'] and not re.fullmatch(r'\d+', campos['agencia']):
        erros.append('Número da agência deve conter apenas números')
    if campos['valor_solicitado']:
        digitos = re.sub(r'\D', '', campos['valor_solicitado'])
        if not digitos or int(digitos) == 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if campos['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+', campos['email']):
        erros.append('E-mail inválido')
    if campos['cpf']:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', campos['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(campos['cpf']):
            erros.append('CPF inválido')
    if campos['cep'] and not re.fullmatch(r'\d{5}-\d{3}', campos['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if campos['data_nascimento']:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', campos['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(campos['data_nascimento']):
            erros.append('Data de nascimento inválida')
    return erros


def montar_oficio(s: Solicitacao) -> str:
    docente = s.aba == 'docentes'
    assunto = ('Solicitação de Auxílio Financeiro - Verba do programa' if docente
               else f'Solicitação de Auxílio Financeiro - {s.tipo_auxilio}')
    linha_programa = (f'Programa: {s.programa}' if docente
                      else f'Programa: {s.programa} - {s.nivel}')
    linhas = [
        f'Interessada(o): {s.nome_completo} - {s.n_usp}',
        f'E-mail: {s.email}',
        f'Assunto: {assunto}',
        linha_programa,
        '',
        f'A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {s.nome_evento}',
        f'Período: {s.periodo_evento}',
        f'Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}',
    ]
    if s.link_evento:
        linhas.append(f'Link do evento: {s.link_evento}')
    linhas += [
        f'Apresentação de trabalho: {s.apresentacao}',
        f'Valor solicitado: {formatar_moeda(s.valor_solicitado)}',
        f'Detalhamento: {s.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{s.logradouro}, {s.numero}',
    ]
    if s.complemento:
        linhas.append(f'Complemento: {s.complemento}')
    linhas += [
        f'CEP: {s.cep}',
        f'{s.bairro}, {s.cidade} - {s.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {s.data_nascimento}',
        f'CPF: {s.cpf}',
        f'RG / RNM: {s.rg_rnm}',
        f'Banco: {s.nome_banco}',
        f'Agência: {s.agencia}',
        f'Conta: {s.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI()


@app.get('/')
def index() -> FileResponse:
    return FileResponse(PASTA / 'index.html')


@app.get('/style.css')
def css() -> FileResponse:
    return FileResponse(PASTA / 'style.css', media_type='text/css')


@app.get('/app.js')
def js() -> FileResponse:
    return FileResponse(PASTA / 'app.js', media_type='text/javascript')


@app.post('/api/solicitacao')
def registrar_solicitacao(s: Solicitacao) -> dict:
    erros = validar(s)
    if erros:
        return {'erros': erros}
    return {'oficio': montar_oficio(s)}


app.mount('/assets', StaticFiles(directory=PASTA / 'assets'), name='assets')
