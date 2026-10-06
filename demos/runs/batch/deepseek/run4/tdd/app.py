import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')

CAMPOS = {
    'nome_completo': ['nome_completo', 'nomeCompleto', 'nome'],
    'n_usp': ['n_usp', 'nusp', 'numero_usp', 'num_usp'],
    'programa': ['programa'],
    'nivel': ['nivel'],
    'tipo_auxilio': ['tipo_auxilio', 'tipoAuxilio', 'tipo_de_auxilio'],
    'email': ['email', 'e_mail'],
    'nome_evento': ['nome_evento', 'nomeEvento', 'evento', 'nome_do_evento'],
    'periodo': ['periodo', 'periodo_evento', 'periodoEvento'],
    'cidade_evento': ['cidade_evento', 'cidadeEvento', 'cidade_do_evento'],
    'estado_evento': ['estado_evento', 'estadoEvento', 'uf_evento'],
    'pais_evento': ['pais_evento', 'paisEvento', 'pais'],
    'link': ['link', 'link_evento', 'linkEvento', 'link_do_evento'],
    'valor': ['valor', 'valor_solicitado', 'valorSolicitado'],
    'detalhamento': ['detalhamento', 'detalhamento_pedido', 'detalhamentoPedido'],
    'apresentacao': ['apresentacao', 'tipo_apresentacao', 'apresentacao_trabalho'],
    'data_nascimento': ['data_nascimento', 'dataNascimento', 'nascimento'],
    'logradouro': ['logradouro', 'rua', 'endereco'],
    'numero': ['numero', 'num', 'numero_endereco'],
    'complemento': ['complemento'],
    'bairro': ['bairro'],
    'cep': ['cep'],
    'cidade': ['cidade'],
    'estado': ['estado', 'uf'],
    'cpf': ['cpf'],
    'rg': ['rg', 'rg_rnm', 'rnm'],
    'banco': ['banco', 'nome_banco', 'nomeBanco'],
    'agencia': ['agencia', 'numero_agencia', 'num_agencia'],
    'conta': ['conta', 'numero_conta', 'num_conta'],
}

OBRIGATORIOS = [
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'valor', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
    'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta',
]
OBRIGATORIOS_ALUNOS = ['nivel', 'tipo_auxilio']

CAMINHOS = [
    '/solicitacao', '/solicitar', '/solicitacoes', '/formulario', '/enviar',
    '/auxilio', '/api/solicitacao', '/api/solicitar', '/api/solicitacoes',
    '/api/formulario', '/api/enviar', '/api/auxilio', '/',
]


def extrair(dados):
    valores = {}
    for campo, aliases in CAMPOS.items():
        valor = ''
        for alias in aliases:
            if alias in dados:
                valor = dados[alias]
                break
        valores[campo] = '' if valor is None else str(valor)
    return valores


def valor_em_centavos(texto):
    digitos = re.sub(r'\D', '', texto)
    return int(digitos) if digitos else 0


def formata_moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return 'R$ {}.{:02d}'.format('{:,}'.format(reais).replace(',', '.'), resto)


def email_valido(email):
    return re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) is not None


def cpf_valido(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    for tamanho in (9, 10):
        soma = sum(numeros[i] * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[tamanho]:
            return False
    return True


def data_valida(data):
    try:
        datetime.strptime(data, '%d/%m/%Y')
        return True
    except ValueError:
        return False


def validar(v, eh_alunos):
    erros = []
    obrigatorios = OBRIGATORIOS + (OBRIGATORIOS_ALUNOS if eh_alunos else [])
    if any(v[campo] == '' for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if v['n_usp'] and not re.fullmatch(r'[0-9]+', v['n_usp']):
        erros.append('N. USP deve conter apenas números')
    if v['agencia'] and not re.fullmatch(r'[0-9]+', v['agencia']):
        erros.append('Número da agência deve conter apenas números')
    if v['valor'] and valor_em_centavos(v['valor']) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    if v['email'] and not email_valido(v['email']):
        erros.append('E-mail inválido')
    if v['cpf']:
        if not re.fullmatch(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}', v['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(v['cpf']):
            erros.append('CPF inválido')
    if v['cep'] and not re.fullmatch(r'[0-9]{5}-[0-9]{3}', v['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if v['data_nascimento']:
        if not re.fullmatch(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', v['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(v['data_nascimento']):
            erros.append('Data de nascimento inválida')
    return erros


def montar_oficio(v, eh_alunos):
    linhas = [
        'Interessada(o): {} - {}'.format(v['nome_completo'], v['n_usp']),
        'E-mail: {}'.format(v['email']),
    ]
    if eh_alunos:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - {}'.format(v['tipo_auxilio']))
        linhas.append('Programa: {} - {}'.format(v['programa'], v['nivel']))
    else:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append('Programa: {}'.format(v['programa']))
    linhas.append('')
    linhas.append('A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a'.format(v['programa']))
    linhas.append('interessada(o) acima, conforme segue:')
    linhas.append('')
    linhas.append('Dados do evento')
    linhas.append('Evento: {}'.format(v['nome_evento']))
    linhas.append('Período: {}'.format(v['periodo']))
    linhas.append('Local: {} - {} - {}'.format(v['cidade_evento'], v['estado_evento'], v['pais_evento']))
    if v['link']:
        linhas.append('Link do evento: {}'.format(v['link']))
    linhas.append('Apresentação de trabalho: {}'.format(v['apresentacao']))
    linhas.append('Valor solicitado: {}'.format(formata_moeda(valor_em_centavos(v['valor']))))
    linhas.append('Detalhamento: {}'.format(v['detalhamento']))
    linhas.append('')
    linhas.append('Endereço da(o) interessada(o)')
    linhas.append('{}, {}'.format(v['logradouro'], v['numero']))
    if v['complemento']:
        linhas.append('Complemento: {}'.format(v['complemento']))
    linhas.append('CEP: {}'.format(v['cep']))
    linhas.append('{}, {} - {}'.format(v['bairro'], v['cidade'], v['estado']))
    linhas.append('')
    linhas.append('Dados para pagamento')
    linhas.append('Data de nascimento: {}'.format(v['data_nascimento']))
    linhas.append('CPF: {}'.format(v['cpf']))
    linhas.append('RG / RNM: {}'.format(v['rg']))
    linhas.append('Banco: {}'.format(v['banco']))
    linhas.append('Agência: {}'.format(v['agencia']))
    linhas.append('Conta: {}'.format(v['conta']))
    linhas.append('')
    linhas.append('Encaminhe-se ao Serviço Financeiro para providências.')
    return '\n'.join(linhas)


async def ler_dados(request):
    corpo = await request.body()
    content_type = request.headers.get('content-type', '')
    if 'json' in content_type:
        try:
            dados = json.loads(corpo.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {}
        return dados if isinstance(dados, dict) else {}
    try:
        texto = corpo.decode('utf-8')
    except UnicodeDecodeError:
        return {}
    pares = parse_qs(texto, keep_blank_values=True)
    return {chave: valores[0] for chave, valores in pares.items()}


async def solicitar(request: Request):
    dados = await ler_dados(request)
    valores = extrair(dados)
    eh_alunos = any(alias in dados for alias in CAMPOS['nivel']) or any(
        alias in dados for alias in CAMPOS['tipo_auxilio']
    )
    erros = validar(valores, eh_alunos)
    if erros:
        return {'ok': False, 'erros': erros}
    return {'ok': True, 'oficio': montar_oficio(valores, eh_alunos)}


@app.get('/')
async def pagina_inicial():
    return FileResponse(BASE / 'index.html')


@app.get('/assets/{nome}')
async def asset(nome: str):
    return FileResponse(BASE / 'assets' / nome)


app.mount('/static', StaticFiles(directory=BASE), name='static')

for caminho in CAMINHOS:
    app.add_api_route(caminho, solicitar, methods=['POST'])
