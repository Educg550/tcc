import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

BASE = Path(__file__).resolve().parent

OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email',
    'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento',
    'pais_evento', 'valor_solicitado', 'detalhamento', 'apresentacao',
    'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade',
    'estado', 'cpf', 'rg_rnm', 'banco', 'agencia', 'conta',
]
OBRIGATORIOS_ALUNOS = ['nivel', 'tipo_auxilio']

CPF_FORMATO = re.compile(r'\d{3}\.\d{3}\.\d{3}-\d{2}')
CEP_FORMATO = re.compile(r'\d{5}-\d{3}')
DATA_FORMATO = re.compile(r'\d{2}/\d{2}/\d{4}')


def digito_verificador(digitos, peso_inicial):
    soma = sum(int(d) * p for d, p in zip(digitos, range(peso_inicial, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf):
    numeros = [int(d) for d in cpf if d.isdigit()]
    if len(numeros) != 11:
        return False
    dv1 = digito_verificador(numeros[:9], 10)
    dv2 = digito_verificador(numeros[:10], 11)
    return numeros[9] == dv1 and numeros[10] == dv2


def formatar_moeda(digitos_valor):
    centavos = int(digitos_valor)
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def validar(campos, perfil):
    erros = []
    obrigatorios = OBRIGATORIOS + (OBRIGATORIOS_ALUNOS if perfil == 'alunos' else [])
    if any(not campos.get(nome) for nome in obrigatorios):
        erros.append('Preencha todos os campos')

    n_usp = campos.get('n_usp', '')
    if n_usp and not n_usp.isdigit():
        erros.append('N. USP deve conter apenas números')

    agencia = campos.get('agencia', '')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = campos.get('valor_solicitado', '')
    centavos = re.sub(r'\D', '', valor)
    if valor and (not centavos or int(centavos) == 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = campos.get('email', '')
    if email and ('@' not in email or not email.split('@', 1)[1]):
        erros.append('E-mail inválido')

    cpf = campos.get('cpf', '')
    if cpf and not CPF_FORMATO.fullmatch(cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif cpf and not cpf_valido(cpf):
        erros.append('CPF inválido')

    cep = campos.get('cep', '')
    if cep and not CEP_FORMATO.fullmatch(cep):
        erros.append('CEP deve estar no formato 00000-000')

    data = campos.get('data_nascimento', '')
    if data and not DATA_FORMATO.fullmatch(data):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    elif data:
        try:
            datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')

    return erros


def redigir_oficio(c, perfil):
    nome = c['nome_completo']
    n_usp = c['n_usp']
    email = c['email']
    programa = c['programa']
    valor = formatar_moeda(re.sub(r'\D', '', c['valor_solicitado']))
    if perfil == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = 'Programa: ' + programa
    else:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - ' + c['tipo_auxilio']
        linha_programa = 'Programa: ' + programa + ' - ' + c['nivel']

    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        'Evento: ' + c['nome_evento'],
        'Período: ' + c['periodo_evento'],
        'Local: ' + c['cidade_evento'] + ' - ' + c['estado_evento'] + ' - ' + c['pais_evento'],
    ]
    if c.get('link_evento'):
        linhas.append('Link do evento: ' + c['link_evento'])
    linhas += [
        'Apresentação de trabalho: ' + c['apresentacao'],
        'Valor solicitado: ' + valor,
        'Detalhamento: ' + c['detalhamento'],
        '',
        'Endereço da(o) interessada(o)',
        c['logradouro'] + ', ' + c['numero'],
    ]
    if c.get('complemento'):
        linhas.append('Complemento: ' + c['complemento'])
    linhas += [
        'CEP: ' + c['cep'],
        c['bairro'] + ', ' + c['cidade'] + ' - ' + c['estado'],
        '',
        'Dados para pagamento',
        'Data de nascimento: ' + c['data_nascimento'],
        'CPF: ' + c['cpf'],
        'RG / RNM: ' + c['rg_rnm'],
        'Banco: ' + c['banco'],
        'Agência: ' + c['agencia'],
        'Conta: ' + c['conta'],
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def receber_solicitacao(payload: dict):
    perfil = payload.get('perfil', 'alunos')
    campos = {nome: str(valor or '').strip() for nome, valor in payload.items() if nome != 'perfil'}
    erros = validar(campos, perfil)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': redigir_oficio(campos, perfil)}


app.mount('/assets', StaticFiles(directory=BASE / 'assets'), name='assets')
app.mount('/', StaticFiles(directory=BASE, html=True), name='site')
