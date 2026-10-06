import re
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro — Pós-Graduação IME-USP')


class Solicitacao(BaseModel):
    aba: Literal['alunos', 'docentes'] = 'alunos'
    nome_completo: str
    n_usp: str
    programa: str
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str
    nome_evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ''
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: str = ''
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    nome_banco: str
    numero_agencia: str
    numero_conta: str


OBRIGATORIOS = (
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor_solicitado',
    'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro', 'numero',
    'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg', 'nome_banco',
    'numero_agencia', 'numero_conta',
)


def _cpf_valido(cpf: str) -> bool:
    numero = re.sub(r'\D', '', cpf)
    digito_um = (sum(int(d) * peso for d, peso in zip(numero[:9], range(10, 1, -1))) * 10 % 11) % 10
    digito_dois = (sum(int(d) * peso for d, peso in zip(numero[:10], range(11, 1, -1))) * 10 % 11) % 10
    return numero[9] == str(digito_um) and numero[10] == str(digito_dois)


def _validar(dados: Solicitacao) -> list:
    erros = []
    obrigatorios = OBRIGATORIOS + (('nivel', 'tipo_auxilio') if dados.aba == 'alunos' else ())
    if any(not getattr(dados, campo).strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if dados.n_usp.strip() and not dados.n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')
    if dados.numero_agencia.strip() and not dados.numero_agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')
    pedacos = ''.join(c for c in dados.valor_solicitado if c.isdigit())
    if dados.valor_solicitado.strip() and (not pedacos or int(pedacos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')
    if dados.email.strip():
        local, arroba, dominio = dados.email.partition('@')
        if not arroba or not local.strip() or not dominio.strip():
            erros.append('E-mail inválido')
    if dados.cpf.strip():
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', dados.cpf.strip()):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(dados.cpf.strip()):
            erros.append('CPF inválido')
    if dados.cep.strip() and not re.fullmatch(r'\d{5}-\d{3}', dados.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')
    if dados.data_nascimento.strip():
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', dados.data_nascimento.strip()):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            dia, mes, ano = dados.data_nascimento.strip().split('/')
            try:
                date(int(ano), int(mes), int(dia))
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def _formatar_valor(valor: str) -> str:
    pedacos = ''.join(c for c in valor if c.isdigit())
    if not pedacos:
        return valor.strip()
    reais, centavos = divmod(int(pedacos), 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{centavos:02d}'


def _oficio(dados: Solicitacao) -> str:
    if dados.aba == 'docentes':
        assunto = 'Verba do programa'
        linha_programa = f'Programa: {dados.programa}'
    else:
        assunto = dados.tipo_auxilio
        linha_programa = f'Programa: {dados.programa} - {dados.nivel}'
    linhas = [
        f'Interessada(o): {dados.nome_completo} - {dados.n_usp}',
        f'E-mail: {dados.email}',
        f'Assunto: Solicitação de Auxílio Financeiro - {assunto}',
        linha_programa,
        '',
        f'A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {dados.nome_evento}',
        f'Período: {dados.periodo}',
        f'Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}',
    ]
    if dados.link_evento.strip():
        linhas.append(f'Link do evento: {dados.link_evento}')
    linhas.extend([
        f'Apresentação de trabalho: {dados.apresentacao}',
        f'Valor solicitado: {_formatar_valor(dados.valor_solicitado)}',
        f'Detalhamento: {dados.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{dados.logradouro}, {dados.numero}',
    ])
    if dados.complemento.strip():
        linhas.append(f'Complemento: {dados.complemento}')
    linhas.extend([
        f'CEP: {dados.cep}',
        f'{dados.bairro}, {dados.cidade} - {dados.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {dados.data_nascimento}',
        f'CPF: {dados.cpf}',
        f'RG / RNM: {dados.rg}',
        f'Banco: {dados.nome_banco}',
        f'Agência: {dados.numero_agencia}',
        f'Conta: {dados.numero_conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/api/solicitacoes')
def receber_solicitacao(dados: Solicitacao):
    erros = _validar(dados)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': _oficio(dados)}


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets', check_dir=False), name='assets')
