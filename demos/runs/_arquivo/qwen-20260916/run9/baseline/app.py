import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

event_fields = [
    'nome_completo',
    'nusp',
    'programa',
    'nivel',
    'tipo_auxilio',
    'email',
    'nome_evento',
    'periodo_evento',
    'cidade_evento',
    'estado_evento',
    'pais_evento',
    'link_evento',
    'valor_solicitado',
    'detalhamento',
    'apresentar_trabalho',
]

address_fields = [
    'data_nascimento',
    'logradouro',
    'numero',
    'complemento',
    'bairro',
    'cep',
    'cidade',
    'estado',
]

payment_fields = [
    'cpf',
    'rg_rnm',
    'banco',
    'agencia',
    'conta',
]

all_fields = event_fields + address_fields + payment_fields


def validate_cpf(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11:
        return False
    if d == [d[0]] * 11:
        return False
    s = sum(d[i] * (10 - i) for i in range(9))
    d1 = (s * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != d[9]:
        return False
    s = sum(d[i] * (11 - i) for i in range(10))
    d2 = (s * 10) % 11
    if d2 == 10:
        d2 = 0
    return d2 == d[10]


def validate_date(d):
    parts = d.split('/')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return False
    dd, mm, yyyy = map(int, parts)
    if not (1 <= mm <= 12):
        return False
    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dd <= days_in_month[mm - 1]


def format_money(cents_str):
    cents = int(cents_str)
    if cents == 0:
        return 'R$ 0,00'
    neg = cents < 0
    cents = abs(cents)
    integer_part = cents // 100
    cents_part = cents % 100
    formatted_int = format(integer_part, ',d').replace(',', '.')
    result = f'R$ {formatted_int},{cents_part:02d}'
    if neg:
        result = '-' + result
    return result


def build_oficio(data):
    nome = data.get('nome_completo', '')
    nusp = data.get('nusp', '')
    email = data.get('email', '')
    programa = data.get('programa', '')
    nivel = data.get('nivel', '')
    tipo_auxilio = data.get('tipo_auxilio', '')
    nome_evento = data.get('nome_evento', '')
    periodo_evento = data.get('periodo_evento', '')
    cidade_evento = data.get('cidade_evento', '')
    estado_evento = data.get('estado_evento', '')
    pais_evento = data.get('pais_evento', '')
    link_evento = data.get('link_evento', '')
    valor_solicitado = data.get('valor_solicitado', '')
    detalhamento = data.get('detalhamento', '')
    apresentar_trabalho = data.get('apresentar_trabalho', '')
    logradouro = data.get('logradouro', '')
    numero = data.get('numero', '')
    complemento = data.get('complemento', '')
    bairro = data.get('bairro', '')
    cidade = data.get('cidade', '')
    estado = data.get('estado', '')
    cep = data.get('cep', '')
    data_nascimento = data.get('data_nascimento', '')
    cpf = data.get('cpf', '')
    rg_rnm = data.get('rg_rnm', '')
    banco = data.get('banco', '')
    agencia = data.get('agencia', '')
    conta = data.get('conta', '')

    linhas = []
    linhas.append(f'Interessada(o): {nome} - {nusp}')
    linhas.append(f'E-mail: {email}')

    if tipo_auxilio:
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}')
        linhas.append(f'Programa: {programa} - {nivel}')
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {programa}')

    linhas.append('')
    linhas.append('A CCP-' + programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a')
    linhas.append('interessada(o) acima, conforme segue:')
    linhas.append('')
    linhas.append('Dados do evento')
    linhas.append(f'Evento: {nome_evento}')
    linhas.append(f'Período: {periodo_evento}')
    linhas.append(f'Local: {cidade_evento} - {estado_evento} - {pais_evento}')
    if link_evento:
        linhas.append(f'Link do evento: {link_evento}')
    linhas.append(f'Apresentação de trabalho: {apresentar_trabalho}')
    linhas.append(f'Valor solicitado: {valor_solicitado}')
    linhas.append(f'Detalhamento: {detalhamento}')
    linhas.append('')
    linhas.append('Endereço da(o) interessada(o)')
    linhas.append(f'{logradouro}, {numero}')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.append(f'CEP: {cep}')
    linhas.append(f'{bairro}, {cidade} - {estado}')
    linhas.append('')
    linhas.append('Dados para pagamento')
    linhas.append(f'Data de nascimento: {data_nascimento}')
    linhas.append(f'CPF: {cpf}')
    linhas.append(f'RG / RNM: {rg_rnm}')
    linhas.append(f'Banco: {banco}')
    linhas.append(f'Agência: {agencia}')
    linhas.append(f'Conta: {conta}')
    linhas.append('')
    linhas.append('Encaminhe-se ao Serviço Financeiro para providências.')

    return '\n'.join(linhas)


@app.post('/api/solicitar')
async def solicitar(request: Request):
    body = await request.body()
    if not body:
        return JSONResponse(content={'success': False, 'errors': ['Preencha todos os campos']})

    data = json.loads(body)
    aba = data.pop('aba', 'alunos')

    if aba == 'docentes':
        data['nivel'] = ''
        data['tipo_auxilio'] = ''

    errors = []

    required_fields = [f for f in all_fields if f not in ('link_evento', 'complemento')]
    if any(not data.get(f, '').strip() for f in required_fields):
        errors.append('Preencha todos os campos')

    if not errors:
        nusp = data['nusp'].strip()
        if not nusp.isdigit():
            errors.append('N. USP deve conter apenas números')

        agencia = data['agencia'].strip()
        if not agencia.isdigit():
            errors.append('Número da agência deve conter apenas números')

        valor = data['valor_solicitado'].strip()
        is_valid_value = False
        try:
            v = int(valor)
            if v > 0:
                is_valid_value = True
                data['valor_solicitado'] = format_money(valor)
        except (ValueError, TypeError):
            pass
        if not is_valid_value:
            errors.append('Valor solicitado deve ser maior que 0')

        email = data['email'].strip()
        if '@' not in email:
            errors.append('E-mail inválido')
        else:
            domain = email.split('@')[1]
            if not domain:
                errors.append('E-mail inválido')

        cpf = data['cpf'].strip()
        if len(cpf) != 14 or cpf[3] != '.' or cpf[7] != '.' or cpf[11] != '-':
            errors.append('CPF deve estar no formato 000.000.000-00')
        else:
            if cpf[:3].isdigit() and cpf[4:7].isdigit() and cpf[8:11].isdigit() and cpf[12:].isdigit():
                if not validate_cpf(cpf):
                    errors.append('CPF inválido')
            else:
                errors.append('CPF deve estar no formato 000.000.000-00')

        cep = data['cep'].strip()
        if len(cep) != 9 or cep[5] != '-':
            errors.append('CEP deve estar no formato 00000-000')
        elif not (cep[:5].isdigit() and cep[6:].isdigit()):
            errors.append('CEP deve estar no formato 00000-000')

        dt = data['data_nascimento'].strip()
        if len(dt) != 10 or dt[2] != '/' or dt[5] != '/':
            errors.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not (dt[:2].isdigit() and dt[3:5].isdigit() and dt[6:].isdigit()):
            errors.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            if not validate_date(dt):
                errors.append('Data de nascimento inválida')

    if errors:
        return JSONResponse(content={'success': False, 'errors': errors})

    oficio = build_oficio(data)
    return JSONResponse(content={'success': True, 'oficio': oficio})


static_dir = Path(__file__).parent / 'static'
app.mount('/', StaticFiles(directory=static_dir, html=True), name='static')
