"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

CAMPOS_COMUNS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
)
CAMPOS_ALUNOS = ("nivel", "tipo_auxilio")

FORMATO_CPF = re.compile(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
FORMATO_CEP = re.compile(r"[0-9]{5}-[0-9]{3}")
FORMATO_DATA = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
SOMENTE_DIGITOS = re.compile(r"[0-9]+")


def texto(campos, chave):
    return str(campos.get(chave) or "").strip()


def digitos(valor):
    return re.sub(r"\D", "", valor)


def moeda(valor):
    d = digitos(valor)
    inteiro = d[:-2] or "0"
    centavos = d[-2:].rjust(2, "0")
    return "R$ " + re.sub(r"\B(?=(\d{3})+$)", ".", inteiro) + "," + centavos


def cpf_valido(valor):
    d = digitos(valor)
    if len(d) != 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * (i + 1 - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(d[i]):
            return False
    return True


def data_valida(valor):
    dia, mes, ano = (int(p) for p in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(aba, campos):
    obrigatorios = CAMPOS_COMUNS + (CAMPOS_ALUNOS if aba == "alunos" else ())
    erros = []

    if any(not texto(campos, chave) for chave in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(campos, "n_usp")
    if n_usp and not SOMENTE_DIGITOS.fullmatch(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = texto(campos, "agencia")
    if agencia and not SOMENTE_DIGITOS.fullmatch(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = texto(campos, "valor")
    if valor and not (digitos(valor) and int(digitos(valor)) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(campos, "email")
    if email and not FORMATO_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")

    cpf = texto(campos, "cpf")
    cpf_no_formato = bool(FORMATO_CPF.fullmatch(cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = texto(campos, "cep")
    if cep and not FORMATO_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(campos, "data_nascimento")
    nascimento_no_formato = bool(FORMATO_DATA.fullmatch(nascimento))
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if nascimento_no_formato and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(aba, campos):
    programa = texto(campos, "programa")
    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = "Programa: " + programa
    else:
        assunto = "Solicitação de Auxílio Financeiro - " + texto(campos, "tipo_auxilio")
        linha_programa = "Programa: " + programa + " - " + texto(campos, "nivel")

    linhas = [
        "Interessada(o): " + texto(campos, "nome") + " - " + texto(campos, "n_usp"),
        "E-mail: " + texto(campos, "email"),
        "Assunto: " + assunto,
        linha_programa,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + texto(campos, "evento"),
        "Período: " + texto(campos, "periodo"),
        "Local: " + texto(campos, "cidade_evento") + " - "
        + texto(campos, "estado_evento") + " - " + texto(campos, "pais_evento"),
    ]

    link = texto(campos, "link_evento")
    if link:
        linhas.append("Link do evento: " + link)

    linhas += [
        "Apresentação de trabalho: " + texto(campos, "apresentacao"),
        "Valor solicitado: " + moeda(texto(campos, "valor")),
        "Detalhamento: " + texto(campos, "detalhamento"),
        "",
        "Endereço da(o) interessada(o)",
        texto(campos, "logradouro") + ", " + texto(campos, "numero"),
    ]

    complemento = texto(campos, "complemento")
    if complemento:
        linhas.append("Complemento: " + complemento)

    linhas += [
        "CEP: " + texto(campos, "cep"),
        texto(campos, "bairro") + ", " + texto(campos, "cidade") + " - " + texto(campos, "estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + texto(campos, "data_nascimento"),
        "CPF: " + texto(campos, "cpf"),
        "RG / RNM: " + texto(campos, "rg"),
        "Banco: " + texto(campos, "banco"),
        "Agência: " + texto(campos, "agencia"),
        "Conta: " + texto(campos, "conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    corpo = await request.json()
    aba = corpo.get("aba") or "alunos"
    campos = corpo.get("campos") or {}

    erros = validar(aba, campos)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": gerar_oficio(aba, campos)}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse("index.html")


@app.get("/style.css", include_in_schema=False)
def estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse("app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
