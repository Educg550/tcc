import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()

class DadosSolicitacao(BaseModel):
    nome: str
    nusp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ''
    valor: int
    detalhamento: str
    apresentacao: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: str = ''
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def _validar_cpf(cpf: str) -> bool:
    nums = re.sub(r'[^0-9]', '', cpf)
    if len(nums) != 11:
        return False
    if nums == nums[0] * 11:
        return False
    soma = sum(int(nums[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    dig1 = 0 if resto < 2 else 11 - resto
    if int(nums[9]) != dig1:
        return False
    soma = sum(int(nums[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    dig2 = 0 if resto < 2 else 11 - resto
    if int(nums[10]) != dig2:
        return False
    return True


def _validar_data(data: str) -> bool:
    if not re.match(r'\d{2}/\d{2}/\d{4}', data):
        return False
    dia, mes, ano = map(int, data.split('/'))
    if mes < 1 or mes > 12:
        return False
    dias_mes = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if dia < 1 or dia > dias_mes[mes - 1]:
        return False
    return True


def _erros(dados: DadosSolicitacao, docente: bool) -> list:
    erros = []
    campos_obrigatorios = ['nome', 'nusp', 'programa', 'email', 'evento', 'periodo',
                           'cidade_evento', 'estado_evento', 'pais_evento', 'detalhamento',
                           'apresentacao', 'data_nascimento', 'logradouro', 'numero',
                           'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg', 'banco',
                           'agencia', 'conta']
    if not docente:
        campos_obrigatorios.extend(['nivel', 'tipo_auxilio'])
    vazio = False
    for campo in campos_obrigatorios:
        val = getattr(dados, campo)
        if not val or (isinstance(val, str) and val.strip() == ''):
            vazio = True
            break
    if vazio:
        erros.append('Preencha todos os campos')
        return erros

    if not dados.nusp.isdigit():
        erros.append('N. USP deve conter apenas números')

    if not dados.agencia.isdigit():
        erros.append('Número da agência deve conter apenas números')

    if dados.valor <= 0:
        erros.append('Valor solicitado deve ser maior que 0')

    if '@' not in dados.email or not dados.email.split('@')[1].strip():
        erros.append('E-mail inválido')

    if not re.match(r'\d{3}\.\d{3}\.\d{3}-\d{2}', dados.cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif not _validar_cpf(dados.cpf):
        erros.append('CPF inválido')

    if not re.match(r'\d{5}-\d{3}', dados.cep):
        erros.append('CEP deve estar no formato 00000-000')

    if not _validar_data(dados.data_nascimento):
        if not re.match(r'\d{2}/\d{2}/\d{4}', dados.data_nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            erros.append('Data de nascimento inválida')

    return erros


def _oficio(dados: DadosSolicitacao, docente: bool) -> str:
    valor_formatado = f"R$ {dados.valor / 100:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')

    linhas = []
    linhas.append(f"Interessada(o): {dados.nome} - {dados.nusp}")
    linhas.append(f"E-mail: {dados.email}")

    if docente:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados.programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}")
        linhas.append(f"Programa: {dados.programa} - {dados.nivel}")

    linhas.append('')
    linhas.append(f"A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append(f"interessada(o) acima, conforme segue:")
    linhas.append('')
    linhas.append('Dados do evento')
    linhas.append(f"Evento: {dados.evento}")
    linhas.append(f"Período: {dados.periodo}")
    linhas.append(f"Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}")
    if dados.link_evento.strip():
        linhas.append(f"Link do evento: {dados.link_evento}")
    linhas.append(f"Apresentação de trabalho: {dados.apresentacao}")
    linhas.append(f"Valor solicitado: {valor_formatado}")
    linhas.append(f"Detalhamento: {dados.detalhamento}")
    linhas.append('')
    linhas.append('Endereço da(o) interessada(o)')
    linhas.append(f"{dados.logradouro}, {dados.numero}")
    if dados.complemento.strip():
        linhas.append(f"Complemento: {dados.complemento}")
    linhas.append(f"CEP: {dados.cep}")
    linhas.append(f"{dados.bairro}, {dados.cidade} - {dados.estado}")
    linhas.append('')
    linhas.append('Dados para pagamento')
    linhas.append(f"Data de nascimento: {dados.data_nascimento}")
    linhas.append(f"CPF: {dados.cpf}")
    linhas.append(f"RG / RNM: {dados.rg}")
    linhas.append(f"Banco: {dados.banco}")
    linhas.append(f"Agência: {dados.agencia}")
    linhas.append(f"Conta: {dados.conta}")
    linhas.append('')
    linhas.append('Encaminhe-se ao Serviço Financeiro para providências.')

    return '\n'.join(linhas)


@app.get('/')
async def home():
    caminho = os.path.join(os.path.dirname(__file__), 'index.html')
    with open(caminho, 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())


@app.post('/solicitacoes/alunos')
async def solicitar_alunos(dados: DadosSolicitacao):
    erros = _erros(dados, docente=False)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    oficio = _oficio(dados, docente=False)
    return {'titulo': 'Solicitação registrada', 'oficio': oficio}


@app.post('/solicitacoes/docentes')
async def solicitar_docentes(dados: DadosSolicitacao):
    erros = _erros(dados, docente=True)
    if erros:
        return JSONResponse(status_code=400, content={'erros': erros})
    oficio = _oficio(dados, docente=True)
    return {'titulo': 'Solicitação registrada', 'oficio': oficio}


app.mount('/assets', StaticFiles(directory=os.path.join(os.path.dirname(__file__), 'assets')), name='assets')
app.mount('/', StaticFiles(directory=os.path.dirname(__file__), html=True), name='statics')
