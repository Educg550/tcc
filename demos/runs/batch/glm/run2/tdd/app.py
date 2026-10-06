""""Aplicação FastAPI para o formulário de auxílio financeiro da Pós-Graduação IME-USP.

Serve os arquivos estáticos e valida as solicitações.
"""
import re
from datetime import date
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class DadosSolicitacao(BaseModel):
"""Dados de uma solicitação de auxílio financeiro."""
nomeCompleto: str = ""
numeroUSP: str = ""
programa: str = ""
nivel: str = ""
tipoAuxilio: str = ""
email: str = ""
nomeEvento: str = ""
periodo: str = ""
cidadeEvento: str = ""
estadoEvento: str = ""
paisEvento: str = ""
linkEvento: str = ""
valorSolicitado: str = ""
detalhamento: str = ""
apresentaTrabalho: str = ""
dataNascimento: str = ""
logradouro: str = ""
numero: str = ""
complemento: str = ""
bairro: str = ""
cep: str = ""
cidade: str = ""
estado: str = ""
cpf: str = ""
rg: str = ""
banco: str = ""
agencia: str = ""
conta: str = ""


# pylint: disable=too-many-locals
@app.post("/api/solicitacao/{tipo}")
async def processar_solicitacao(tipo: str, dados: DadosSolicitacao):
"""""Processa uma solicitação, validando e gerando o ofício."""
if tipo not in ('alunos', 'docentes'):
return JSONResponse(status_code=404, content={"ok": False, "erros": ["Tipo inválido"]})

erros = validar(dados, tipo)
if erros:
return {"ok": False, "erros": erros}

oficio = gerar_oficio(dados, tipo)
return {"ok": True, "oficio": oficio}


def validar(dados, tipo):
"""""Valida os dados de uma solicitação. Retorna lista de mensagens de erro."""
erros = []

# Campos obrigatórios (vazios)
obrigatorios = [
dados.nomeCompleto, dados.numeroUSP, dados.programa, dados.email,
dados.nomeEvento, dados.periodo, dados.cidadeEvento, dados.estadoEvento,
dados.paisEvento, dados.valorSolicitado, dados.detalhamento,
dados.apresentaTrabalho, dados.dataNascimento, dados.logradouro,
dados.numero, dados.bairro, dados.cep, dados.cidade, dados.estado,
dados.cpf, dados.rg, dados.banco, dados.agencia, dados.conta
]
if tipo == 'alunos':
obrigatorios.append(dados.nivel)
obrigatorios.append(dados.tipoAuxilio)
if any(campo.strip() == '' for campo in obrigatorios):
erros.append("Preencha todos os campos")

# N. USP
if dados.numeroUSP and not dados.numeroUSP.isdigit():
erros.append("N. USP deve conter apenas números")

# Agência
if dados.agencia and not dados.agencia.isdigit():
erros.append("Número da agência deve conter apenas números")

# Valor
if dados.valorSolicitado:
valor = dados.valorSolicitado.replace('R$ ', '').replace('.', '').replace(',', '.')
try:
num = float(valor)
if num <= 0:
erros.append("Valor solicitado deve ser maior que 0")
except ValueError:
erros.append("Valor solicitado deve ser maior que 0")

# E-mail
if dados.email:
if '@' not in dados.email or '.' not in dados.email.split('@')[-1]:
erros.append("E-mail inválido")

# CPF formato
if dados.cpf:
if not re.match(r'^\d{3}\.\d{3}-\d{2}$', dados.cpf) and not re.match(r'^\d{3}\.\d{3}\.\d{3}\-\d{2}$', dados.cpf):
erros.append("CPF deve estar no formato 000.000.000-00")

# CEP formato
if dados.cep:
if not re.match(r'^\d{5}\-\d{3}$', dados.cep):
erros.append("CEP deve estar no formato 00000-000")

# Data de nascimento formato
if dados.dataNascimento:
match = re.match(r'^(\d{2})\/(\d{2})\/(\d{4})$', dados.dataNascimento)
if not match:
erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
else:
try:
dia = int(match.group(1))
mes = int(match.group(2))
date(dia=dia, month=mes, year=int(match.group(3)))
except ValueError:
erros.append("Data de nascimento inválida")

# CPF dígito verificador
if dados.cpf:
if re.match(r'^\d{3}\.\d{3}\.\d{3}\-\d{2}$', dados.cpf):
digitos = ''.join(re.findall(r'\d', dados.cpf))
if len(digitos) == 11 and not validar_cpf(digitos):
erros.append("CPF inválido")

return erros


def validar_cpf(digitos):
"""""Valida os dígitos verificadores de um CPF."""
if len(digitos) != 11 or digitos == digitos[0] * 11:
return False
soma = 0
for i in range(9):
soma += int(digitos[i]) * (10 - i)
resto = soma % 11
if resto < 2:
dv1 = 0
else:
dv1 = 11 - resto
if int(digitos[9]) != dv1:
return False
soma = 0
for i in range(10):
soma += int(digitos[i]) * (11 - i)
resto = soma % 11
if resto < 2:
dv2 = 0
else:
dv2 = 11 - resto
return int(digitos[10]) == dv2


def formatar_moeda(valor_str):
"""""Formata uma string de valor como moeda brasileira (R$ 1.500,00)."""
digitos = valor_str.replace('R$ ', '').replace('.', '').replace(',', '')
if not digitos.isdigit():
return valor_str
digitos = digitos.lstrip('0') or '0'
digitos = digitos.rjust(3, '0')
centavos = digitos[-2:]
parte_inteira = digits[:0 - 2] or '0'
partes = []
while len(parte_inteira) > 3:
partes.insert(0, parte_inteira[-3:])
parte_inteira = parte_inteira[:-3]
partes.insert(0, parte_inteira)
return 'R$ ' + '.'.join(partes) + ',' + centavos


def gerar_oficio(dados, tipo):
"""""Gera o texto do ofício com os dados preenchidos."""
linhas = []
linhas.append(f"Interessada(o): {dados.nomeCompleto} - {dados.numeroUSP}")
linhas.append(f"E-mail: {dados.email}")
if tipo == 'alunos':
linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados.tipoAuxilio}")
linhas.append(f"Programa: {dados.programa} - {dados.nivel}")
else:
linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
linhas.append(f"Programa: {dados.programa}")
linhas.append("")
linhas.append(f"A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
linhas.append("interessada(o) acima, conforme segue:")
linhas.append("")
linhas.append("Dados do evento")
linhas.append(f"Evento: {dados.nomeEvento}")
linhas.append(f"Período: {dados.periodo}")
linhas.append(f"Local: {dados.cidadeEvento} - {dados.estadoEvento} - {dados.paisEvento}")
if dados.linkEvento.strip():
linhas.append(f"Link do evento: {dados.linkEvento}")
linhas.append(f"Apresentação de trabalho: {dados.apresentaTrabalho}")
linhas.append(f"Valor solicitado: {formatar_moeda(dados.valorSolicitado)}")
linhas.append(f"Detalhamento: {dados.detalhamento}")
linhas.append("")
linhas.append("Endereço da(o) interessada(o)")
linhas.append(f"{dados.logradouro}, {dados.numero}")
if dados.complemento.strip():
linhas.append(f"Complemento: {dados.complemento}")
linhas.append(f"CEP: {dados.cep}")
linhas.append(f"{dados.bairro}, {dados.cidade} - {dados.estado}")
linhas.append("")
linhas.append("Dados para pagamento")
linhas.append(f"Data de nascimento: {dados.dataNascimento}")
linhas.append(f"CPF: {dados.cpf}")
linhas.append(f"RG / RNM: {dados.rg}")
linhas.append(f"Banco: {dados.banco}")
linhas.append(f"Agência: {dados.agencia}")
linhas.append(f"Conta: {dados.conta}")
linhas.append("")
linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
return "\n".join(linhas)


# Montagem da aplicação: montar estáticos
app.mount("/", StaticFiles(directory=".", html=True), name="estaticos")
