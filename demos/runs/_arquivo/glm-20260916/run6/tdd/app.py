"""Backend do formulário de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
import unicodedata
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

raiz = Path(__file__).resolve().parent
app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')

PROGRAMA_PADRAO = 'Ciência da Computação'
OBRIGATORIOS = [
    'nome', 'usp', 'programa', 'email', 'evento', 'periodo', 'cidade_evento',
    'estado_evento', 'pais_evento', 'valor', 'detalhamento', 'apresentacao',
    'nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
]


@app.get('/')
def index():
    return FileResponse(raiz / 'index.html', media_type='text/html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(raiz / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(raiz / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=raiz / 'assets', check_dir=False), name='assets')


@app.post('/solicitacao')
async def solicitar(request: Request):
    try:
        bruto = await request.()
    except Exception:
        bruto = dict(await request.form())
    if not isinstance(bruto, dict):
        bruto = {}
    dados = coletar(bruto)
    perfil = valor_em(dados, 'perfil').lower()
    docentes = perfil == 'docentes' or (
        perfil not in ('alunos', 'docentes')
        and not valor_em(dados, 'nivel')
        and not valor_em(dados, 'auxilio')
    )
    erros = validar(dados, docentes)
    if erros:
        return JSONResponse({'ok': False, 'erros': erros})
    return JSONResponse({'ok': True, 'oficio': oficio(dados, docentes)})


def normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_')


def campo_de(chave):
    n = normalizar(chave)
    if 'nascimento' in n:
        return 'nascimento'
    if 'cpf' in n:
        return 'cpf'
    if 'cep' in n:
        return 'cep'
    if 'rg' in n or 'rnm' in n:
        return 'rg'
    if 'usp' in n:
        return 'usp'
    if 'valor' in n:
        return 'valor'
    if 'mail' in n:
        return 'email'
    if 'nivel' in n:
        return 'nivel'
    if 'auxilio' in n:
        return 'auxilio'
    if 'banco' in n:
        return 'banco'
    if 'agencia' in n:
        return 'agencia'
    if 'conta' in n:
        return 'conta'
    if 'link' in n:
        return 'link'
    if 'apresenta' in n or 'trabalho' in n:
        return 'apresentacao'
    if 'periodo' in n:
        return 'periodo'
    if 'detalh' in n or 'pedido' in n:
        return 'detalhamento'
    if 'logradouro' in n or 'endereco' in n:
        return 'logradouro'
    if 'complemento' in n:
        return 'complemento'
    if 'bairro' in n:
        return 'bairro'
    if 'cidade' in n:
        return 'cidade_evento' if 'evento' in n else 'cidade'
    if 'estado' in n:
        return 'estado_evento' if 'evento' in n else 'estado'
    if 'pais' in n:
        return 'pais_evento'
    if 'evento' in n:
        return 'evento'
    if 'numero' in n:
        return 'numero'
    if 'nome' in n:
        return 'nome'
    if 'programa' in n:
        return 'programa'
    if 'aba' in n or 'perfil' in n or 'papel' in n or 'form' in n or 'solicitante' in n or 'categoria' in n or 'origem' in n:
        return 'perfil'
    return None


def coletar(bruto):
    dados = {}
    for chave, valor in bruto.items():
        campo = campo_de(chave)
        if campo:
            dados[campo] = '' if valor is None else str(valor)
    return dados


def valor_em(dados, campo):
    return (dados.get(campo) or '').strip()


def valor_numerico(texto):
    t = texto.strip()
    if re.fullmatch(r'\d+', t):
        return int(t) / 100
    t = t.replace('R$', '').strip()
    if ',' in t:
        t = t.replace('.', '').replace(',', '.')
    try:
        return float(t)
    except ValueError:
        return None


def moeda(numero):
    return 'R$ ' + f'{numero:,.2f}'.replace(',', '@').replace('.', ',').replace('@', '.')


def cpf_valido(cpf):
    digitos = re.sub(r'\D', '', cpf)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(digitos[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != int(digitos[n]):
            return False
    return True


def validar(dados, docentes):
    erros = []
    obrigatorios = OBRIGATORIOS if docentes else OBRIGATORIOS + ['nivel', 'auxilio']
    if any(not valor_em(dados, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    usp = valor_em(dados, 'usp')
    if usp and not usp.isdigit():
        erros.append('N. USP deve conter apenas números')
    agencia = valor_em(dados, 'agencia')
    if agencia and not agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')
    valor = valor_em(dados, 'valor')
    if valor:
        numero = valor_numerico(valor)
        if numero is None or numero <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    email = valor_em(dados, 'email')
    if email and ('@' not in email or not email.split('@', 1)[1].strip()):
        erros.append('E-mail inválido')
    cpf = valor_em(dados, 'cpf')
    if cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')
    cep = valor_em(dados, 'cep')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')
    nascimento = valor_em(dados, 'nascimento')
    if nascimento:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    return erros


def oficio(dados, docentes):
    programa = valor_em(dados, 'programa')
    if not programa or programa == 'texto':
        programa = PROGRAMA_PADRAO
    linhas = [
        f"Interessada(o): {valor_em(dados, 'nome')} - {valor_em(dados, 'usp')}",
        f"E-mail: {valor_em(dados, 'email')}",
    ]
    if docentes:
        linhas.append('Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {programa}')
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {valor_em(dados, 'auxilio')}")
        linhas.append(f'Programa: {programa} - {valor_em(dados, "nivel")}')
    linhas += [
        '',
        f'A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {valor_em(dados, 'evento')}",
        f"Período: {valor_em(dados, 'periodo')}",
        f"Local: {valor_em(dados, 'cidade_evento')} - {valor_em(dados, 'estado_evento')} - {valor_em(dados, 'pais_evento')}",
    ]
    link = valor_em(dados, 'link')
    if link:
        linhas.append(f'Link do evento: {link}')
    linhas += [
        f"Apresentação de trabalho: {valor_em(dados, 'apresentacao')}",
        f'Valor solicitado: {moeda(valor_numerico(valor_em(dados, "valor")))}',
        f"Detalhamento: {valor_em(dados, 'detalhamento')}",
        '',
        'Endereço da(o) interessada(o)',
        f"{valor_em(dados, 'logradouro')}, {valor_em(dados, 'numero')}",
    ]
    complemento = valor_em(dados, 'complemento')
    if complemento:
        linhas.append(f'Complemento: {complemento}')
    linhas += [
        f"CEP: {valor_em(dados, 'cep')}",
        f"{valor_em(dados, 'bairro')}, {valor_em(dados, 'cidade')} - {valor_em(dados, 'estado')}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {valor_em(dados, 'nascimento')}",
        f"CPF: {valor_em(dados, 'cpf')}",
        f"RG / RNM: {valor_em(dados, 'rg')}",
        f"Banco: {valor_em(dados, 'banco')}",
        f"Agência: {valor_em(dados, 'agencia')}",
        f"Conta: {valor_em(dados, 'conta')}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)
