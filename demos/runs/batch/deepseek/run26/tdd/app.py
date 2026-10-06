import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script_da_pagina():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


def _campo(dados, nome):
    return str(dados.get(nome) or "").strip()


def _so_digitos(valor):
    return bool(re.fullmatch(r"\d+", valor))


def _valor_positivo(valor):
    limpo = re.sub(r"[^\d,]", "", valor).replace(",", ".")
    try:
        return float(limpo) > 0
    except ValueError:
        return False


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    for i in (9, 10):
        soma = sum(int(digitos[j]) * ((i + 1) - j) for j in range(i))
        resto = (soma * 10) % 11
        if (0 if resto == 10 else resto) != int(digitos[i]):
            return False
    return True


def _data_existente(texto):
    try:
        dia, mes, ano = texto.split("/")
        date(int(ano), int(mes), int(dia))
        return True
    except ValueError:
        return False


def validar(dados, aba):
    erros = []
    obrigatorios = [
        "nome", "n_usp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais", "valor", "detalhamento",
        "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
        "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba != "docentes":
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not _campo(dados, nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _campo(dados, "n_usp")
    if n_usp and not _so_digitos(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = _campo(dados, "agencia")
    if agencia and not _so_digitos(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = _campo(dados, "valor")
    if valor and not _valor_positivo(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _campo(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = _campo(dados, "cpf")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _campo(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _campo(dados, "data_nascimento")
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_existente(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


@app.post("/solicitacao")
async def solicitar(request: Request):
    tipo = request.headers.get("content-type", "")
    if "application/json" in tipo:
        dados = await request.json()
    else:
        dados = dict(await request.form())
    aba = _campo(dados, "aba").lower() or "alunos"
    return {"erros": validar(dados, aba)}
