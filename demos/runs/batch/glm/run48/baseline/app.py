from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class Solicitacao(BaseModel):
    tipo: str  # "aluno" ou "docente"
    nome: str
    nusp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    nome_evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: Optional[str] = ""
    valor_solicitado: float
    detalhamento: str
    apresentacao: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = ""
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str

def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = ((soma * 10) % 11) % 10
        if int(cpf[i]) != digito:
            return False
    return True

def validar_data(data_str: str) -> bool:
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False

@app.post("/api/solicitacao")
async def criar_solicitacao(s: Solicitacao):
    erros: List[str] = []

    campos_obrigatorios = [
        s.nome, s.nusp, s.programa, s.email, s.nome_evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento,
        str(s.valor_solicitado) if s.valor_solicitado else "", s.detalhamento,
        s.apresentacao, s.data_nascimento, s.logradouro, s.numero, s.bairro,
        s.cep, s.cidade, s.estado, s.cpf, s.rg, s.banco, s.agencia, s.conta
    ]
    if s.tipo == "aluno":
        campos_obrigatorios.extend([s.nivel or "", s.tipo_auxilio or ""])
    if any(c.strip() == "" for c in campos_obrigatorios):
        erros.append("Preencha todos os campos")

    if s.nusp and not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor_solicitado is not None and s.valor_solicitado <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email and ("@" not in s.email or s.email.split("@")[-1].strip() == ""):
        erros.append("E-mail inválido")
    if s.cpf and not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif s.cpf and re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', s.cpf) and not validar_cpf(s.cpf):
        erros.append("CPF inválido")
    if s.cep and not re.match(r'^\d{5}-\d{3}$', s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if s.data_nascimento and not re.match(r'^\d{2}/\d{2}/\d{4}$', s.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif s.data_nascimento and re.match(r'^\d{2}/\d{2}/\d{4}$', s.data_nascimento) and not validar_data(s.data_nascimento):
        erros.append("Data de nascimento inválida")

    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})

    valor_fmt = f"R$ {s.valor_solicitado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if s.tipo == "docente":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {s.programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        linha_programa = f"Programa: {s.programa} - {s.nivel}"

    linhas = [
        f"Interessada(o): {s.nome} - {s.nusp}",
        f"E-mail: {s.email}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento:
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.extend([
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ])
    if s.complemento:
        linhas.append(f"Complemento: {s.complemento}")
    linhas.extend([
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])

    return {"oficio": "\n".join(linhas)}

@app.get("/")
async def root():
    return JSONResponse(content={"status": "ok"})
