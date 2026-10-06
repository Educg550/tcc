from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

REGRAS = {
    'nome': [('obrigatorio', 'Preencha todos os campos'), ('comprimento', 2, 'Nome completo deve ter no mínimo 2 caracteres'), ('texto', 'Nome completo não pode conter números')],
    'nusp': [('obrigatorio', 'Preencha todos os campos'), ('digitos', 'N. USP deve conter apenas números')],
    'programa': [('obrigatorio', 'Preencha todos os campos')],
    'nivel': [('obrigatorio', 'Preencha todos os campos')],
    'tipo': [('obrigatorio', 'Preencha todos os campos')],
    'email': [('obrigatorio', 'Preencha todos os campos'), ('email', 'E-mail inválido')],
    'evento': [('obrigatorio', 'Preencha todos os campos')],
    'periodo': [('obrigatorio', 'Preencha todos os campos')],
    'cidade_evento': [('obrigatorio', 'Preencha todos os campos')],
    'estado_evento': [('obrigatorio', 'Preencha todos os campos')],
    'pais_evento': [('obrigatorio', 'Preencha todos os campos')],
    'valor': [('obrigatorio', 'Preencha todos os campos'), ('valor', 'Valor solicitado deve ser maior que 0')],
    'detalhamento': [('obrigatorio', 'Preencha todos os campos')],
    'apresentacao': [('obrigatorio', 'Preencha todos os campos')],
    'nascimento': [('obrigatorio', 'Preencha todos os campos'), ('data_formato', 'Data de nascimento deve estar no formato dd/mm/aaaa'), ('data_valida', 'Data de nascimento inválida')],
    'logradouro': [('obrigatorio', 'Preencha todos os campos')],
    'numero': [('obrigatorio', 'Preencha todos os campos')],
    'bairro': [('obrigatorio', 'Preencha todos os campos')],
    'cep': [('obrigatorio', 'Preencha todos os campos'), ('cep', 'CEP deve estar no formato 00000-000')],
    'cidade': [('obrigatorio', 'Preencha todos os campos')],
    'estado': [('obrigatorio', 'Preencha todos os campos')],
    'cpf': [('obrigatorio', 'Preencha todos os campos'), ('cpf_formato', 'CPF deve estar no formato 000.000.000-00'), ('cpf_valido', 'CPF inválido')],
    'rg': [('obrigatorio', 'Preencha todos os campos')],
    'banco': [('obrigatorio', 'Preencha todos os campos')],
    'agencia': [('obrigatorio', 'Preencha todos os campos'), ('digitos', 'Número da agência deve conter apenas números')],
    'conta': [('obrigatorio', 'Preencha todos os campos')],
}

CAMPOS_DOCENTES = {k for k in REGRAS if k not in ('nivel', 'tipo')}


def so_digitos(s):
    return s.isdigit() if s else False


def formato_email(s):
    partes = s.split('@')
    if len(partes) != 2:
        return False
    dominio = partes[1]
    return '.' in dominio and not dominio.startswith('.') and not dominio.endswith('.')


def cpf_valido(s):
    numeros = [int(c) for c in s if c.isdigit()]
    if len(numeros) != 11:
        return False
    if len(set(numeros)) == 1:
        return False
    soma = sum(numeros[i] * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != numeros[9]:
        return False
    soma = sum(numeros[i] * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    return resto == numeros[10]


def checar_regra(regra, campo, valor):
    tipo = regra[0]
    mensagem = regra[1]
    if tipo == 'obrigatorio':
        if not valor.strip():
            return mensagem
    elif tipo == 'comprimento':
        minimo = regra[1]
        mensagem = regra[2]
        if valor.strip() and len(valor.strip()) < minimo:
            return mensagem
    elif tipo == 'texto':
        if valor.strip() and any(c.isdigit() for c in valor):
            return mensagem
    elif tipo == 'digitos':
        if not so_digitos(valor):
            return mensagem
    elif tipo == 'email':
        if not formato_email(valor):
            return mensagem
    elif tipo == 'valor':
        try:
            centavos = int(valor)
            if centavos <= 0:
                return mensagem
        except ValueError:
            return mensagem
    elif tipo == 'cep':
        if len(valor) != 9 or valor[5] != '-' or not (valor[:5] + valor[6:]).isdigit():
            return mensagem
    elif tipo == 'cpf_formato':
        if len(valor) != 14 or valor[3] != '.' or valor[7] != '.' or valor[11] != '-' or not (valor[:3] + valor[4:7] + valor[8:11] + valor[12:]).isdigit():
            return mensagem
    elif tipo == 'cpf_valido':
        if not cpf_valido(valor):
            return mensagem
    elif tipo == 'data_formato':
        if len(valor) != 10 or valor[2] != '/' or valor[5] != '/' or not (valor[:2] + valor[3:5] + valor[6:]).isdigit():
            return mensagem
    elif tipo == 'data_valida':
        dia, mes, ano = int(valor[:2]), int(valor[3:5]), int(valor[6:])
        if mes < 1 or mes > 12:
            return mensagem
        ultimo_dia = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
        if dia < 1 or dia > ultimo_dia:
            return mensagem
    return None


def validar(dados, aba):
    erros = []
    ja = set()
    campos = REGRAS.keys() if aba == 'alunos' else CAMPOS_DOCENTES
    for campo in campos:
        valor = str(dados.get(campo, '') or '')
        for regra in REGRAS[campo]:
            erro = checar_regra(regra, campo, valor)
            if erro and erro not in ja:
                erros.append(erro)
                ja.add(erro)
    return erros


def formatar_valor(centavos):
    inteiro = centavos // 100
    resto = centavos % 100
    texto = f'{inteiro:,}'.replace(',', '.')
    return f'R$ {texto},{resto:02d}'


def gerar_oficio(dados, aba):
    nome = dados.get('nome', '')
    nusp = dados.get('nusp', '')
    email = dados.get('email', '')
    programa = dados.get('programa', '')
    linha_assunto = f'Assunto: Solicitação de Auxílio Financeiro - {dados.get("tipo", "")}' if aba == 'alunos' else 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
    linha_programa = f'Programa: {programa} - {dados.get("nivel", "")}' if aba == 'alunos' else f'Programa: {programa}'
    valor = formatar_valor(int(dados.get('valor', 0)))

    linhas = [
        f'Interessada(o): {nome} - {nusp}',
        f'E-mail: {email}',
        linha_assunto,
        linha_programa,
        '',
        'A CCP-' + programa + ' aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {dados.get("evento", "")}',
        f'Período: {dados.get("periodo", "")}',
        f'Local: {dados.get("cidade_evento", "")} - {dados.get("estado_evento", "")} - {dados.get("pais_evento", "")}',
    ]
    link = dados.get('link', '')
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend([
        f'Apresentação de trabalho: {dados.get("apresentacao", "")}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {dados.get("detalhamento", "")}',
        '',
        'Endereço da(o) interessada(o)',
        f'{dados.get("logradouro", "")}, {dados.get("numero", "")}',
    ])
    complemento = dados.get('complemento', '')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend([
        f'CEP: {dados.get("cep", "")}',
        f'{dados.get("bairro", "")}, {dados.get("cidade", "")} - {dados.get("estado", "")}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {dados.get("nascimento", "")}',
        f'CPF: {dados.get("cpf", "")}',
        f'RG / RNM: {dados.get("rg", "")}',
        f'Banco: {dados.get("banco", "")}',
        f'Agência: {dados.get("agencia", "")}',
        f'Conta: {dados.get("conta", "")}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
async def solicitacao(payload: dict):
    aba = payload.get('aba', 'alunos')
    dados = payload.get('dados', {})
    erros = validar(dados, aba)
    if erros:
        return JSONResponse(status_code=422, content={'ok': False, 'erros': erros})
    return JSONResponse(status_code=200, content={'ok': True, 'oficio': gerar_oficio(dados, aba)})


@app.get('/')
async def raiz():
    return FileResponse(BASE_DIR / 'index.html')


app.mount('/', StaticFiles(directory=str(BASE_DIR), html=True), name='static')
