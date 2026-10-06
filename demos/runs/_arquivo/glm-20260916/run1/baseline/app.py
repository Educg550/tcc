import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

PASTA = Path(__file__).resolve().parent

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

OBRIGATORIOS_COMUNS = [
    'nome', 'n_usp', 'programa', 'email', 'evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor',
    'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro',
    'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg',
    'banco', 'agencia', 'conta',
]


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for n in range(9, 11):
        soma = sum(digitos[i] * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != digitos[n]:
            return False
    return True


def centavos_do_valor(texto):
    limpo = texto.replace('R$', '').replace('.', '').replace(',', '').replace(' ', '')
    if not limpo.isdigit():
        return None
    return int(limpo)


def formatar_valor(centavos):
    reais, cent = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{cent:02d}'


def montar_oficio(perfil, v, valor):
    programa = v['programa']
    if perfil == 'alunos':
        assunto = 'Solicitação de Auxílio Financeiro - ' + v['tipo_auxilio']
        linha_programa = 'Programa: {} - {}'.format(programa, v['nivel'])
    else:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + programa

    linhas = [
        'Interessada(o): {} - {}'.format(v['nome'], v['n_usp']),
        'E-mail: ' + v['email'],
        'Assunto: ' + assunto,
        linha_programa,
        '',
        'A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(programa),
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + v['evento'],
        'Período: ' + v['periodo'],
        'Local: {} - {} - {}'.format(v['cidade_evento'], v['estado_evento'], v['pais_evento']),
    ]
    if v['link']:
        linhas.append('Link do evento: ' + v['link'])
    linhas += [
        'Apresentação de trabalho: ' + v['apresentacao'],
        'Valor solicitado: ' + valor,
        'Detalhamento: ' + v['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        '{}, {}'.format(v['logradouro'], v['numero']),
    ]
    if v['complemento']:
        linhas.append('Complemento: ' + v['complemento'])
    linhas += [
        'CEP: ' + v['cep'],
        '{}, {} - {}'.format(v['bairro'], v['cidade'], v['estado']),
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + v['data_nascimento'],
        'CPF: ' + v['cpf'],
        'RG / RNM: ' + v['rg'],
        'Banco: ' + v['banco'],
        'Agência: ' + v['agencia'],
        'Conta: ' + v['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
async def registrar_solicitacao(request: Request):
    try:
        dados = await request.()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}

    perfil = dados.get('perfil')
    if perfil not in ('alunos', 'docentes'):
        perfil = 'alunos'

    obrigatorios = OBRIGATORIOS_COMUNS + (['nivel', 'tipo_auxilio'] if perfil == 'alunos' else [])
    chaves = set(obrigatorios) | {'link', 'complemento'}
    v = {c: str(dados.get(c) or '').strip() for c in chaves}

    erros = []
    if any(not v[c] for c in obrigatorios):
        erros.append('Preencha todos os campos')

    if v['n_usp'] and not v['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if v['agencia'] and not v['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')

    centavos = centavos_do_valor(v['valor']) if v['valor'] else None
    if v['valor'] and (centavos is None or centavos <= 0):
        erros.append('Valor solicitado deve ser maior que 0')

    if v['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+', v['email']):
        erros.append('E-mail inválido')

    cpf_ok = bool(re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', v['cpf']))
    if v['cpf'] and not cpf_ok:
        erros.append('CPF deve estar no formato 000.000.000-00')
    if v['cep'] and not re.fullmatch(r'\d{5}-\d{3}', v['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    data_ok = bool(re.fullmatch(r'\d{2}/\d{2}/\d{4}', v['data_nascimento']))
    if v['data_nascimento'] and not data_ok:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_ok and not cpf_valido(v['cpf']):
        erros.append('CPF inválido')
    if data_ok:
        try:
            datetime.strptime(v['data_nascimento'], '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    if erros:
        return {'erros': erros, 'oficio': None}

    return {'erros': [], 'oficio': montar_oficio(perfil, v, formatar_valor(centavos))}


app.mount('/', StaticFiles(directory=PASTA, html=True, check_dir=False), name='static')
