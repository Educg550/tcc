'''Solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Backend em FastAPI: serve a tela, valida a solicitação e devolve o ofício já
redigido. Nada é gravado - a solicitação se encerra na resposta.
'''

import struct
import zlib
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')

_RAIZ = Path(__file__).resolve().parent

_OBRIGATORIOS = [
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo', 'cidade',
    'estado', 'pais', 'valor', 'detalhamento', 'apresentacao', 'nascimento',
    'logradouro', 'numero', 'bairro', 'cep', 'cidade_endereco',
    'estado_endereco', 'cpf', 'rg', 'banco', 'agencia', 'conta',
]
_CAMPOS = _OBRIGATORIOS + ['nivel', 'tipo', 'link', 'complemento']


# --------------------------------------------------------------------- estáticos


@app.get('/')
def index():
    return FileResponse(_RAIZ / 'index.html', media_type='text/html')


@app.get('/static/style.css')
def style_css():
    return FileResponse(_RAIZ / 'style.css', media_type='text/css')


@app.get('/static/app.js')
def app_js():
    return FileResponse(_RAIZ / 'app.js', media_type='application/javascript')


@app.get('/static/usp-logo.png')
def usp_logo():
    caminho = _RAIZ / 'assets' / 'usp-logo.png'
    if caminho.is_file():
        return FileResponse(caminho, media_type='image/png')
    return Response(content=_png_usp(), media_type='image/png')


def _png_usp():
    '''Logotipo mínimo (1x1, azul USP), caso o arquivo não exista.'''
    def pedaco(tipo, dados):
        corpo = tipo + dados
        return struct.pack('>I', len(dados)) + corpo + struct.pack('>I', zlib.crc32(corpo))

    ihdr = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes([0, 0x10, 0x94, 0xAB]))
    png = bytes([0x89]) + b'PNG' + bytes([13, 10, 26, 10])
    return png + pedaco(b'IHDR', ihdr) + pedaco(b'IDAT', idat) + pedaco(b'IEND', b'')


# ------------------------------------------------------------------- formatação


def _texto(valor):
    return '' if valor is None else str(valor).strip()


def _digitos(valor):
    return ''.join(c for c in str(valor) if c.isdigit())


def _moeda(valor):
    d = _digitos(valor)
    if not d:
        return ''
    reais, centavos = divmod(int(d), 100)
    return 'R$ %s,%02d' % ('{:,}'.format(reais).replace(',', '.'), centavos)


def _cpf(valor):
    d = _digitos(valor)
    if len(d) != 11:
        return d
    return '%s.%s.%s-%s' % (d[:3], d[3:6], d[6:9], d[9:])


def _cep(valor):
    d = _digitos(valor)
    if len(d) != 8:
        return d
    return '%s-%s' % (d[:5], d[5:])


def _data(valor):
    d = _digitos(valor)
    if len(d) != 8:
        return d
    return '%s/%s/%s' % (d[:2], d[2:4], d[4:])


@app.get('/formatar/valor')
def formatar_valor(digitado: str = ''):
    return {'formatado': _moeda(digitado)}


@app.get('/formatar/cpf')
def formatar_cpf(digitado: str = ''):
    return {'formatado': _cpf(digitado)}


@app.get('/formatar/cep')
def formatar_cep(digitado: str = ''):
    return {'formatado': _cep(digitado)}


@app.get('/formatar/data')
def formatar_data(digitado: str = ''):
    return {'formatado': _data(digitado)}


# --------------------------------------------------------------------- validação


def _email_valido(email):
    local, arroba, dominio = email.partition('@')
    if not arroba or '@' in dominio:
        return False
    return bool(local) and '.' in dominio and dominio[0] != '.' and dominio[-1] != '.'


def _cpf_valido(d):
    if len(d) != 11:
        return False
    soma = sum(int(d[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    soma = sum(int(d[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    return int(d[9]) == d1 and int(d[10]) == d2


def _partes_data(valor):
    '''(dia, mes, ano) de dd/mm/aaaa ou ddmmaaaa; None em outro formato.'''
    if len(valor) == 10 and valor[2] == '/' and valor[5] == '/':
        numeros = valor[0:2] + valor[3:5] + valor[6:]
    elif len(valor) == 8:
        numeros = valor
    else:
        return None
    if not numeros.isdigit():
        return None
    return int(numeros[0:2]), int(numeros[2:4]), int(numeros[4:])


def _data_existe(partes):
    try:
        date(partes[2], partes[1], partes[0])
        return True
    except ValueError:
        return False


def _validar(carga):
    docente = carga.get('aba') == 'docentes'
    obrigatorios = _OBRIGATORIOS + ([] if docente else ['nivel', 'tipo'])
    erros = []
    if any(_texto(carga.get(c)) == '' for c in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = _texto(carga.get('n_usp'))
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = _texto(carga.get('agencia'))
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = _texto(carga.get('valor'))
    if valor and not (valor.isdigit() and int(valor) > 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = _texto(carga.get('email'))
    if email and not _email_valido(email):
        erros.append('E-mail inválido')

    cpf_texto = _texto(carga.get('cpf'))
    cpf = _digitos(cpf_texto)
    cep_texto = _texto(carga.get('cep'))
    cep = _digitos(cep_texto)
    nascimento = _texto(carga.get('nascimento'))
    partes = _partes_data(nascimento)

    if cpf_texto and len(cpf) != 11:
        erros.append('CPF deve estar no formato 000.000.000-00')
    if cep_texto and len(cep) != 8:
        erros.append('CEP deve estar no formato 00000-000')
    if nascimento and partes is None:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_texto and len(cpf) == 11 and not _cpf_valido(cpf):
        erros.append('CPF inválido')
    if nascimento and partes is not None and not _data_existe(partes):
        erros.append('Data de nascimento inválida')
    return erros


# ------------------------------------------------------------------------ ofício


def _oficio(carga):
    d = {c: _texto(carga.get(c)) for c in _CAMPOS}
    linhas = [
        'Interessada(o): %s - %s' % (d['nome'], d['n_usp']),
        'E-mail: %s' % d['email'],
    ]
    if carga.get('aba') == 'docentes':
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: %s' % d['programa'])
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - %s' % d['tipo'])
        linhas.append('Programa: %s - %s' % (d['programa'], d['nivel']))
    linhas += [
        '',
        'A CCP-%s aprovou na data de hoje, a solicitação de auxílio financeiro para a' % d['programa'],
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: %s' % d['evento'],
        'Período: %s' % d['periodo'],
        'Local: %s - %s - %s' % (d['cidade'], d['estado'], d['pais']),
    ]
    if d['link']:
        linhas.append('Link do evento: %s' % d['link'])
    linhas += [
        'Apresentação de trabalho: %s' % d['apresentacao'],
        'Valor solicitado: %s' % _moeda(d['valor']),
        'Detalhamento: %s' % d['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        '%s, %s' % (d['logradouro'], d['numero']),
    ]
    if d['complemento']:
        linhas.append('Complemento: %s' % d['complemento'])
    linhas += [
        'CEP: %s' % _cep(d['cep']),
        '%s, %s - %s' % (d['bairro'], d['cidade_endereco'], d['estado_endereco']),
        '',
        'Dados para pagamento',
        'Data de nascimento: %s' % _data(d['nascimento']),
        'CPF: %s' % _cpf(d['cpf']),
        'RG / RNM: %s' % d['rg'],
        'Banco: %s' % d['banco'],
        'Agência: %s' % d['agencia'],
        'Conta: %s' % d['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitacao')
def solicitacao(carga: dict):
    erros = _validar(carga)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    return {'titulo': 'Solicitação registrada', 'oficio': _oficio(carga)}
