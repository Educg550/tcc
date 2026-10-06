import datetime
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]


@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


def _digitos(texto):
    return re.sub(r"\D", "", texto or "")


def _somente_numeros(texto):
    return bool(re.fullmatch(r"\d+", texto or ""))


def _cpf_valido(cpf):
    numeros = [int(c) for c in _digitos(cpf)]
    if len(numeros) != 11:
        return False
    for i in range(9, 11):
        soma = sum(numeros[j] * (i + 1 - j) for j in range(i))
        if (soma * 10 % 11) % 10 != numeros[i]:
            return False
    return True


def _validar(d, aba):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba != "DOCENTES":
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not d.get(campo, "").strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = d.get("n_usp", "")
    if n_usp and not _somente_numeros(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = d.get("agencia", "")
    if agencia and not _somente_numeros(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = d.get("valor", "")
    if valor:
        digitos = _digitos(valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = d.get("email", "")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = d.get("cpf", "")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = d.get("cep", "")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = d.get("data_nascimento", "")
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(parte) for parte in data.split("/"))
            try:
                datetime.date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _gerar_oficio(d, aba):
    if aba == "DOCENTES":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + d["programa"]
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + d["tipo_auxilio"]
        programa = "Programa: " + d["programa"] + " - " + d["nivel"]

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
        "Evento: " + d["evento"],
        "Período: " + d["periodo"],
        "Local: " + d["cidade_evento"] + " - " + d["estado_evento"] + " - " + d["pais_evento"],
    ]

    if d.get("link_evento", "").strip():
        linhas.append("Link do evento: " + d["link_evento"])

    linhas += [
        "Apresentação de trabalho: " + d["apresentacao"],
        "Valor solicitado: " + d["valor"],
        "Detalhamento: " + d["detalhamento"],
        "",
        "Endereço da(o) interessada(o)",
        d["logradouro"] + ", " + d["numero"],
    ]

    if d.get("complemento", "").strip():
        linhas.append("Complemento: " + d["complemento"])

    linhas += [
        "CEP: " + d["cep"],
        d["bairro"] + ", " + d["cidade"] + " - " + d["estado"],
        "",
        "Dados para pagamento",
        "Data de nascimento: " + d["data_nascimento"],
        "CPF: " + d["cpf"],
        "RG / RNM: " + d["rg"],
        "Banco: " + d["banco"],
        "Agência: " + d["agencia"],
        "Conta: " + d["conta"],
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    try:
        corpo = await request.json()
    except Exception:
        formulario = await request.form()
        corpo = dict(formulario)

    if not isinstance(corpo, dict):
        corpo = {}

    dados = {chave: ("" if valor is None else str(valor)) for chave, valor in corpo.items()}
    aba = dados.get("aba") or "ALUNOS"

    erros = _validar(dados, aba)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": _gerar_oficio(dados, aba)}
