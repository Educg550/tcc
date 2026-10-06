import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse("app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")


CAMPOS_OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
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

RE_CPF = re.compile(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
RE_CEP = re.compile(r"[0-9]{5}-[0-9]{3}")
RE_DATA = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
RE_DIGITOS = re.compile(r"[0-9]+")


def _v(dados, chave):
    return str(dados.get(chave) or "").strip()


def _cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(nums[j] * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != nums[i]:
            return False
    return True


def _data_existe(valor):
    dia, mes, ano = valor.split("/")
    try:
        date(int(ano), int(mes), int(dia))
    except ValueError:
        return False
    return True


def validar(dados):
    erros = []
    tipo = dados.get("tipo", "alunos")
    obrigatorios = CAMPOS_OBRIGATORIOS
    if tipo == "alunos":
        obrigatorios = obrigatorios + ["nivel", "tipo_auxilio"]

    if any(not _v(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _v(dados, "n_usp")
    if n_usp and not RE_DIGITOS.fullmatch(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = _v(dados, "agencia")
    if agencia and not RE_DIGITOS.fullmatch(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = _v(dados, "valor_solicitado")
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _v(dados, "email")
    if email and not RE_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")

    cpf = _v(dados, "cpf")
    cpf_formato = bool(RE_CPF.fullmatch(cpf)) if cpf else False
    if cpf and not cpf_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = _v(dados, "cep")
    if cep and not RE_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_nascimento = _v(dados, "data_nascimento")
    data_formato = bool(RE_DATA.fullmatch(data_nascimento)) if data_nascimento else False
    if data_nascimento and not data_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_nascimento and data_formato and not _data_existe(data_nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados):
    tipo = dados.get("tipo", "alunos")
    programa = _v(dados, "programa")

    if tipo == "alunos":
        assunto = "Solicitação de Auxílio Financeiro - " + _v(dados, "tipo_auxilio")
        linha_programa = programa + " - " + _v(dados, "nivel")
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = programa

    linhas = [
        "Interessada(o): " + _v(dados, "nome_completo") + " - " + _v(dados, "n_usp"),
        "E-mail: " + _v(dados, "email"),
        "Assunto: " + assunto,
        "Programa: " + linha_programa,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + _v(dados, "evento"),
        "Período: " + _v(dados, "periodo"),
        "Local: " + _v(dados, "cidade_evento") + " - " + _v(dados, "estado_evento") + " - " + _v(dados, "pais_evento"),
    ]

    if _v(dados, "link_evento"):
        linhas.append("Link do evento: " + _v(dados, "link_evento"))

    linhas += [
        "Apresentação de trabalho: " + _v(dados, "apresentacao"),
        "Valor solicitado: " + _v(dados, "valor_solicitado"),
        "Detalhamento: " + _v(dados, "detalhamento"),
        "",
        "Endereço da(o) interessada(o)",
        _v(dados, "logradouro") + ", " + _v(dados, "numero"),
    ]

    if _v(dados, "complemento"):
        linhas.append("Complemento: " + _v(dados, "complemento"))

    linhas += [
        "CEP: " + _v(dados, "cep"),
        _v(dados, "bairro") + ", " + _v(dados, "cidade") + " - " + _v(dados, "estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + _v(dados, "data_nascimento"),
        "CPF: " + _v(dados, "cpf"),
        "RG / RNM: " + _v(dados, "rg"),
        "Banco: " + _v(dados, "banco"),
        "Agência: " + _v(dados, "agencia"),
        "Conta: " + _v(dados, "conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados)}
