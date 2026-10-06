import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

CAMPOS_OBRIGATORIOS = (
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
    'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
)
CAMPOS_SO_DE_ALUNOS = ('nivel', 'tipo_auxilio')

RE_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
RE_CPF = re.compile(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$')
RE_CEP = re.compile(r'^\d{5}-\d{3}$')
RE_DATA = re.compile(r'^\d{2}/\d{2}/\d{4}$')


def _texto(dados, campo):
    return str(dados.get(campo) or '').strip()


def _digitos(valor):
    return re.sub(r'\D', '', valor)


def _cpf_valido(digitos):
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[i]) * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != int(digitos[posicao]):
            return False
    return True


def _data_valida(valor):
    dia, mes, ano = (int(parte) for parte in valor.split('/'))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _valor_formatado(valor):
    centavos = int(_digitos(valor) or '0')
    reais, resto = divmod(centavos, 100)
    milhares = '{:,}'.format(reais).replace(',', '.')
    return 'R$ {},{:02d}'.format(milhares, resto)


def _validar(dados):
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if _texto(dados, 'aba') != 'docentes':
        obrigatorios += list(CAMPOS_SO_DE_ALUNOS)

    erros = []
    if any(not _texto(dados, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _texto(dados, 'n_usp')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = _texto(dados, 'agencia')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = _texto(dados, 'valor')
    if valor and int(_digitos(valor) or '0') <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    email = _texto(dados, 'email')
    if email and not RE_EMAIL.match(email):
        erros.append('E-mail inválido')

    cpf = _texto(dados, 'cpf')
    if cpf:
        if not RE_CPF.match(cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(_digitos(cpf)):
            erros.append('CPF inválido')

    cep = _texto(dados, 'cep')
    if cep and not RE_CEP.match(cep):
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = _texto(dados, 'data_nascimento')
    if nascimento:
        if not RE_DATA.match(nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not _data_valida(nascimento):
            erros.append('Data de nascimento inválida')

    return erros


def _oficio(dados):
    def campo(nome):
        return _texto(dados, nome)

    linhas = [
        'Interessada(o): {} - {}'.format(campo('nome_completo'), campo('n_usp')),
        'E-mail: {}'.format(campo('email')),
    ]
    if campo('aba') == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: {}'.format(campo('programa')))
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - {}'.format(campo('tipo_auxilio')))
        linhas.append('Programa: {} - {}'.format(campo('programa'), campo('nivel')))

    linhas += [
        '',
        'A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(campo('programa')),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: {}'.format(campo('nome_evento')),
        'Período: {}'.format(campo('periodo')),
        'Local: {} - {} - {}'.format(campo('cidade_evento'), campo('estado_evento'), campo('pais_evento')),
    ]
    if campo('link_evento'):
        linhas.append('Link do evento: {}'.format(campo('link_evento')))
    linhas += [
        'Apresentação de trabalho: {}'.format(campo('apresentacao')),
        'Valor solicitado: {}'.format(_valor_formatado(campo('valor'))),
        'Detalhamento: {}'.format(campo('detalhamento')),
        '',
        'Endereço da(o) interessada(o)',
        '{}, {}'.format(campo('logradouro'), campo('numero')),
    ]
    if campo('complemento'):
        linhas.append('Complemento: {}'.format(campo('complemento')))
    linhas += [
        'CEP: {}'.format(campo('cep')),
        '{}, {} - {}'.format(campo('bairro'), campo('cidade'), campo('estado')),
        '',
        'Dados para pagamento',
        'Data de nascimento: {}'.format(campo('data_nascimento')),
        'CPF: {}'.format(campo('cpf')),
        'RG / RNM: {}'.format(campo('rg')),
        'Banco: {}'.format(campo('banco')),
        'Agência: {}'.format(campo('agencia')),
        'Conta: {}'.format(campo('conta')),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


app = FastAPI()


@app.post('/api/solicitacao')
async def solicitar(request: Request):
    dados = await request.json()
    if not isinstance(dados, dict):
        dados = {}
    erros = _validar(dados)
    if erros:
        return {'erros': erros, 'oficio': None}
    return {'erros': [], 'oficio': _oficio(dados)}


app.mount('/', StaticFiles(directory=RAIZ, html=True), name='estaticos')
