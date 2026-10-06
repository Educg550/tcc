import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


CAMPOS = [
    "aba", "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio",
    "email", "nome_evento", "periodo", "cidade_evento", "estado_evento",
    "pais_evento", "link_evento", "valor_solicitado", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "complemento",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia",
    "conta",
]

OBRIGATORIOS_COMUNS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia",
    "conta",
]


def cpf_valido(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(numeros[j] * ((i + 1) - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[i]:
            return False
    return True


def validar(d):
    erros = []

    obrigatorios = list(OBRIGATORIOS_COMUNS)
    if d["aba"] != "docentes":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not d[c] for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if d["n_usp"] and not d["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")

    if d["agencia"] and not d["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")

    if d["valor_solicitado"]:
        digitos = re.sub(r"\D", "", d["valor_solicitado"])
        if not digitos or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if d["email"] and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", d["email"]):
        erros.append("E-mail inválido")

    if d["cpf"]:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", d["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(d["cpf"]):
            erros.append("CPF inválido")

    if d["cep"] and not re.match(r"^\d{5}-\d{3}$", d["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    if d["data_nascimento"]:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", d["data_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(d["data_nascimento"], "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d):
    linhas = [
        "Interessada(o): {} - {}".format(d["nome_completo"], d["n_usp"]),
        "E-mail: {}".format(d["email"]),
    ]
    if d["aba"] == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(d["programa"]))
    else:
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - {}".format(d["tipo_auxilio"])
        )
        linhas.append("Programa: {} - {}".format(d["programa"], d["nivel"]))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            d["programa"]
        ),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(d["nome_evento"]),
        "Período: {}".format(d["periodo"]),
        "Local: {} - {} - {}".format(
            d["cidade_evento"], d["estado_evento"], d["pais_evento"]
        ),
    ]
    if d["link_evento"]:
        linhas.append("Link do evento: {}".format(d["link_evento"]))
    linhas += [
        "Apresentação de trabalho: {}".format(d["apresentacao"]),
        "Valor solicitado: {}".format(d["valor_solicitado"]),
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
    form = await request.form()
    d = {campo: str(form.get(campo) or "").strip() for campo in CAMPOS}
    erros = validar(d)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"erros": [], "oficio": gerar_oficio(d)})
