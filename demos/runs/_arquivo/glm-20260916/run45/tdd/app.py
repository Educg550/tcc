import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

CAMPOS = [
    'nome_completo', 'numero_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
    'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento',
    'link_evento', 'valor_solicitado', 'detalhamento', 'apresentacao_trabalho',
    'data_nascimento', 'logradouro', 'numero', 'complemento', 'bairro', 'cep',
    'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco', 'numero_agencia', 'numero_conta',
]

OBRIGATORIOS = [
    campo for campo in CAMPOS
    if campo not in ('nivel', 'tipo_auxilio', 'link_evento', 'complemento')
]


@app.get('/')
async def pagina():
    return FileResponse(RAIZ / 'index.html', media_type='text/html')


@app.get('/style.css')
async def estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
async def script():
    return FileResponse(RAIZ / 'app.js', media_type='application/javascript')


if (RAIZ / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')


@app.post('/solicitacao')
async def receber_solicitacao(request: Request):
    dados = await _corpo(request)
    aluno = 'nivel' in dados or 'tipo_auxilio' in dados
    valores = {campo: _texto(dados, campo) for campo in CAMPOS}
    erros = _validar(valores, aluno)
    if erros:
        return JSONResponse({'ok': False, 'erros': erros})
    return JSONResponse({'ok': True, 'oficio': _oficio(valores, aluno)})


async def _corpo(request: Request):
    try:
        if '' in request.headers.get('content-type', ''):
            corpo = await request.()
            return corpo if isinstance(corpo, dict) else {}
        return dict(await request.form())
    except Exception:
        return {}


def _texto(dados, campo):
    valor = dados.get(campo)
    return '' if valor is None else str(valor)


def _validar(v, aluno):
    erros = []
    obrigatorios = OBRIGATORIOS + (['nivel', 'tipo_auxilio'] if aluno else [])
    if any(not v[campo].strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if v['numero_usp'].strip() and not re.fullmatch(r'[0-9]+', v['numero_usp'].strip()):
        erros.append('N. USP deve conter apenas números')

    if v['numero_agencia'].strip() and not re.fullmatch(r'[0-9]+', v['numero_agencia'].strip()):
        erros.append('Número da agência deve conter apenas números')

    centavos = _centavos(v['valor_solicitado'])
    if v['valor_solicitado'].strip() and (centavos is None or centavos <= 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = v['email'].strip()
    if email and ('@' not in email or not email.rsplit('@', 1)[1].strip()):
        erros.append('E-mail inválido')

    cpf = v['cpf'].strip()
    if cpf and not re.fullmatch(r'[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}', cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not _cpf_valido(cpf):
        erros.append('CPF inválido')

    cep = v['cep'].strip()
    if cep and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    data = v['data_nascimento'].strip()
    if data and not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', data):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data:
        try:
            datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def _centavos(texto):
    digitos = re.sub('[^0-9]', '', texto)
    return int(digitos) if digitos else None


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + format(reais, ',').replace(',', '.') + ',' + f'{resto:02d}'


def _cpf_valido(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    dig1 = (sum(a * b for a, b in zip(digitos[:9], range(10, 1, -1))) * 10) % 11 % 10
    dig2 = (sum(a * b for a, b in zip(digitos[:10], range(11, 1, -1))) * 10) % 11 % 10
    return digitos[9] == dig1 and digitos[10] == dig2


def _oficio(v, aluno):
    if aluno:
        assunto = 'Solicitação de Auxílio Financeiro - ' + v['tipo_auxilio']
        linha_programa = 'Programa: ' + v['programa'] + ' - ' + v['nivel']
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + v['programa']

    linhas = [
        'Interessada(o): ' + v['nome_completo'] + ' - ' + v['numero_usp'],
        'E-mail: ' + v['email'],
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-' + v['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + v['nome_evento'],
        'Período: ' + v['periodo_evento'],
        'Local: ' + v['cidade_evento'] + ' - ' + v['estado_evento'] + ' - ' + v['pais_evento'],
    ]
    if v['link_evento'].strip():
        linhas.append('Link do evento: ' + v['link_evento'])
    linhas += [
        'Apresentação de trabalho: ' + v['apresentacao_trabalho'],
        'Valor solicitado: ' + _moeda(_centavos(v['valor_solicitado'])),
        'Detalhamento: ' + v['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        v['logradouro'] + ', ' + v['numero'],
    ]
    if v['complemento'].strip():
        linhas.append('Complemento: ' + v['complemento'])
    linhas += [
        'CEP: ' + v['cep'],
        v['bairro'] + ', ' + v['cidade'] + ' - ' + v['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + v['data_nascimento'],
        'CPF: ' + v['cpf'],
        'RG / RNM: ' + v['rg_rnm'],
        'Banco: ' + v['nome_banco'],
        'Agência: ' + v['numero_agencia'],
        'Conta: ' + v['numero_conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)
