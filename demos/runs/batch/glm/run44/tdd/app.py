'''Solicitação de auxílio financeiro da Pós-Graduação do IME-USP: backend FastAPI.

Não grava nada: a solicitação se encerra na resposta.
'''

import re
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação do IME-USP')


class Solicitacao(BaseModel):
    tipo: Optional[str] = None
    nome: Optional[str] = None
    n_usp: Optional[str] = None
    programa: Optional[str] = None
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: Optional[str] = None
    evento: Optional[str] = None
    periodo: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    pais: Optional[str] = None
    link: Optional[str] = None
    valor: Optional[str] = None
    detalhamento: Optional[str] = None
    apresentacao: Optional[str] = None
    data_nascimento: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cep: Optional[str] = None
    cidade_endereco: Optional[str] = None
    estado_endereco: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta: Optional[str] = None


OBRIGATORIOS_COMUNS = (
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo', 'cidade',
    'estado', 'pais', 'valor', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
    'cidade_endereco', 'estado_endereco', 'cpf', 'rg', 'banco', 'agencia',
    'conta',
)
OBRIGATORIOS_ALUNO = OBRIGATORIOS_COMUNS + ('nivel', 'tipo_auxilio')


def campo(solicitacao, nome):
    return (getattr(solicitacao, nome) or '').strip()


def parse_valor(valor):
    limpo = valor.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(limpo)
    except ValueError:
        return None


def formatar_brl(numero):
    centavos = round(numero * 100)
    reais, resto = divmod(centavos, 100)
    milhar = f'{reais:,}'.replace(',', '.')
    return f'R$ {milhar},{resto:02d}'


def digito_verificador(parcial):
    soma = sum(int(d) * (len(parcial) + 1 - i) for i, d in enumerate(parcial))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def cpf_valido(cpf):
    digitos = re.sub('[^0-9]', '', cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    return (
        digitos[9] == digito_verificador(digitos[:9])
        and digitos[10] == digito_verificador(digitos[:10])
    )


def erros_de_data(valor):
    if re.fullmatch('[0-9]{2}/[0-9]{2}/[0-9]{4}', valor):
        dia, mes, ano = valor.split('/')
        try:
            date(int(ano), int(mes), int(dia))
        except ValueError:
            return ['Data de nascimento inválida']
        return []
    # Fora do formato não há data para ler: além do aviso de formato,
    # a data informada também é inválida.
    return [
        'Data de nascimento deve estar no formato dd/mm/aaaa',
        'Data de nascimento inválida',
    ]


def validar(s):
    docente = campo(s, 'tipo').lower() == 'docente'
    obrigatorios = OBRIGATORIOS_COMUNS if docente else OBRIGATORIOS_ALUNO

    erros = []
    if any(campo(s, nome) == '' for nome in obrigatorios):
        erros.append('Preencha todos os campos')

    # As checagens de formato só olham campos presentes no pedido;
    # os ausentes já são cobertos pelo aviso de campos obrigatórios.
    if s.n_usp is not None and not re.fullmatch('[0-9]+', campo(s, 'n_usp')):
        erros.append('N. USP deve conter apenas números')
    if s.agencia is not None and not re.fullmatch('[0-9]+', campo(s, 'agencia')):
        erros.append('Número da agência deve conter apenas números')
    if s.valor is not None:
        numero = parse_valor(campo(s, 'valor'))
        if numero is None or numero <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if s.email is not None and not re.fullmatch('[^@ ]+@[^@ ]+[.][^@ ]+', campo(s, 'email')):
        erros.append('E-mail inválido')
    if s.cpf is not None:
        if re.fullmatch('[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}', campo(s, 'cpf')):
            if not cpf_valido(campo(s, 'cpf')):
                erros.append('CPF inválido')
        else:
            erros.append('CPF deve estar no formato 000.000.000-00')
    if s.cep is not None and not re.fullmatch('[0-9]{5}-[0-9]{3}', campo(s, 'cep')):
        erros.append('CEP deve estar no formato 00000-000')
    if s.data_nascimento is not None:
        erros.extend(erros_de_data(campo(s, 'data_nascimento')))
    return erros


def gerar_oficio(s):
    docente = campo(s, 'tipo').lower() == 'docente'
    hoje = date.today().strftime('%d/%m/%Y')
    nome = campo(s, 'nome')
    n_usp = campo(s, 'n_usp')
    programa = campo(s, 'programa')
    email = campo(s, 'email')
    nivel = campo(s, 'nivel')
    tipo_auxilio = campo(s, 'tipo_auxilio')
    evento = campo(s, 'evento')
    periodo = campo(s, 'periodo')
    cidade = campo(s, 'cidade')
    estado = campo(s, 'estado')
    pais = campo(s, 'pais')
    link = campo(s, 'link')
    apresentacao = campo(s, 'apresentacao')
    valor = formatar_brl(parse_valor(campo(s, 'valor')))
    detalhamento = campo(s, 'detalhamento')
    data_nascimento = campo(s, 'data_nascimento')
    logradouro = campo(s, 'logradouro')
    numero = campo(s, 'numero')
    complemento = campo(s, 'complemento')
    bairro = campo(s, 'bairro')
    cep = campo(s, 'cep')
    cidade_endereco = campo(s, 'cidade_endereco')
    estado_endereco = campo(s, 'estado_endereco')
    cpf = campo(s, 'cpf')
    rg = campo(s, 'rg')
    banco = campo(s, 'banco')
    agencia = campo(s, 'agencia')
    conta = campo(s, 'conta')

    linhas = [
        'Solicitação registrada',
        '',
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
    ]
    if docente:
        linhas += [
            'Assunto: Solicitação de Auxílio Financeiro - Verba do programa',
            f'Programa: {programa}',
        ]
    else:
        linhas += [
            f'Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}',
            f'Programa: {programa} - {nivel}',
        ]
    linhas += [
        '',
        f'A CCP-{programa} aprovou na data de hoje ({hoje}), a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {evento}',
        f'Período: {periodo}',
        f'Local: {cidade} - {estado} - {pais}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ]
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f'CEP: {cep}',
        f'{bairro}, {cidade_endereco} - {estado_endereco}',
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
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao)
    if erros:
        return {'valido': False, 'erros': erros}
    return {'valido': True, 'erros': [], 'oficio': gerar_oficio(solicitacao)}


@app.get('/')
def index():
    return FileResponse(BASE_DIR / 'index.html', media_type='text/html')


@app.get('/style.css')
def style_css():
    return FileResponse(BASE_DIR / 'style.css', media_type='text/css')


@app.get('/app.js')
def app_js():
    return FileResponse(BASE_DIR / 'app.js', media_type='text/javascript')


@app.get('/assets/{nome}')
def asset(nome: str):
    return FileResponse(BASE_DIR / 'assets' / nome)
