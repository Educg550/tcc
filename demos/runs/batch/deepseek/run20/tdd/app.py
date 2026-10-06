import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

ALIASES = {
    'aba': ('aba', 'tipo', 'tipo_formulario', 'formulario', 'solicitante', 'perfil', 'categoria'),
    'nome': ('nome', 'nome_completo', 'NOME COMPLETO - SEM ABREVIAR'),
    'n_usp': ('n_usp', 'nusp', 'numero_usp'),
    'programa': ('programa',),
    'nivel': ('nivel',),
    'tipo_auxilio': ('tipo_auxilio',),
    'email': ('email', 'e_mail'),
    'evento': ('evento', 'nome_evento'),
    'periodo': ('periodo', 'periodo_evento'),
    'cidade_evento': ('cidade_evento',),
    'estado_evento': ('estado_evento',),
    'pais_evento': ('pais_evento',),
    'link': ('link', 'link_evento'),
    'valor': ('valor', 'valor_solicitado'),
    'detalhamento': ('detalhamento',),
    'apresentacao': ('apresentacao', 'apresenta_trabalho'),
    'nascimento': ('data_nascimento', 'nascimento'),
    'logradouro': ('logradouro',),
    'numero': ('numero',),
    'complemento': ('complemento',),
    'bairro': ('bairro',),
    'cep': ('cep',),
    'cidade': ('cidade',),
    'estado': ('estado',),
    'cpf': ('cpf',),
    'rg': ('rg', 'rg_rnm'),
    'banco': ('banco', 'nome_banco'),
    'agencia': ('agencia', 'numero_agencia'),
    'conta': ('conta', 'numero_conta'),
}

OBRIGATORIOS = (
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo', 'cidade_evento',
    'estado_evento', 'pais_evento', 'valor', 'detalhamento', 'apresentacao',
    'nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
)

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')

app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')


@app.get('/', include_in_schema=False)
@app.get('/index.html', include_in_schema=False)
def pagina():
    return FileResponse(BASE / 'index.html', media_type='text/html')


@app.get('/style.css', include_in_schema=False)
def estilos():
    return FileResponse(BASE / 'style.css', media_type='text/css')


@app.get('/app.js', include_in_schema=False)
def script():
    return FileResponse(BASE / 'app.js', media_type='application/javascript')


def _campo(dados, chave):
    for alias in ALIASES[chave]:
        if alias in dados:
            valor = dados[alias]
            return '' if valor is None else str(valor).strip()
    return ''


def _cpf_valido(cpf):
    numeros = [int(digito) for digito in re.sub(r'[^0-9]', '', cpf)]
    for posicao in (9, 10):
        soma = sum(numeros[i] * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != numeros[posicao]:
            return False
    return True


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def _validar(aba, campos):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba == 'ALUNOS':
        obrigatorios += ['nivel', 'tipo_auxilio']
    if any(not campos[chave] for chave in obrigatorios):
        erros.append('Preencha todos os campos')
    if campos['n_usp'] and not re.fullmatch(r'[0-9]+', campos['n_usp']):
        erros.append('N. USP deve conter apenas números')
    if campos['agencia'] and not re.fullmatch(r'[0-9]+', campos['agencia']):
        erros.append('Número da agência deve conter apenas números')
    centavos = re.sub(r'[^0-9]', '', campos['valor'])
    if campos['valor'] and (not centavos or int(centavos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')
    if campos['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', campos['email']):
        erros.append('E-mail inválido')
    if campos['cpf']:
        if re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', campos['cpf']):
            if not _cpf_valido(campos['cpf']):
                erros.append('CPF inválido')
        else:
            erros.append('CPF deve estar no formato 000.000.000-00')
    if campos['cep'] and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', campos['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if campos['nascimento']:
        if re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', campos['nascimento']):
            dia, mes, ano = (int(parte) for parte in campos['nascimento'].split('/'))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append('Data de nascimento inválida')
        else:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    return erros


def _oficio(aba, campos):
    if aba == 'DOCENTES':
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        programa = campos['programa']
    else:
        assunto = 'Solicitação de Auxílio Financeiro - ' + campos['tipo_auxilio']
        programa = campos['programa'] + ' - ' + campos['nivel']
    valor = _moeda(int(re.sub(r'[^0-9]', '', campos['valor'])))
    linhas = [
        'Interessada(o): ' + campos['nome'] + ' - ' + campos['n_usp'],
        'E-mail: ' + campos['email'],
        'Assunto: ' + assunto,
        'Programa: ' + programa,
        '',
        'A CCP-' + campos['programa'] + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + campos['evento'],
        'Período: ' + campos['periodo'],
        'Local: ' + campos['cidade_evento'] + ' - ' + campos['estado_evento'] + ' - ' + campos['pais_evento'],
    ]
    if campos['link']:
        linhas.append('Link do evento: ' + campos['link'])
    linhas += [
        'Apresentação de trabalho: ' + campos['apresentacao'],
        'Valor solicitado: ' + valor,
        'Detalhamento: ' + campos['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        campos['logradouro'] + ', ' + campos['numero'],
    ]
    if campos['complemento']:
        linhas.append('Complemento: ' + campos['complemento'])
    linhas += [
        'CEP: ' + campos['cep'],
        campos['bairro'] + ', ' + campos['cidade'] + ' - ' + campos['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + campos['nascimento'],
        'CPF: ' + campos['cpf'],
        'RG / RNM: ' + campos['rg'],
        'Banco: ' + campos['banco'],
        'Agência: ' + campos['agencia'],
        'Conta: ' + campos['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitar')
async def solicitar(request: Request):
    try:
        dados = await request.json()
    except Exception:
        dados = dict(await request.form())
    if not isinstance(dados, dict):
        dados = {}
    campos = {chave: _campo(dados, chave) for chave in ALIASES}
    aba = campos['aba'].upper()
    if aba not in ('ALUNOS', 'DOCENTES'):
        aba = 'ALUNOS'
    erros = _validar(aba, campos)
    if erros:
        return {'erros': erros, 'oficio': ''}
    return {'erros': [], 'oficio': _oficio(aba, campos)}
