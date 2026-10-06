import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title='Auxílio Financeiro - Pós-Graduação IME-USP')

CAMPOS = (
    'nome', 'n_usp', 'programa', 'nivel', 'tipo_auxilio', 'email', 'evento',
    'periodo', 'cidade_evento', 'estado_evento', 'pais_evento', 'link_evento',
    'valor_solicitado', 'detalhamento', 'apresentacao', 'data_nascimento',
    'logradouro', 'numero', 'complemento', 'bairro', 'cep', 'cidade', 'estado',
    'cpf', 'rg', 'banco', 'agencia', 'conta',
)
OPCIONAIS = {'nivel', 'tipo_auxilio', 'link_evento', 'complemento'}


def _digito_verificador(parte, peso):
    resto = sum(int(algarismo) * (peso - posicao) for posicao, algarismo in enumerate(parte)) % 11
    return '0' if resto < 2 else str(11 - resto)


def _cpf_valido(cpf):
    return cpf[9:] == _digito_verificador(cpf[:9], 10) + _digito_verificador(cpf[:10], 11)


def _erros(d, marcador):
    erros = []
    obrigatorios = [campo for campo in CAMPOS if campo not in OPCIONAIS]
    if marcador == 'alunos':
        obrigatorios += ['nivel', 'tipo_auxilio']
    if any(not d[campo] for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if d['n_usp'] and not d['n_usp'].isdigit():
        erros.append('N. USP deve conter apenas números')

    if d['agencia'] and not d['agencia'].isdigit():
        erros.append('Número da agência deve conter apenas números')

    if d['valor_solicitado']:
        centavos = re.sub(r'\D', '', d['valor_solicitado'])
        if not centavos or int(centavos) <= 0:
            erros.append('Valor solicitado deve ser maior que 0')

    if d['email']:
        partes = d['email'].split('@')
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append('E-mail inválido')

    cpf = re.sub(r'\D', '', d['cpf'])
    if d['cpf'] and len(cpf) != 11:
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif len(cpf) == 11 and not _cpf_valido(cpf):
        erros.append('CPF inválido')

    cep = re.sub(r'\D', '', d['cep'])
    if d['cep'] and len(cep) != 8:
        erros.append('CEP deve estar no formato 00000-000')

    nascimento = re.sub(r'\D', '', d['data_nascimento'])
    if d['data_nascimento']:
        if len(nascimento) != 8:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(nascimento, '%d%m%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return 'R$ ' + f'{reais:,}'.replace(',', '.') + f',{resto:02d}'


def _oficio(d, docente):
    if docente:
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f"Programa: {d['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}"
        programa = f"Programa: {d['programa']} - {d['nivel']}"
    linhas = [
        f"Interessada(o): {d['nome']} - {d['n_usp']}",
        f"E-mail: {d['email']}",
        assunto,
        programa,
        '',
        f"A CCP-{d['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {d['evento']}",
        f"Período: {d['periodo']}",
        f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}",
    ]
    if d['link_evento']:
        linhas.append(f"Link do evento: {d['link_evento']}")
    centavos = int(re.sub(r'\D', '', d['valor_solicitado']))
    linhas += [
        f"Apresentação de trabalho: {d['apresentacao']}",
        f"Valor solicitado: {_moeda(centavos)}",
        f"Detalhamento: {d['detalhamento']}",
        '',
        'Endereço da(o) interessada(o)',
        f"{d['logradouro']}, {d['numero']}",
    ]
    if d['complemento']:
        linhas.append(f"Complemento: {d['complemento']}")
    cep = re.sub(r'\D', '', d['cep'])
    cpf = re.sub(r'\D', '', d['cpf'])
    nascimento = re.sub(r'\D', '', d['data_nascimento'])
    linhas += [
        f"CEP: {cep[:5]}-{cep[5:]}",
        f"{d['bairro']}, {d['cidade']} - {d['estado']}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {nascimento[:2]}/{nascimento[2:4]}/{nascimento[4:]}",
        f"CPF: {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}",
        f"RG / RNM: {d['rg']}",
        f"Banco: {d['banco']}",
        f"Agência: {d['agencia']}",
        f"Conta: {d['conta']}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


async def _corpo(request: Request):
    try:
        dados = await request.()
    except Exception:
        dados = None
    if isinstance(dados, dict):
        return dados
    formulario = await request.form()
    return {chave: formulario[chave] for chave in formulario}


@app.post('/api/solicitacao')
async def solicitar(request: Request):
    bruto = await _corpo(request)
    marcador = str(bruto.get('formulario', '') or '').strip().lower()
    d = {campo: str(bruto.get(campo, '') or '').strip() for campo in CAMPOS}
    erros = _erros(d, marcador)
    if erros:
        return JSONResponse({'erros': erros})
    docente = marcador == 'docentes' if marcador else not (d['nivel'] or d['tipo_auxilio'])
    return JSONResponse({'oficio': _oficio(d, docente)})


@app.get('/')
def pagina():
    return FileResponse(BASE / 'index.html')


@app.get('/style.css')
def estilo():
    return FileResponse(BASE / 'style.css')


@app.get('/app.js')
def script():
    return FileResponse(BASE / 'app.js')


app.mount('/assets', StaticFiles(directory=BASE / 'assets', check_dir=False), name='assets')
