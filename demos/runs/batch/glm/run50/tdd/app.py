import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade: str = ""
    estado: str = ""
    pais: str = ""
    link: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade_end: str = ""
    estado_end: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


OBRIGATORIOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade",
    "estado", "pais", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta",
)
OBRIGATORIOS_ALUNOS = OBRIGATORIOS + ("nivel", "tipo_auxilio")

SO_DIGITOS = re.compile(r"[0-9]+")
FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
FORMATO_CPF = re.compile(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
FORMATO_CEP = re.compile(r"[0-9]{5}-[0-9]{3}")
FORMATO_DATA = re.compile(r"[0-3][0-9]/[0-9]{2}/[0-9]{4}")


def centavos(valor):
    digitos = re.sub(r"\D", "", valor)
    return int(digitos) if digitos else 0


def moeda(cent):
    reais, resto = divmod(cent, 100)
    return "R$ " + "{:,}".format(reais).replace(",", ".") + "," + "{:02d}".format(resto)


def cpf_valido(cpf):
    numeros = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(numeros) != 11:
        return False
    soma = sum(n * (10 - i) for i, n in enumerate(numeros[:9]))
    dv1 = 0 if soma % 11 < 2 else 11 - soma % 11
    if dv1 != numeros[9]:
        return False
    soma = sum(n * (11 - i) for i, n in enumerate(numeros[:10]))
    dv2 = 0 if soma % 11 < 2 else 11 - soma % 11
    return dv2 == numeros[10]


def validar(aba, dados):
    erros = []
    c = dados.model_dump()
    obrigatorios = OBRIGATORIOS_ALUNOS if aba == "alunos" else OBRIGATORIOS
    if any(not c[campo].strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if c["n_usp"].strip() and not SO_DIGITOS.fullmatch(c["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if c["agencia"].strip() and not SO_DIGITOS.fullmatch(c["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if c["valor"].strip() and centavos(c["valor"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if c["email"].strip() and not FORMATO_EMAIL.fullmatch(c["email"]):
        erros.append("E-mail inválido")
    if c["cpf"].strip():
        if not FORMATO_CPF.fullmatch(c["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(c["cpf"]):
            erros.append("CPF inválido")
    if c["cep"].strip() and not FORMATO_CEP.fullmatch(c["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if c["data_nascimento"].strip():
        if not FORMATO_DATA.fullmatch(c["data_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(c["data_nascimento"], "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(aba, dados):
    c = dados.model_dump()
    if aba == "alunos":
        assunto = c["tipo_auxilio"]
        linha_programa = "Programa: {} - {}".format(c["programa"], c["nivel"])
    else:
        assunto = "Verba do programa"
        linha_programa = "Programa: " + c["programa"]
    linhas = [
        "Interessada(o): {} - {}".format(c["nome"], c["n_usp"]),
        "E-mail: " + c["email"],
        "Assunto: Solicitação de Auxílio Financeiro - " + assunto,
        linha_programa,
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(c["programa"]),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + c["evento"],
        "Período: " + c["periodo"],
        "Local: {} - {} - {}".format(c["cidade"], c["estado"], c["pais"]),
    ]
    if c["link"].strip():
        linhas.append("Link do evento: " + c["link"])
    linhas += [
        "Apresentação de trabalho: " + c["apresentacao"],
        "Valor solicitado: " + moeda(centavos(c["valor"])),
        "Detalhamento: " + c["detalhamento"],
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(c["logradouro"], c["numero"]),
        "Complemento: " + c["complemento"],
        "CEP: " + c["cep"],
        "{}, {} - {}".format(c["bairro"], c["cidade_end"], c["estado_end"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + c["data_nascimento"],
        "CPF: " + c["cpf"],
        "RG / RNM: " + c["rg"],
        "Banco: " + c["banco"],
        "Agência: " + c["agencia"],
        "Conta: " + c["conta"],
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao/{aba}")
def criar_solicitacao(aba: str, dados: Solicitacao):
    if aba not in ("alunos", "docentes"):
        return JSONResponse(status_code=404, content={"ok": False, "erros": []})
    erros = validar(aba, dados)
    if erros:
        return JSONResponse(status_code=422, content={"ok": False, "erros": erros})
    return {"ok": True, "oficio": gerar_oficio(aba, dados)}


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html", media_type="text/html; charset=utf-8")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css; charset=utf-8")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript; charset=utf-8")


@app.get("/assets/{caminho:path}")
def estaticos(caminho: str):
    return FileResponse(BASE / "assets" / caminho)
