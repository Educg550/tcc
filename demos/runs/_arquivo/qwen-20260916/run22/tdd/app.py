import re
from datetime import datetime
from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

class Solicitacao(BaseModel):
    nome_completo: str = Field(..., alias='nome_completo')
    numero_usp: str = Field(..., alias='numero_usp')
    programa: str = Field(..., alias='programa')
    nivel: Optional[str] = Field(None, alias='nivel')
    tipo_auxilio: Optional[str] = Field(None, alias='tipo_auxilio')
    email: str = Field(..., alias='email')
    nome_evento: str = Field(..., alias='nome_evento')
    periodo: str = Field(..., alias='periodo')
    cidade_evento: str = Field(..., alias='cidade_evento')
    estado_evento: str = Field(..., alias='estado_evento')
    pais_evento: str = Field(..., alias='pais_evento')
    link_evento: Optional[str] = Field('', alias='link_evento')
    valor: str = Field(..., alias='valor')
    detalhamento: str = Field(..., alias='detalhamento')
    apresentacao: str = Field(..., alias='apresentacao')
    data_nascimento: str = Field(..., alias='data_nascimento')
    logradouro: str = Field(..., alias='logradouro')
    numero: str = Field(..., alias='numero')
    complemento: Optional[str] = Field('', alias='complemento')
    bairro: str = Field(..., alias='bairro')
    cep: str = Field(..., alias='cep')
    cidade: str = Field(..., alias='cidade')
    estado: str = Field(..., alias='estado')
    cpf: str = Field(..., alias='cpf')
    rg: str = Field(..., alias='rg')
    banco: str = Field(..., alias='banco')
    agencia: str = Field(..., alias='agencia')
    conta: str = Field(..., alias='conta')

    class Config:
        populate_by_name = True

def valida_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma * 10 % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma * 10 % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[10]):
        return False
    return True

def formata_valor(valor: str) -> str:
    try:
        centavos = int(valor)
    except ValueError:
        return '0,00'
    if centavos < 0:
        centavos = 0
    inteiro, frac = divmod(centavos, 100)
    inteiro_str = ''
    s = str(inteiro)
    for i, d in enumerate(s):
        if i > 0 and (len(s) - i) % 3 == 0:
            inteiro_str += '.'
        inteiro_str += d
    return f'{inteiro_str},{frac:02d}'

def gera_oficio(dados: Solicitacao, tipo: str) -> str:
    linhas = []
    linhas.append(f'Interessada(o): {dados.nome_completo} - {dados.numero_usp}')
    linhas.append(f'E-mail: {dados.email}')
    
    if tipo == 'alunos':
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}')
        linhas.append(f'Programa: {dados.programa} - {dados.nivel}')
    else:
        linhas.append(f'Assunto: Solicitação de Auxílio Financeiro - Verba do programa')
        linhas.append(f'Programa: {dados.programa}')

    linhas.append(f'A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a')
    linhas.append('interessada(o) acima, conforme segue:')
    linhas.append('')
    linhas.append('Dados do evento')
    linhas.append(f'Evento: {dados.nome_evento}')
    linhas.append(f'Período: {dados.periodo}')
    linhas.append(f'Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}')
    if dados.link_evento:
        linhas.append(f'Link do evento: {dados.link_evento}')
    linhas.append(f'Apresentação de trabalho: {dados.apresentacao}')
    linhas.append(f'Valor solicitado: R$ {formata_valor(dados.valor)}')
    linhas.append(f'Detalhamento: {dados.detalhamento}')
    linhas.append('')
    linhas.append('Endereço da(o) interessada(o)')
    linhas.append(f'{dados.logradouro}, {dados.numero}')
    if dados.complemento:
        linhas.append(f'Complemento: {dados.complemento}')
    linhas.append(f'CEP: {dados.cep}')
    linhas.append(f'{dados.bairro}, {dados.cidade} - {dados.estado}')
    linhas.append('')
    linhas.append('Dados para pagamento')
    linhas.append(f'Data de nascimento: {dados.data_nascimento}')
    linhas.append(f'CPF: {dados.cpf}')
    linhas.append(f'RG / RNM: {dados.rg}')
    linhas.append(f'Banco: {dados.banco}')
    linhas.append(f'Agência: {dados.agencia}')
    linhas.append(f'Conta: {dados.conta}')
    linhas.append('')
    linhas.append('Encaminhe-se ao Serviço Financeiro para providências.')
    return '\n'.join(linhas)

def valida_solicitacao(dados: Solicitacao, tipo: str) -> List[str]:
    erros = []
    
    obrigatorios = ['nome_completo', 'numero_usp', 'programa', 'email', 'nome_evento', 'periodo', 'cidade_evento', 'estado_evento', 'pais_evento', 'valor', 'detalhamento', 'apresentacao', 'data_nascimento', 'logradouro', 'numero', 'bairro', 'cep', 'cidade', 'estado', 'cpf', 'rg', 'banco', 'agencia', 'conta']
    if tipo == 'alunos':
        obrigatorios.extend(['nivel', 'tipo_auxilio'])
    
    for campo in obrigatorios:
        val = getattr(dados, campo)
        if not val or val.strip() == '':
            erros.append('Preencha todos os campos')
            break
    
    if not re.match(r'^\d+$', dados.numero_usp):
        erros.append('N. USP deve conter apenas números')
    
    if not re.match(r'^\d+$', dados.agencia):
        erros.append('Número da agência deve conter apenas números')
    
    try:
        v = int(dados.valor)
        if v <= 0:
            erros.append('Valor solicitado deve ser maior que 0')
    except ValueError:
        erros.append('Valor solicitado deve ser maior que 0')
    
    if '@' not in dados.email or not dados.email.split('@')[-1]:
        erros.append('E-mail inválido')
    
    if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', dados.cpf):
        erros.append('CPF deve estar no formato 000.000.000-00')
    elif not valida_cpf(dados.cpf):
        erros.append('CPF inválido')
    
    if not re.match(r'^\d{5}-\d{3}$', dados.cep):
        erros.append('CEP deve estar no formato 00000-000')
    
    if not re.match(r'^\d{2}/\d{2}/\d{4}$', dados.data_nascimento):
        erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
    else:
        try:
            datetime.strptime(dados.data_nascimento, '%d/%m/%Y')
        except ValueError:
            erros.append('Data de nascimento inválida')
    
    return erros

@app.get('/')
async def read_root():
    with open('index.html', 'r') as f:
        return HTMLResponse(content=f.read())

app.mount('/assets', StaticFiles(directory='assets'), name='assets')

@app.post('/solicitacao/alunos')
async def solicita_alunos(dados: Solicitacao):
    erros = valida_solicitacao(dados, 'alunos')
    oficio = '' if erros else gera_oficio(dados, 'alunos')
    return {'erros': erros, 'oficio': oficio}

@app.post('/solicitacao/docentes')
async def solicita_docentes(dados: Solicitacao):
    erros = valida_solicitacao(dados, 'docentes')
    oficio = '' if erros else gera_oficio(dados, 'docentes')
    return {'erros': erros, 'oficio': oficio}
