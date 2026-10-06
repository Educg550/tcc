import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Solicitacao de Auxilio Financeiro - Pos-Graduacao IME-USP')

ROTULOS = {
    'nome': 'NOME COMPLETO - SEM ABREVIAR',
    'n_usp': 'N. USP',
    'programa': 'PROGRAMA',
    'nivel': 'NIVEL',
    'tipo_auxilio': 'TIPO DE AUXILIO',
    'email': 'E-MAIL',
    'evento': 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA',
    'periodo': 'PERIODO DO EVENTO, EXAME OU DEFESA',
    'cidade_evento': 'CIDADE DO EVENTO, EXAME OU DEFESA',
    'estado_evento': 'ESTADO DO EVENTO, EXAME OU DEFESA',
    'pais_evento': 'PAIS DO EVENTO, EXAME OU DEFESA',
    'link_evento': 'LINK DO EVENTO, EXAME OU DEFESA',
    'valor': 'VALOR SOLICITADO (R$)',
    'detalhamento': 'DETALHAMENTO DO PEDIDO',
    'apresentacao': 'IRA APRESENTAR TRABALHO NO EVENTO? QUE TIPO?',
    'data_nascimento': 'DATA DE NASCIMENTO',
    'logradouro': 'LOGRADOURO',
    'numero': 'NUMERO',
    'complemento': 'COMPLEMENTO',
    'bairro': 'BAIRRO',
    'cep': 'CEP',
    'cidade': 'CIDADE',
    'estado': 'ESTADO',
    'cpf': 'CPF (SEPARADOS POR PONTOS E TRACO)',
    'rg_rnm': 'RG / RNM (SEPARADOS POR PONTOS E TRACO)',
    'banco': 'NOME DO BANCO',
    'agencia': 'NUMERO DA AGENCIA',
    'conta': 'NUMERO DA CONTA',
}

OPCIONAIS = ('link_evento', 'complemento')


def _variantes(rotulo):
    slug = re.sub('[^a-z0-9]+', '_', rotulo.lower()).strip('_')
    variantes = {rotulo, slug, slug.replace('_', '')}
    variantes.add(re.sub('_([a-z])', lambda m: m.group(1).upper(), slug))
    if re.search('_[a-z]$', slug):
        variantes.add(re.sub('_[a-z]$', '', slug))
    return variantes


CHAVES = {campo: _variantes(rotulo) | {campo} for campo, rotulo in ROTULOS.items()}


def _pegar(dados, campo):
    for chave in CHAVES[campo]:
        if chave in dados:
            valor = dados[chave]
            return '' if valor is None else str(valor).strip()
    caixas = {chave.lower() for chave in CHAVES[campo]}
    for chave in dados:
        if str(chave).strip().lower() in caixas:
            valor = dados[chave]
            return '' if valor is None else str(valor).strip()
    return None


def _digito_cpf(base):
    soma = 0
    peso = len(base) + 1
    for digito in base:
        soma += int(digito) * peso
        peso = peso - 1
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def _cpf_valido(digitos):
    return _digito_cpf(digitos[:9]) == digitos[9] and _digito_cpf(digitos[:10]) == digitos[10]


def _centavos(texto):
    limpo = re.sub('(?i)^r[$]', '', texto).strip()
    if re.fullmatch('[0-9]+', limpo):
        return int(limpo)
    limpo = limpo.replace('.', '').replace(',', '.')
    try:
        return int(round(float(limpo) * 100))
    except ValueError:
        return None


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return 'R$ {},{}'.format('{:,}'.format(reais).replace(',', '.'), '{:02d}'.format(resto))


def _processar(dados):
    valores = {campo: _pegar(dados, campo) for campo in ROTULOS}
    erros = []
    for campo in ROTULOS:
        if campo in OPCIONAIS:
            continue
        if campo in ('nivel', 'tipo_auxilio') and valores[campo] is None:
            continue
        if not valores[campo]:
            erros.append('Preencha todos os campos')
            break

    if valores['n_usp'] and not re.fullmatch('[0-9]+', valores['n_usp']):
        erros.append('N. USP deve conter apenas números')

    if valores['agencia'] and not re.fullmatch('[0-9]+', valores['agencia']):
        erros.append('Número da agência deve conter apenas números')

    centavos = None
    if valores['valor']:
        centavos = _centavos(valores['valor'])
        if centavos is None or centavos <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
            centavos = None

    if valores['email']:
        partes = valores['email'].split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')

    cpf_formatado = ''
    if valores['cpf']:
        cpf = valores['cpf']
        if re.fullmatch('[0-9]{11}', cpf):
            digitos = cpf
        elif re.fullmatch('[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}', cpf):
            digitos = cpf.replace('.', '').replace('-', '')
        else:
            digitos = None
        if digitos is None:
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(digitos):
            erros.append('CPF inválido')
        else:
            cpf_formatado = '{}.{}.{}-{}'.format(digitos[:3], digitos[3:6], digitos[6:9], digitos[9:])

    cep_formatado = ''
    if valores['cep']:
        cep = valores['cep']
        if re.fullmatch('[0-9]{5}-[0-9]{3}', cep):
            cep_formatado = cep
        elif re.fullmatch('[0-9]{8}', cep):
            cep_formatado = '{}-{}'.format(cep[:5], cep[5:])
        else:
            erros.append('CEP deve estar no formato 00000-000')

    data_formatada = ''
    if valores['data_nascimento']:
        data = valores['data_nascimento']
        dia = None
        if re.fullmatch('[0-9]{2}/[0-9]{2}/[0-9]{4}', data):
            dia, mes, ano = data[:2], data[3:5], data[6:]
        elif re.fullmatch('[0-9]{8}', data):
            dia, mes, ano = data[:2], data[2:4], data[4:]
        else:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        if dia is not None:
            try:
                datetime(int(ano), int(mes), int(dia))
                data_formatada = '{}/{}/{}'.format(dia, mes, ano)
            except ValueError:
                erros.append('Data de nascimento inválida')

    if erros:
        return {'erros': erros}

    de_aluno = valores['nivel'] is not None or valores['tipo_auxilio'] is not None
    return {'titulo': 'Solicitação registrada',
            'oficio': _oficio(valores, cpf_formatado, cep_formatado, data_formatada, centavos, de_aluno)}


def _oficio(v, cpf_formatado, cep_formatado, data_formatada, centavos, de_aluno):
    linhas = ['Interessada(o): {} - {}'.format(v['nome'], v['n_usp']),
              'E-mail: {}'.format(v['email'])]
    if de_aluno:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - {}'.format(v['tipo_auxilio']))
        linhas.append('Programa: {} - {}'.format(v['programa'], v['nivel']))
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: {}'.format(v['programa']))
    linhas.extend([
        '',
        'A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(v['programa']),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: {}'.format(v['evento']),
        'Período: {}'.format(v['periodo']),
        'Local: {} - {} - {}'.format(v['cidade_evento'], v['estado_evento'], v['pais_evento']),
    ])
    if v['link_evento']:
        linhas.append('Link do evento: {}'.format(v['link_evento']))
    linhas.extend([
        'Apresentação de trabalho: {}'.format(v['apresentacao']),
        'Valor solicitado: {}'.format(_moeda(centavos)),
        'Detalhamento: {}'.format(v['detalhamento']),
        '',
        'Endereço da(o) interessada(o)',
        '{}, {}'.format(v['logradouro'], v['numero']),
    ])
    if v['complemento']:
        linhas.append('Complemento: {}'.format(v['complemento']))
    linhas.extend([
        'CEP: {}'.format(cep_formatado),
        '{}, {} - {}'.format(v['bairro'], v['cidade'], v['estado']),
        '',
        'Dados para pagamento',
        'Data de nascimento: {}'.format(data_formatada),
        'CPF: {}'.format(cpf_formatado),
        'RG / RNM: {}'.format(v['rg_rnm']),
        'Banco: {}'.format(v['banco']),
        'Agência: {}'.format(v['agencia']),
        'Conta: {}'.format(v['conta']),
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.get('/', response_class=HTMLResponse)
def pagina():
    return (BASE / 'index.html').read_text(encoding='utf-8')


@app.post('/api/solicitacao')
async def solicitacao(request: Request):
    dados = {}
    try:
        corpo = await request.()
        if isinstance(corpo, dict):
            dados = corpo
    except Exception:
        formulario = await request.form()
        dados = dict(formulario)
    return JSONResponse(_processar(dados))


app.mount('/assets', StaticFiles(directory=BASE / 'assets', check_dir=False), name='assets')
app.mount('/', StaticFiles(directory=BASE, html=True), name='estaticos')
