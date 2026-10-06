import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

CAMPOS_DOCENTES = (
    'nome_completo', 'n_usp', 'programa', 'email', 'nome_evento',
    'periodo_evento', 'cidade_evento', 'estado_evento', 'pais_evento',
    'link_evento', 'valor_solicitado', 'detalhamento', 'apresentacao_trabalho',
    'data_nascimento', 'logradouro', 'numero', 'complemento', 'bairro', 'cep',
    'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_banco', 'agencia', 'conta',
)
CAMPOS_ALUNOS = CAMPOS_DOCENTES[:3] + ('nivel', 'tipo_auxilio') + CAMPOS_DOCENTES[3:]

app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


@app.post('/solicitacao')
def receber_solicitacao(dados: dict):
    erros = validar(dados)
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(dados)}


@app.get('/')
def pagina_inicial():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css')
def folha_de_estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script_da_pagina():
    return FileResponse(RAIZ / 'app.js', media_type='text/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')


def texto(dados, chave):
    valor = dados.get(chave)
    return '' if valor is None else str(valor).strip()


def validar(dados):
    erros = []
    obrigatorios = CAMPOS_DOCENTES if dados.get('aba') == 'DOCENTES' else CAMPOS_ALUNOS
    if any(not texto(dados, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')

    if texto(dados, 'n_usp') and not texto(dados, 'n_usp').isdigit():
        erros.append('N. USP deve conter apenas números')

    if texto(dados, 'agencia') and not texto(dados, 'agencia').isdigit():
        erros.append('Número da agência deve conter apenas números')

    valor = texto(dados, 'valor_solicitado')
    if valor and (not valor.isdigit() or int(valor) == 0):
        erros.append('Valor solicitado deve ser maior que 0')

    email = texto(dados, 'email')
    if email and ('@' not in email or not email.split('@', 1)[1]):
        erros.append('E-mail inválido')

    cpf = texto(dados, 'cpf')
    if cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        elif not cpf_valido(cpf):
            erros.append('CPF inválido')

    cep = texto(dados, 'cep')
    if cep and not re.fullmatch(r'\d{5}-\d{3}', cep):
        erros.append('CEP deve estar no formato 00000-000')

    data = texto(dados, 'data_nascimento')
    if data:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', data):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(data, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')

    return erros


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r'\D', '', cpf)]
    if len(digitos) != 11:
        return False
    dv1 = (sum(d * p for d, p in zip(digitos[:9], range(10, 1, -1))) * 10) % 11 % 10
    dv2 = (sum(d * p for d, p in zip(digitos[:10], range(11, 1, -1))) * 10) % 11 % 10
    return digitos[9] == dv1 and digitos[10] == dv2


def formatar_moeda(digitos):
    centavos = int(digitos)
    reais, resto = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def gerar_oficio(dados):
    docentes = dados.get('aba') == 'DOCENTES'
    if docentes:
        assunto = 'Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f"Programa: {dados['programa']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        linha_programa = f"Programa: {dados['programa']} - {dados['nivel']}"

    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        f'Assunto: {assunto}',
        linha_programa,
        '',
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo_evento']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados.get('link_evento'):
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas.extend([
        f"Apresentação de trabalho: {dados['apresentacao_trabalho']}",
        f"Valor solicitado: {formatar_moeda(dados['valor_solicitado'])}",
        f"Detalhamento: {dados['detalhamento']}",
        '',
        'Endereço da(o) interessada(o)',
        f"{dados['logradouro']}, {dados['numero']}",
    ])
    if dados.get('complemento'):
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.extend([
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        '',
        'Dados para pagamento',
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg_rnm']}",
        f"Banco: {dados['nome_banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)
