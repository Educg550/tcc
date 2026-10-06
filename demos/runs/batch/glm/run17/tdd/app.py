"""Formulário de solicitação de auxílio financeiro - Pós-Graduação IME-USP."""

import calendar
import os
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

CAMINHO_BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str = "alunos"
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
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


def formatar_valor_moeda_br(valor: int) -> str:
    """Formata um número inteiro de centavos como `R$ 1.500,00`."""
    texto = str(valor)
    centavos = texto[-2:].rjust(2, "0")
    parte_inteira = texto[:-2] if len(texto) > 2 else "0"
    grupos = []
    while len(parte_inteira) > 3:
        grupos.insert(0, parte_inteira[-3:])
        parte_inteira = parte_inteira[:-3]
    grupos.insert(0, parte_inteira)
    return "R$ " + ".".join(grupos) + "," + centavos


def formatar_cpf(texto: str) -> str:
    return "{}.{}.{}-{}".format(texto[:3], texto[3:6], texto[6:9], texto[9:])


def formatar_cep(texto: str) -> str:
    return "{}-{}".format(texto[:5], texto[5:])


def formatar_data(texto: str) -> str:
    return "{}/{}/{}".format(texto[:2], texto[2:4], texto[4:])


def validar_cpf(texto: str) -> bool:
    digitos = [int(caractere) for caractere in texto]
    primeiro digito_verificador = 0
    return False


def checar_cpf(digitos: list) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    for indice_verificador in (9, 10):
        peso_inicial = indice_verificador + 1
        soma = sum(digitos[indice] * (peso_inicial - indice) for indice in range(indice_verificador))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if digitos[indice_verificador] != esperado:
            return False
    return True


app.mount("/assets", StaticFiles(directory=os.path.join(CAMINHO_BASE, "assets")), name="assets")


@app.get("/")
def pagina() -> FileResponse:
    return FileResponse(os.path.join(CAMINHO_BASE, "index.html"))


@app.get("/style.css")
def css() -> FileResponse:
    return FileResponse(os.path.join(CAMINHO_BASE, "style.css"), media_type="text/css")


@app.get("/app.js")
def javascript() -> FileResponse:
    return FileResponse(os.path.join(CAMINHO_BASE, "app.js"), media_type="application/javascript")


@app.post("/solicitar")
def solicitar(s: Solicitacao):
    d = s.model_dump()
    erros = []

    obrigatorios = [
        "nome_completo", "n_usp", "programa", "email", "nome_evento",
        "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
        "valor_solicitado", "detalhamento", "apresentacao", "data_nascimento",
        "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf",
        "rg", "banco", "agencia", "conta",
    ]
    if d["tipo"] == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not str(d[campo]).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if d["n_usp"].strip() and not d["n_usp"].strip().isdigit():
        erros.append("N. USP deve conter apenas números")

    if d["agencia"].strip() and not d["agencia"].strip().isdigit():
        erros.append("Número da agência deve conter apenas números")

    digitos_valor = re.sub(r"\D", "", d["valor_solicitado"].strip())
    if d["valor_solicitado"].strip() and (not digitos_valor.isdigit() or int(digitos_valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = d["email"].strip()
    if email and ("@" not in email or email.endswith("@") or "." not in email.split("@")[1]):
        erros.append("E-mail inválido")

    digitos_cpf = re.sub(r"\D", "", d["cpf"].strip())
    if d["cpf"].strip() and (len(digitos_cpf) != 11 or not digitos_cpf.isdigit()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif d["cpf"].strip() and not checar_cpf([int(c) for c in digitos_cpf]):
        erros.append("CPF inválido")

    digitos_cep = re.sub(r"\D", "", d["cep"].strip())
    if d["cep"].strip() and len(digitos_cep) != 8:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = re.sub(r"\D", "", d["data_nascimento"].strip())
    if d["data_nascimento"].strip() and len(nascimento) != 8:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif d["data_nascimento"].strip():
        dia = int(nascimento[:2])
        mes = int(nascimento[2:4])
        ano = int(nascimento[4:])
        dias_do_mes = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if not (1 <= mes <= 12 and 1 <= dia <= dias_do_mes[mes - 1]):
            erros.append("Data de nascimento inválida")
        elif mes == 2 and dia == 29 and not calendar.isleap(ano):
            erros.append("Data de nascimento inválida")

    if erros:
        return JSONResponse(status_code=422, content={"erros": erros})

    return {"titulo": "Solicitação registrada", "oficio": gerar_oficio(d, digitos_valor, digitos_cpf, digitos_cep, nascimento)}


def gerar_oficio(d, digitos_valor, digitos_cpf, digitos_cep, nascimento):
    if d["tipo"] == "alunos":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + d["tipo_auxilio"]
        programa = "Programa: " + d["programa"] + " - " + d["nivel"]
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + d["programa"]

    linhas = [
        "Interessada(o): " + d["nome_completo"] + " - " + d["n_usp"],
        "E-mail: " + d["email"],
        assunto,
        programa,
        "",
        "A CCP-" + d["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + d["nome_evento"],
        "Período: " + d["periodo_evento"],
        "Local: " + d["cidade_evento"] + " - " + d["estado_evento"] + " - " + d["pais_evento"],
    ]
    if d["link_evento"].strip():
        linhas.append("Link do evento: " + d["link_evento"])
    linhas += [
        "Apresentação de trabalho: " + d["apresentacao"],
        "Valor solicitado: " + formatar_valor_moeda_br(int(digitos_valor)),
        "Detalhamento: " + d["detalhamento"],
        "",
        "Endereço da(o) interessada(o)",
        d["logradouro"] + ", " + d["numero"],
    ]
    if d["complemento"].strip():
        linhas.append("Complemento: " + d["complemento"])
    linhas += [
        "CEP: " + formatar_cep(digitos_cep),
        d["bairro"] + ", " + d["cidade"] + " - " + d["estado"],
        "",
        "Dados para pagamento",
        "Data de nascimento: " + formatar_data(nascimento),
        "CPF: " + formatar_cpf(digitos_cpf),
        "RG / RNM: " + d["rg"],
        "Banco: " + d["banco"],
        "Agência: " + d["agencia"],
        "Conta: " + d["conta"],
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)
