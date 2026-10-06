from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Endereco(BaseModel):
    nascimento: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    estado: str


class Solicitacao(BaseModel):
    nome: str
    numero_usp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link: str
    valor: str
    detalhamento: str
    apresentacao: str
    endereco: Endereco
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


import re


def validar_cpf(cpf: str) -> bool:
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False
    digitos = [int(c) for c in cpf if c.isdigit()]
    soma = sum(d * f for d, f in zip(digitos[:9], range(10, 1, -1)))
    dv1 = (soma * 10 % 11) % 10
    if dv1 != digitos[9]:
        return False
    soma = sum(d * f for d, f in zip(digitos[:10], range(11, 2, -1)))
    dv2 = (soma * 10 % 11) % 10
    return dv2 == digitos[10]


def validar_data(data: str) -> bool:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return False
    try:
        dia, mes, ano = (int(p) for p in data.split("/"))
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


@app.post("/api/solicitacao")
def criar_solicitacao(s: Solicitacao):
    pass
