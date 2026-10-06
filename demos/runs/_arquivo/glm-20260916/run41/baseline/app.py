import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

CPF_FORMATO = re.compile(r'[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}')
CEP_FORMATO = re.compile(r'[0-9]{5}-[0-9]{3}')
DATA_FORMATO = re.compile(r'[0-9]{2}/[0-9]{2}/[0-9]{4}')

CAMPOS = [
    'nome', 'nusp', 'programa', 'nivel', 'tipo_auxilio', 'email', 'evento', 'periodo',
    'cidade_evento', 'estado_evento', 'pais_evento', 'link', 'valor', 'detalhamento',
    'apresentacao', 'nascimento', 'logradouro', 'numero', 'complemento', 'bairro',
    'cep', 'cidade', 'estado', 'cpf', 'rgrnm', 'banco', 'agencia', 'conta',
]
OPCIONAIS = {'link', 'complemento'}
CAMPOS_DE_ALUNO = {'nivel', 'tipo_auxilio'}


class Solicitacao(BaseModel):
    origem: str
    nome: str = ''
    nusp: str = ''
    programa: str = ''
    nivel: str = ''
    tipo_auxilio: str = ''
    email: str = ''
    evento: str = ''
    periodo: str = ''
    cidade_evento: str = ''
    estado_evento: str = ''
    pais_evento: str = ''
    link: str = ''
    valor: str = ''
    detalhamento: str = ''
    apresentacao: str = ''
    nascimento: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    cidade: str = ''
    estado: str = ''
    cpf: str = ''
    rgrnm: str = ''
    banco: str = ''
    agencia: str = ''
    conta: str = ''


app = FastAPI(title='Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP')


def valor_em_centavos(texto: str):
    limpo = texto.replace('R$', '').replace('.', '').replace(',', '').replace(' ', '').strip()
    if re.fullmatch(r'[0-9]+', limpo):
        return int(limpo)
    return None


def digito_verificador_cpf(base: str, peso_inicial: int) -> str:
    soma = sum(int(caractere) * (peso_inicial - posicao) for posicao, caractere in enumerate(base))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def cpf_valido(cpf: str) -> bool:
    return (
        digito_verificador_cpf(cpf[:9], 10) == cpf[9]
        and digito_verificador_cpf(cpf[:10], 11) == cpf[10]
    )


def data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, '%d/%m/%Y')
    except ValueError:
        return False
    return True


def email_valido(texto: str) -> bool:
    local, arroba, dominio = texto.partition('@')
    return bool(local) and bool(arroba) and bool(dominio)


def moeda(centavos: int) -> str:
    reais, resto = divmod(centavos, 100)
    return f'R$ {reais:,}'.replace(',', '.') + f',{resto:02d}'


def gerar_oficio(d: Solicitacao) -> str:
    if d.origem == 'docentes':
        assunto = 'Assunto: Solicitação de Auxílio Financeiro - Verba do programa'
        linha_programa = f'Programa: {d.programa}'
    else:
        assunto = f'Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}'
        linha_programa = f'Programa: {d.programa} - {d.nivel}'
    linhas = [
        f'Interessada(o): {d.nome} - {d.nusp}',
        f'E-mail: {d.email}',
        assunto,
        linha_programa,
        '',
        f'A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {d.evento}',
        f'Período: {d.periodo}',
        f'Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}',
    ]
    if d.link:
        linhas.append(f'Link do evento: {d.link}')
    linhas += [
        f'Apresentação de trabalho: {d.apresentacao}',
        f'Valor solicitado: {moeda(valor_em_centavos(d.valor))}',
        f'Detalhamento: {d.detalhamento}',
        '',
        'Endereço da(o) interessada(o)',
        f'{d.logradouro}, {d.numero}',
    ]
    if d.complemento:
        linhas.append(f'Complemento: {d.complemento}')
    linhas += [
        f'CEP: {d.cep}',
        f'{d.bairro}, {d.cidade} - {d.estado}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {d.nascimento}',
        f'CPF: {d.cpf}',
        f'RG / RNM: {d.rgrnm}',
        f'Banco: {d.banco}',
        f'Agência: {d.agencia}',
        f'Conta: {d.conta}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]
    return '\n'.join(linhas)


@app.post('/api/solicitacoes')
def registrar_solicitacao(s: Solicitacao):
    d = s.model_copy(update={campo: getattr(s, campo).strip() for campo in CAMPOS})
    obrigatorios = [
        campo for campo in CAMPOS
        if campo not in OPCIONAIS and (campo not in CAMPOS_DE_ALUNO or d.origem == 'alunos')
    ]

    erros = []
    if any(not getattr(d, campo) for campo in obrigatorios):
        erros.append('Preencha todos os campos')
    if d.nusp and not re.fullmatch(r'[0-9]+', d.nusp):
        erros.append('N. USP deve conter apenas números')
    if d.agencia and not re.fullmatch(r'[0-9]+', d.agencia):
        erros.append('Número da agência deve conter apenas números')
    centavos = valor_em_centavos(d.valor) if d.valor else None
    if d.valor and not centavos:
        erros.append('Valor solicitado deve ser maior que 0')
    if d.email and not email_valido(d.email):
        erros.append('E-mail inválido')
    cpf_no_formato = bool(d.cpf) and bool(CPF_FORMATO.fullmatch(d.cpf))
    if d.cpf and not cpf_no_formato:
        erros.append('CPF deve estar no formato 000.000.000-00')
    if d.cep and not CEP_FORMATO.fullmatch(d.cep):
        erros.append('CEP deve estar no formato 00000-000')
    data_no_formato = bool(d.nascimento) and bool(DATA_FORMATO.fullmatch(d.nascimento))
    if d.nascimento and not data_no_formato:
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    if cpf_no_formato and not cpf_valido(d.cpf):
        erros.append('CPF inválido')
    if data_no_formato and not data_valida(d.nascimento):
        erros.append('Data de nascimento inválida')

    if erros:
        return {'erros': erros}
    return {'oficio': gerar_oficio(d)}


@app.get('/', include_in_schema=False)
def pagina():
    return FileResponse(RAIZ / 'index.html')


@app.get('/style.css', include_in_schema=False)
def estilo():
    return FileResponse(RAIZ / 'style.css')


@app.get('/app.js', include_in_schema=False)
def roteiro():
    return FileResponse(RAIZ / 'app.js')


app.mount('/assets', StaticFiles(directory=RAIZ / 'assets'), name='assets')
