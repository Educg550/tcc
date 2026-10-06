import 
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

DIGITOS = set('0123456789')
CPF_FORMATO = re.compile(r'^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$')
CEP_FORMATO = re.compile(r'^[0-9]{5}-[0-9]{3}$')
DATA_FORMATO = re.compile(r'^[0-9]{2}/[0-9]{2}/[0-9]{4}$')

CAMPOS = [
    'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email',
    'nome_evento', 'periodo_evento', 'cidade_evento', 'estado_evento',
    'pais_evento', 'link_evento', 'valor_solicitado', 'detalhamento',
    'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'complemento',
    'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg_rnm', 'banco', 'agencia',
    'conta',
]
OPCIONAIS = {'link_evento', 'complemento'}
PROPRIOS_DO_ALUNO = {'nivel', 'tipo_auxilio'}

app = FastAPI()


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(RAIZ / 'style.css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js')


async def corpo(request):
    try:
        dados = await request.()
        if isinstance(dados, dict):
            return dados
    except Exception:
        pass
    try:
        return dict(await request.form())
    except Exception:
        return {}


def aba_de(dados):
    for chave in (
        'aba', 'formulario', 'origem', 'categoria', 'tipo_formulario',
        'tipo_solicitacao', 'perfil', 'tipo_solicitante', 'papel',
    ):
        valor = str(dados.get(chave) or '').strip().lower()
        if valor.startswith('docente'):
            return 'docentes'
    return 'alunos'


def coletar(dados):
    return {campo: str(dados.get(campo) or '') for campo in CAMPOS}


def so_digitos(texto):
    return bool(texto) and all(caractere in DIGITOS for caractere in texto)


def centavos(texto):
    digitos = ''.join(c for c in texto if c in DIGITOS)
    return int(digitos) if digitos else 0


def moeda(texto):
    total = centavos(texto)
    reais, resto = divmod(total, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c in DIGITOS]
    if len(digitos) != 11:
        return False
    base = digitos[:9]
    dv1 = (sum(d * p for d, p in zip(base, range(10, 1, -1))) * 10) % 11 % 10
    dv2 = (sum(d * p for d, p in zip(base + [dv1], range(11, 1, -1))) * 10) % 11 % 10
    return digitos[9] == dv1 and digitos[10] == dv2


def data_valida(texto):
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def validar(d, aba):
    erros = []
    obrigatorios = [c for c in CAMPOS if c not in OPCIONAIS]
    if aba == 'docentes':
        obrigatorios = [c for c in obrigatorios if c not in PROPRIOS_DO_ALUNO]
    if any(not d[c].strip() for c in obrigatorios):
        erros.append('Preencha todos os campos')
    if d['n_usp'] and not so_digitos(d['n_usp']):
        erros.append('N. USP deve conter apenas números')
    if d['agencia'] and not so_digitos(d['agencia']):
        erros.append('Número da agência deve conter apenas números')
    if d['valor_solicitado'] and centavos(d['valor_solicitado']) <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    if d['email']:
        partes = d['email'].split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')
    if d['cpf']:
        if not CPF_FORMATO.match(d['cpf']):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(d['cpf']):
            erros.append('CPF inválido')
    if d['cep'] and not CEP_FORMATO.match(d['cep']):
        erros.append('CEP deve estar no formato 00000-000')
    if d['data_nascimento']:
        if not DATA_FORMATO.match(d['data_nascimento']):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        elif not data_valida(d['data_nascimento']):
            erros.append('Data de nascimento inválida')
    return erros


def oficio(d, aba):
    if aba == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {d["programa"]}'
    else:
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {d["tipo_auxilio"]}'
        linha_programa = f'Programa: {d["programa"]} - {d["nivel"]}'
    linhas = [
        f'Interessada(o): {d["nome_completo"]} - {d["n_usp"]}',
        f'E-mail: {d["email"]}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{d["programa"]} aprovou na data de hoje, a solicitação de '
        'auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {d["nome_evento"]}',
        f'Período: {d["periodo_evento"]}',
        f'Local: {d["cidade_evento"]} - {d["estado_evento"]} - {d["pais_evento"]}',
    ]
    if d['link_evento']:
        linhas.append(f'Link do evento: {d["link_evento"]}')
    linhas += [
        f'Apresentação de trabalho: {d["apresentacao"]}',
        f'Valor solicitado: {moeda(d["valor_solicitado"])}',
        f'Detalhamento: {d["detalhamento"]}',
        '',
        'Endereço da(o) interessada(o)',
        f'{d["logradouro"]}, {d["numero"]}',
    ]
    if d['complemento']:
        linhas.append(f'Complemento: {d["complemento"]}')
    linhas += [
        f'CEP: {d["cep"]}',
        f'{d["bairro"]}, {d["cidade"]} - {d["estado"]}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {d["data_nascimento"]}',
        f'CPF: {d["cpf"]}',
        f'RG / RNM: {d["rg_rnm"]}',
        f'Banco: {d["banco"]}',
        f'Agência: {d["agencia"]}',
        f'Conta: {d["conta"]}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/solicitacao')
async def solicitar(request: Request):
    dados = await corpo(request)
    aba = aba_de(dados)
    valores = coletar(dados)
    erros = validar(valores, aba)
    texto = None if erros else oficio(valores, aba)
    conteudo = .dumps({'erros': erros, 'oficio': texto}, ensure_ascii=False)
    return Response(conteudo, media_type='application/')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets', check_dir=False), name='assets')
