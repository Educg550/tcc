from fastapi import FastAPI, HTTPException
from fastapi.middleware.staticfiles import StaticFiles
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import re
import os

app = FastAPI()

class DadosSolicitacao(BaseModel):
    nome: str
    nusp: str
    programa: str
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link: Optional[str] = ""
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
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
    nivel: Optional[str] = None
    tipo: Optional[str] = None

    class Config:
        extra = "ignore"

def validar_dados(d: DadosSolicitacao) -> list:
    erros = set()

    # Campos obrigatórios vazios
    obrigatorios = [
        d.nome, d.nusp, d.programa, d.email, d.evento,
        d.periodo, d.cidade_evento, d.estado_evento, d.pais_evento,
        d.valor, d.detalhamento, d.apresentacao, d.nascimento,
        d.logradouro, d.numero, d.bairro, d.cep, d.cidade, d.estado,
        d.cpf, d.rg, d.banco, d.agencia, d.conta
    ]
    if d.nivel is not None:
        obrigatorios.append(d.nivel)
    if d.tipo is not None:
        obrigatorios.append(d.tipo)

    if any(str(item).strip() == "" for item in obrigatorios if item is not None):
        erros.add("Preencha todos os campos")

    # N. USP apenas números
    if not re.fullmatch(r"\d+", d.nusp):
        erros.add("N. USP deve conter apenas números")

    # Agência apenas números
    if not re.fullmatch(r"\d+", d.agencia):
        erros.add("Número da agência deve conter apenas números")

    # Valor
    digitos_valor = re.sub(r"\D", "", d.valor)
    if digitos_valor == "" or int(digitos_valor) <= 0:
        erros.add("Valor solicitado deve ser maior que 0")

    # E-mail
    if "@" not in d.email or d.email.split("@")[-1] == "" or "." not in d.email.split("@")[-1]:
        erros.add("E-mail inválido")

    # CPF
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d.cpf):
        erros.add("CPF deve estar no formato 000.000.000-00")
    else:
        if not validar_cpf(d.cpf):
            erros.add("CPF inválido")

    # CEP
    if not re.fullmatch(r"\d{5}-\d{3}", d.cep):
        erros.add("CEP deve estar no formato 00000-000")

    # Data de nascimento
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d.nascimento):
        erros.add("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dd, mm, aaaa = map(int, d.nascimento.split("/"))
        if not (1 <= mm <= 12) or not (1 <= dd <= 31):
            erros.add("Data de nascimento inválida")
        elif mm in [4, 6, 9, 11] and dd > 30:
            erros.add("Data de nascimento inválida")
        elif mm == 2 and dd > 29:
            erros.add("Data de nascimento inválida")

    return list(erros)

def validar_cpf(cpf: str) -> bool:
    cpf_digits = re.sub(r"\D", "", cpf)
    if len(set(cpf_digits)) == 1:
        return False

    def calcula_digito(cpf_soma, pos):
        soma = sum(int(cpf_soma[i]) * (pos - i) for i in range(pos - 1))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    dig1 = calcula_digito(cpf_digits, 10)
    dig2 = calcula_digito(cpf_digits, 11)

    return cpf_digits[-2:] == f"{dig1}{dig2}"

@app.post("/api/solicitar")
async def solicitar(d: DadosSolicitacao):
    erros = validar_dados(d)
    if erros:
        raise HTTPException(status_code=400, detail={"erros": erros})

    aba = "alunos" if d.nivel is not None and d.tipo is not None else "docentes"
    dig = re.sub(r"\D", "", d.valor)
    valor_formatado = f"R$ {int(dig) / 100:.2f}".replace('.', ',')

    oficio = f"""Interessada(o): {d.nome} - {d.nusp}
E-mail: {d.email}
Assunto: Solicitação de Auxílio Financeiro - {d.tipo if aba == 'alunos' else 'Verba do programa'}
Programa: {d.programa}{' - ' + d.nivel if aba == 'alunos' else ''}

A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:

Dados do evento
Evento: {d.evento}
Período: {d.periodo}
Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}"""

    if d.link and d.link.strip():
        oficio += f"\nLink do evento: {d.link}"

    oficio += f"""
Apresentação de trabalho: {d.apresentacao}
Valor solicitado: {valor_formatado}
Detalhamento: {d.detalhamento}

Endereço da(o) interessada(o)
{d.logradouro}, {d.numero}"""

    if d.complemento and d.complemento.strip():
        oficio += f"\nComplemento: {d.complemento}"

    oficio += f"""
CEP: {d.cep}
{d.bairro}, {d.cidade} - {d.estado}

Dados para pagamento
Data de nascimento: {d.nascimento}
CPF: {d.cpf}
RG / RNM: {d.rg}
Banco: {d.banco}
Agência: {d.agencia}
Conta: {d.conta}

Encaminhe-se ao Serviço Financeiro para providências."""

    return {"oficio": oficio, "erros": []}

@app.get("/", response_class=HTMLResponse)
async def get_home():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r", encoding="utf-8") as f:
        return f.read()

app.mount("/", StaticFiles(directory=".", html=True), name="static")