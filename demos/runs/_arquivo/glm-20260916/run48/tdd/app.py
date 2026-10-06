import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

OBRIGATORIOS_ALUNOS = (
    'nome_completo', 'n_usp', 'programa', 'nivel', 'tipo_de_auxilio',
    'email', 'nome_do_evento', 'periodo_do_evento', 'cidade_do_evento',
    'estado_do_evento', 'pais_do_evento', 'valor_solicitado',
    'detalhamento_do_pedido', 'ira_apresentar_trabalho',
    'data_de_nascimento', 'logradouro', 'numero', 'bairro', 'cep',
    'cidade', 'estado', 'cpf', 'rg_rnm', 'nome_do_banco',
    'numero_da_agencia', 'numero_da_conta',
)
OBRIGATORIOS_DOCENTES = tuple(
    campo for campo in OBRIGATORIOS_ALUNOS
    if campo not in ('nivel', 'tipo_de_auxilio')
)


class Solicitacao(BaseModel):
    aba: str = ''
    nome_completo: str = ''
    n_usp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_de_auxilio: str = ''
    email: str = ''
    nome_do_evento: str = ''
    periodo_do_evento: str = ''
    cidade_do_evento: str = ''
    estado_do_evento: str = ''
    pais_do_evento: str = ''
    link_do_evento: str = ''
    valor_solicitado: str = ''
    detalhamento_do_pedido: str = ''
    ira_apresentar_trabalho: str = ''
    data_de_nascimento: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    cidade: str = ''
    estado: str = ''
    cpf: str = ''
    rg_rnm: str = ''
    nome_do_banco: str = ''
    numero_da_agencia: str = ''
    numero_da_conta: str = ''


app = FastAPI()


def digito_verificador(digitos, tamanho, peso_inicial):
    soma = sum(
        digito * peso
        for digito, peso in zip(digitos[:tamanho], range(peso_inicial, 1, -1))
    )
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    return (
        digito_verificador(digitos, 9, 10) == digitos[9]
        and digito_verificador(digitos, 10, 11) == digitos[10]
    )


def data_valida(data):
    dia, mes, ano = (int(parte) for parte in data.split('/'))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def valor_em_centavos(valor):
    limpo = valor.strip().replace('R$', '').strip()
    if not re.fullmatch(r'\d+([.,]\d+)*', limpo):
        return None
    return int(re.sub(r'\D', '', limpo))


def moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def validar(dados):
    obrigatorios = (
        OBRIGATORIOS_DOCENTES if dados.aba == 'docentes' else OBRIGATORIOS_ALUNOS
    )
    valores = dados.model_dump()
    erros = []
    if any(not valores[campo].strip() for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if dados.n_usp.strip() and not dados.n_usp.strip().isdigit():
        erros.append('N. USP deve conter apenas números')
    if dados.numero_da_agencia.strip() and not dados.numero_da_agencia.strip().isdigit():
        erros.append('Número da agência deve conter apenas números')
    if dados.valor_solicitado.strip():
        centavos = valor_em_centavos(dados.valor_solicitado)
        if centavos is None or centavos <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    if dados.email.strip() and not re.fullmatch(r'[^@\s]+@[^@\s]+', dados.email.strip()):
        erros.append('E-mail inválido')
    cpf = dados.cpf.strip()
    if cpf:
        if re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf):
            if not cpf_valido(cpf):
                erros.append('CPF inválido')
        else:
            erros.append('CPF deve estar no formato 000.000.000-00')
    if dados.cep.strip() and not re.fullmatch(r'\d{5}-\d{3}', dados.cep.strip()):
        erros.append('CEP deve estar no formato 00000-000')
    nascimento = dados.data_de_nascimento.strip()
    if nascimento:
        if re.fullmatch(r'\d{2}/\d{2}/\d{4}', nascimento):
            if not data_valida(nascimento):
                erros.append('Data de nascimento inválida')
        else:
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    return erros


def gerar_oficio(dados):
    if dados.aba == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        programa = f'Programa: {dados.programa}'
    else:
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {dados.tipo_de_auxilio}'
        programa = f'Programa: {dados.programa} - {dados.nivel}'
    linhas = [
        f'Interessada(o): {dados.nome_completo} - {dados.n_usp}',
        f'E-mail: {dados.email}',
        assunto,
        programa,
        '',
        f'A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {dados.nome_do_evento}',
        f'Período: {dados.periodo_do_evento}',
        f'Local: {dados.cidade_do_evento} - {dados.estado_do_evento} - {dados.pais_do_evento}',
    ]
    if dados.link_do_evento.strip():
        linhas.append(f'Link do evento: {dados.link_do_evento}')
    linhas.extend([
        f'Apresentação de trabalho: {dados.ira_apresentar_trabalho}',
        f'Valor solicitado: {moeda(valor_em_centavos(dados.valor_solicitado))}',
        f'Detalhamento: {dados.detalhamento_do_pedido}',
        '',
        'Endereço da(o) interessada(o)',
        f'{dados.logradouro}, {dados.numero}',
    ])
    if dados.complemento.strip():
        linhas.append(f'Complemento: {dados.complemento}')
    linhas.extend([
        f'CEP: {dados.cep}',
        f'{dados.bairro}, {dados.cidade} - {dados.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {dados.data_de_nascimento}',
        f'CPF: {dados.cpf}',
        f'RG / RNM: {dados.rg_rnm}',
        f'Banco: {dados.nome_do_banco}',
        f'Agência: {dados.numero_da_agencia}',
        f'Conta: {dados.numero_da_conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ])
    return '\n'.join(linhas)


@app.post('/api/solicitacao')
def registrar_solicitacao(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(dados)}


@app.get('/')
def pagina():
    return FileResponse(RAIZ / 'index.html', media_type='text/html')


@app.get('/style.css')
def estilo():
    return FileResponse(RAIZ / 'style.css', media_type='text/css')


@app.get('/app.js')
def script():
    return FileResponse(RAIZ / 'app.js', media_type='application/javascript')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
