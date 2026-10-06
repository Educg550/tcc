'''Backend do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Serve a página estática (index.html, style.css, app.js e o logotipo) e recebe
a solicitação em POST /api/solicitacao. Toda a validação acontece aqui: com
erro, responde a lista de mensagens; válido, responde o ofício redigido com
os dados no lugar dos marcadores. Nada é gravado.
'''

import re
import struct
import zlib
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

PASTA = Path(__file__).resolve().parent

OPCIONAIS = {'link', 'complemento'}
CAMPOS_DE_DOCENTES = {'nivel', 'tipo'}
CAMPOS = (
    'nome', 'nusp', 'programa', 'nivel', 'tipo', 'email', 'evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'link', 'valor',
    'detalhe', 'apresenta', 'data_nascimento', 'logradouro', 'numero',
    'complemento', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg', 'banco',
    'agencia', 'conta',
)

_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+$')
_DATA = re.compile(r'^\d{2}/\d{2}/\d{4}$')

app = FastAPI(title='Solicitação de Auxílio Financeiro — IME-USP')


async def _dados(request: Request):
    tipo = (request.headers.get('content-type') or '').split(';')[0].strip().lower()
    if tipo == 'application/x-www-form-urlencoded':
        formulario = await request.form()
        bruto = {chave: formulario[chave] for chave in formulario.keys()}
    else:
        try:
            bruto = await request.()
        except Exception:
            bruto = {}
    if not isinstance(bruto, dict):
        return {}
    return {str(chave): '' if valor is None else str(valor)
            for chave, valor in bruto.items()}


def _obrigatorios_preenchidos(dados, docente):
    for campo in CAMPOS:
        if campo in OPCIONAIS or (docente and campo in CAMPOS_DE_DOCENTES):
            continue
        if not dados.get(campo, '').strip():
            return False
    return True


def _cpf_valido(digitos):
    def digito(base, inicio):
        soma = sum(int(caractere) * peso
                   for caractere, peso in zip(base, range(inicio, 1, -1)))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    return (digito(digitos[:9], 10) == digitos[9]
            and digito(digitos[:10], 11) == digitos[10])


def _centavos_do_valor(bruto):
    texto = bruto.strip().replace('R$', '').strip()
    if not texto:
        return None
    if ',' in texto or '.' in texto:
        try:
            centavos = round(float(texto.replace('.', '').replace(',', '.')) * 100)
        except ValueError:
            return None
    elif texto.isdigit():
        centavos = int(texto)
    else:
        return None
    return centavos if centavos > 0 else None


def _validar(dados):
    erros = []
    docente = 'nivel' not in dados and 'tipo' not in dados

    if not _obrigatorios_preenchidos(dados, docente):
        erros.append('Preencha todos os campos')

    nusp = dados.get('nusp', '').strip()
    if nusp and not nusp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = dados.get('agencia', '').strip()
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    centavos = None
    valor = dados.get('valor', '').strip()
    if valor:
        centavos = _centavos_do_valor(valor)
        if centavos is None:
            erros.append('Valor solicitado deve ser maior que 0')

    email = dados.get('email', '').strip()
    if email and not _EMAIL.match(email):
        erros.append('E-mail inválido')

    cpf = re.sub(r'\D', '', dados.get('cpf', ''))
    if cpf:
        if len(cpf) != 11:
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = re.sub(r'\D', '', dados.get('cep', ''))
    if cep and len(cep) != 8:
        erros.append('CEP deve estar no formato 00000-000')

    data = dados.get('data_nascimento', '').strip()
    if data:
        if not _DATA.match(data):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros, docente, centavos, cpf, cep


def _formatar_centavos(centavos):
    reais, resto = divmod(centavos, 100)
    milhar = '{:,}'.format(reais).replace(',', '.')
    return 'R$ {},{:02d}'.format(milhar, resto)


def _oficio(dados, docente, centavos, cpf, cep):
    programa = dados.get('programa', '').strip()
    linhas = [
        'Interessada(o): {} - {}'.format(dados.get('nome', '').strip(),
                                         dados.get('nusp', '').strip()),
        'E-mail: {}'.format(dados.get('email', '').strip()),
    ]
    if docente:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: {}'.format(programa))
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - {}'.format(
            dados.get('tipo', '').strip()))
        linhas.append('Programa: {} - {}'.format(programa, dados.get('nivel', '').strip()))
    linhas += [
        '',
        'A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(programa),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: {}'.format(dados.get('evento', '').strip()),
        'Período: {}'.format(dados.get('periodo', '').strip()),
        'Local: {} - {} - {}'.format(dados.get('cidade_evento', '').strip(),
                                     dados.get('estado_evento', '').strip(),
                                     dados.get('pais_evento', '').strip()),
    ]
    link = dados.get('link', '').strip()
    if link:
        linhas.append('Link do evento: {}'.format(link))
    linhas += [
        'Apresentação de trabalho: {}'.format(dados.get('apresenta', '').strip()),
        'Valor solicitado: {}'.format(_formatar_centavos(centavos)),
        'Detalhamento: {}'.format(dados.get('detalhe', '').strip()),
        '',
        'Endereço da(o) interessada(o)',
        '{}, {}'.format(dados.get('logradouro', '').strip(),
                        dados.get('numero', '').strip()),
    ]
    complemento = dados.get('complemento', '').strip()
    if complemento:
        linhas.append('Complemento: {}'.format(complemento))
    linhas += [
        'CEP: {}'.format('{}-{}'.format(cep[:5], cep[5:]) if cep
                         else dados.get('cep', '').strip()),
        '{}, {} - {}'.format(dados.get('bairro', '').strip(),
                             dados.get('cidade', '').strip(),
                             dados.get('estado', '').strip()),
        '',
        'Dados para pagamento',
        'Data de nascimento: {}'.format(dados.get('data_nascimento', '').strip()),
        'CPF: {}.{}.{}-{}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:]),
        'RG / RNM: {}'.format(dados.get('rg', '').strip()),
        'Banco: {}'.format(dados.get('banco', '').strip()),
        'Agência: {}'.format(dados.get('agencia', '').strip()),
        'Conta: {}'.format(dados.get('conta', '').strip()),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


_png = None


def _png_solida(largura, altura, rgb):
    def bloco(tipo, dados):
        pedaco = tipo + dados
        return (struct.pack('>I', len(dados)) + pedaco
                + struct.pack('>I', zlib.crc32(pedaco) & 0xFFFFFFFF))

    linha = b'\x00' + bytes(rgb) * largura
    cabecalho = struct.pack('>IIBBBBB', largura, altura, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n'
            + bloco(b'IHDR', cabecalho)
            + bloco(b'IDAT', zlib.compress(linha * altura))
            + bloco(b'IEND', b''))


@app.get('/')
def pagina_inicial():
    return FileResponse(PASTA / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(PASTA / 'style.css', media_type='text/css')


@app.get('/app.js')
def roteiro_da_pagina():
    return FileResponse(PASTA / 'app.js', media_type='text/javascript')


@app.get('/assets/usp-logo.png')
def logotipo():
    global _png
    arquivo = PASTA / 'assets' / 'usp-logo.png'
    if arquivo.is_file():
        return FileResponse(arquivo, media_type='image/png')
    if _png is None:
        _png = _png_solida(132, 44, (16, 148, 171))
    return Response(content=_png, media_type='image/png')


@app.post('/api/solicitacao')
async def solicitar(request: Request):
    dados = await _dados(request)
    erros, docente, centavos, cpf, cep = _validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    return {'oficio': _oficio(dados, docente, centavos, cpf, cep)}
