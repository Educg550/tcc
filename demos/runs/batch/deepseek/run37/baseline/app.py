import datetime
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS = [
    "aba", "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "link_evento", "valor", "detalhamento", "apresentacao", "data_nascimento",
    "logradouro", "numero", "complemento", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]

OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def cpf_valido(cpf):
    n = [int(c) for c in cpf if c.isdigit()]
    if len(set(n)) == 1:
        return False
    for tam in (9, 10):
        soma = sum(n[i] * (tam + 1 - i) for i in range(tam))
        if (soma * 10) % 11 % 10 != n[tam]:
            return False
    return True


def data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    if not 1 <= mes <= 12:
        return False
    try:
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(d):
    erros = []
    obrig = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if d["aba"] == "alunos" else [])
    if any(not d[campo].strip() for campo in obrig):
        erros.append("Preencha todos os campos")
    if d["n_usp"] and not d["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if d["agencia"] and not d["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    digitos_valor = re.sub(r"\D", "", d["valor"])
    if d["valor"] and not (digitos_valor and int(digitos_valor) > 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if d["email"] and not RE_EMAIL.match(d["email"]):
        erros.append("E-mail inválido")
    if d["cpf"] and not RE_CPF.match(d["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    if d["cep"] and not RE_CEP.match(d["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if d["data_nascimento"] and not RE_DATA.match(d["data_nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if RE_CPF.match(d["cpf"]) and not cpf_valido(d["cpf"]):
        erros.append("CPF inválido")
    if RE_DATA.match(d["data_nascimento"]) and not data_valida(d["data_nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(d):
    linhas = [
        "Interessada(o): {} - {}".format(d["nome"], d["n_usp"]),
        "E-mail: {}".format(d["email"]),
    ]
    if d["aba"] == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(d["tipo_auxilio"]))
        linhas.append("Programa: {} - {}".format(d["programa"], d["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(d["programa"]))
    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(d["programa"]),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(d["evento"]),
        "Período: {}".format(d["periodo"]),
        "Local: {} - {} - {}".format(d["cidade_evento"], d["estado_evento"], d["pais_evento"]),
    ]
    if d["link_evento"]:
        linhas.append("Link do evento: {}".format(d["link_evento"]))
    linhas += [
        "Apresentação de trabalho: {}".format(d["apresentacao"]),
        "Valor solicitado: {}".format(d["valor"]),
        "Detalhamento: {}".format(d["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(d["logradouro"], d["numero"]),
    ]
    if d["complemento"]:
        linhas.append("Complemento: {}".format(d["complemento"]))
    linhas += [
        "CEP: {}".format(d["cep"]),
        "{}, {} - {}".format(d["bairro"], d["cidade"], d["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(d["data_nascimento"]),
        "CPF: {}".format(d["cpf"]),
        "RG / RNM: {}".format(d["rg"]),
        "Banco: {}".format(d["banco"]),
        "Agência: {}".format(d["agencia"]),
        "Conta: {}".format(d["conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    corpo = await request.json()
    d = {}
    for campo in CAMPOS:
        valor = corpo.get(campo, "")
        d[campo] = "" if valor is None else str(valor)
    if d["aba"] not in ("alunos", "docentes"):
        d["aba"] = "alunos"
    erros = validar(d)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(d)}


@app.get("/")
def index():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
