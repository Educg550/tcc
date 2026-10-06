import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


@app.get('/')
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


if (RAIZ / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')


CAMPOS = [
    'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
    'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento',
    'pais_evento', 'link_evento', 'valor_solicitado', 'detalhamento',
    'apresentacao_trabalho', 'data_nascimento', 'logradouro', 'numero',
    'complemento', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm',
    'nome_banco', 'numero_agencia', 'numero_conta',
]

EXCLUSIVOS_DE_ALUNOS = ('nivel', 'tipo_auxilio')


def _campo(dados, chave):
    valor = dados.get(chave, '')
    if valor is None:
        return ''
    return str(valor).strip()


def _cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    if len(digitos) != 11:
        return False
    resto = sum(digito * peso for digito, peso in zip(digitos[:9], range(10, 1, -1))) % 11
    if (0 if resto < 2 else 11 - resto) != digitos[9]:
        return False
    resto = sum(digito * peso for digito, peso in zip(digitos[:10], range(11, 1, -1))) % 11
    return (0 if resto < 2 else 11 - resto) == digitos[10]


def _erros_de_formato(valores):
    erros = []
    if valores['n_usp'] and not valores['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')
    if valores['numero_agencia'] and not valores['numero_agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')
    if valores['valor_solicitado']:
        texto = (
            valores['valor_solicitado']
            .replace('R$', '')
            .replace(' ', '')
            .replace('.', '')
            .replace(',', '.')
        )
        try:
            valor = float(texto)
        except ValueError:
            erros.append('Valor solicitado deve ser maior que 0')
        else:
            if valor <= 0:
                erros.append('Valor solicitado deve ser maior que 0')
    if valores['email']:
        partes = valores['email'].split('@')
        if len(partes) != 2 or not partes[1]:
            erros.append('E-mail inválido')
    if valores['cpf']:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', valores['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not _cpf_valido(valores['cpf']):
            erros.append('CPF inválido')
    if valores['cep'] and not re.fullmatch(r'\d{5}-\d{3}', valores['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if valores['data_nascimento']:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', valores['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(valores['data_nascimento'], '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def _oficio(valores, docentes):
    nome = valores['nome_completo']
    n_usp = valores['n_usp']
    email = valores['email']
    programa = valores['programa']
    tipo_auxilio = valores['tipo_auxilio']
    nivel = valores['nivel']
    evento = valores['nome_evento']
    periodo = valores['periodo_evento']
    cidade_evento = valores['cidade_evento']
    estado_evento = valores['estado_evento']
    pais_evento = valores['pais_evento']
    link = valores['link_evento']
    apresentacao = valores['apresentacao_trabalho']
    valor = valores['valor_solicitado']
    detalhamento = valores['detalhamento']
    logradouro = valores['logradouro']
    numero = valores['numero']
    complemento = valores['complemento']
    bairro = valores['bairro']
    cidade = valores['cidade']
    estado = valores['estado']
    nascimento = valores['data_nascimento']
    cpf = valores['cpf']
    rg_rnm = valores['rg_rnm']
    banco = valores['nome_banco']
    agencia = valores['numero_agencia']
    conta = valores['numero_conta']
    if docentes:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {programa}'
    else:
        assunto = f'Solicitação de Auxílio Financeiro - {tipo_auxilio}'
        linha_programa = f'Programa: {programa} - {nivel}'
    linhas = [
        f'Interessada(o): {nome} - {n_usp}',
        f'E-mail: {email}',
        f'Assunto: {assunto}',
        linha_programa,
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {evento}',
        f'Período: {periodo}',
        f'Local: {cidade_evento} - {estado_evento} - {pais_evento}',
    ]
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas.extend([
        f'Apresentação de trabalho: {apresentacao}',
        f'Valor solicitado: {valor}',
        f'Detalhamento: {detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{logradouro}, {numero}',
    ])
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas.extend([
        f'CEP: {valores['cep']}' if False else f'CEP: {valores["cep"]}',
    ])
    return linhas


@app.post('/api/solicitacao')
async def receber_solicitacao(request: Request):
    try:
        dados = await request.()
    except Exception:
        dados = dict(await request.form())
    if not isinstance(dados, dict):
        dados = {}
    aba = str(dados.get('aba') or dados.get('perfil') or 'alunos').upper()
    docentes = aba == 'DOCENTES'
    valores = {chave: _campo(dados, chave) for chave in CAMPOS}
    obrigatorios = [
        chave for chave in CAMPOS
        if not (docentes and chave in EXCLUSIVOS_DE_ALUNOS)
    ]
    erros = []
    if any(not valores[chave] for chave in obrigatorios):
        erros.append('Preencha todos os campos')
    erros.extend(_erros_de_formato(valores))
    if erros:
        return {'erros': erros}
    return {'oficio': _oficio(valores, docentes)}
