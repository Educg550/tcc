from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import re
from datetime import datetime

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
async def read_index():
    return FileResponse("index.html")

class Solicitacao(BaseModel):
    aba: str
    nome_completo: str = ''
    n_usp: str = ''
    programa: str = ''
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str = ''
    nome_evento: str = ''
    periodo: str = ''
    cidade_evento: str = ''
    estado_evento: str = ''
    pais_evento: str = ''
    link_evento: str = ''
    valor_solicitado: str = ''
    detalhamento: str = ''
    apresentar_trabalho: str = ''
    data_nascimento: str = ''
    logradouro: str = ''
    numero: str = ''
    complemento: str = ''
    bairro: str = ''
    cep: str = ''
    cidade: str = ''
    estado: str = ''
    cpf: str = ''
    rg_rnm: str = ''
    nome_banco: str = ''
    numero_agencia: str = ''
    numero_conta: str = ''

@app.post("/solicitar")
async def solicitar(s: Solicitacao):
    erros = []
    campos_obrigatorios = [
        s.nome_completo, s.n_usp, s.programa, s.email, s.nome_evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor_solicitado,
        s.detalhamento, s.apresentar_trabalho, s.data_nascimento, s.logradouro,
        s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg_rnm,
        s.nome_banco, s.numero_agencia, s.numero_conta
    ]
    if s.aba == 'alunos':
        campos_obrigatorios.extend([s.nivel, s.tipo_auxilio])
    if any(f is None or str(f).strip() == '' for f in campos_obrigatorios):
        erros.append('Preencha todos os campos')
    if s.n_usp and not re.fullmatch(r'\d+', s.n_usp):
        erros.append('N. USP deve conter apenas números')
    if s.numero_agencia and not re.fullmatch(r'\d+', s.numero_agencia):
        erros.append('Número da agência deve conter apenas números')
    valor_num = None
    if s.valor_solicitado:
        v = re.sub(r'\D', '', s.valor_solicitado)
        if v:
            valor_num = int(v)
    if valor_num is None or valor_num <= 0:
        erros.append('Valor solicitado deve ser maior que 0')
    if s.email and not re.fullmatch(r'[^@]+@[^@]+\.[^@]+', s.email):
        erros.append('E-mail inválido')
    if s.cpf:
        if not re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', s.cpf):
            erros.append('CPF deve estar no formato 000.000.000-00')
        else:
            cpf_digits = re.sub(r'\D', '', s.cpf)
            if len(cpf_digits) == 11:
                def calc_dv(d):
                    soma = sum(int(d[i]) * (10 - i) for i in range(9))
                    resto = soma % 11
                    return '0' if resto < 2 else str(11 - resto)
                if calc_dv(cpf_digits) != cpf_digits[9] or calc_dv(cpf_digits[:9] + cpf_digits[9]) != cpf_digits[10]:
                    erros.append('CPF inválido')
    if s.cep and not re.fullmatch(r'\d{5}-\d{3}', s.cep):
        erros.append('CEP deve estar no formato 00000-000')
    if s.data_nascimento:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', s.data_nascimento):
            erros.append('Data de nascimento deve estar no formato dd/mm/aaaa')
        else:
            try:
                datetime.strptime(s.data_nascimento, '%d/%m/%Y')
            except ValueError:
                erros.append('Data de nascimento inválida')
    if erros:
        return {'erros': erros}
    valor_formatado = f'R$ {valor_num/100:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    tipo_auxilio_oficio = s.tipo_auxilio if s.aba == 'alunos' else 'Verba do programa'
    nivel_oficio = s.nivel if s.aba == 'alunos' else ''
    link_line = f"Link do evento: {s.link_evento}" if s.link_evento and s.link_evento.strip() else ''
    comp_line = f"Complemento: {s.complemento}" if s.complemento and s.complemento.strip() else ''
    oficio = f"""Interessada(o): {s.nome_completo} - {s.n_usp}
E-mail: {s.email}
Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio_oficio}
Programa: {s.programa}{' - ' + nivel_oficio if nivel_oficio else ''}

A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {s.nome_evento}
Período: {s.periodo}
Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}
{link_line}
Apresentação de trabalho: {s.apresentar_trabalho}
Valor solicitado: {valor_formatado}
Detalhamento: {s.detalhamento}

Endereço da(o) interessada(o)
{s.logradouro}, {s.numero}
{comp_line}
CEP: {s.cep}
{s.bairro}, {s.cidade} - {s.estado}

Dados para pagamento
Data de nascimento: {s.data_nascimento}
CPF: {s.cpf}
RG / RNM: {s.rg_rnm}
Banco: {s.nome_banco}
Agência: {s.numero_agencia}
Conta: {s.numero_conta}

Encaminhe-se ao Serviço Financeiro para providências."""
    linhas = oficio.split('\n')
    if not link_line:
        linhas = [l for l in linhas if l != '']
    if not comp_line:
        linhas = [l for l in linhas if l != '']
    oficio = '\n'.join(linhas)
    return {'oficio': oficio}
