"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

O backend decide se a solicitação é válida e devolve o ofício já redigido.
Nada é gravado: a solicitação se encerra na resposta.
"""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def indice():
    return FileResponse(BASE / "index.html", media_type="text/html; charset=utf-8")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css; charset=utf-8")


@app.get("/app.js")
def aplicativo():
    return FileResponse(BASE / "app.js", media_type="text/javascript; charset=utf-8")


OBRIGATORIOS = (
    "nome",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade",
    "estado",
    "pais",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade_end",
    "estado_end",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
)


def campo(dados, nome):
    return str(dados.get(nome) or "").strip()


def centavos(valor):
    digitos = re.sub(r"\D", "", valor)
    return int(digitos) if digitos else 0


def moeda(valor_em_centavos):
    reais, resto = divmod(valor_em_centavos, 100)
    return "R$ " + format(reais, ",").replace(",", ".") + "," + format(resto, "02")


def cpf_valido(cpf):
    numeros = [int(digito) for digito in re.sub(r"\D", "", cpf)]
    if len(numeros) != 11:
        return False

    def verificador(base):
        total = sum(digito * peso for digito, peso in zip(base, range(len(base) + 1, 1, -1)))
        resto = total % 11
        return 0 if resto < 2 else 11 - resto

    return numeros[9] == verificador(numeros[:9]) and numeros[10] == verificador(numeros[:10])


def data_valida(texto):
    try:
        dia, mes, ano = (int(parte) for parte in texto.split("/"))
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(dados):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if campo(dados, "tipo") != "docentes":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not campo(dados, nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campo(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campo(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campo(dados, "valor")
    if valor and centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = campo(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = campo(dados, "cpf")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = campo(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campo(dados, "data_nascimento")
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(dados):
    d = {nome: campo(dados, nome) for nome in (
        "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email", "evento",
        "periodo", "cidade", "estado", "pais", "link", "detalhamento",
        "apresentacao", "data_nascimento", "logradouro", "numero", "complemento",
        "bairro", "cep", "cidade_end", "estado_end", "cpf", "rg", "banco",
        "agencia", "conta",
    )}
    linhas = [
        "Interessada(o): {} - {}".format(d["nome"], d["n_usp"]),
        "E-mail: {}".format(d["email"]),
    ]
    if campo(dados, "tipo") == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(d["programa"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(d["tipo_auxilio"]))
        linhas.append("Programa: {} - {}".format(d["programa"], d["nivel"]))
    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(d["programa"]),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(d["evento"]),
        "Período: {}".format(d["periodo"]),
        "Local: {} - {} - {}".format(d["cidade"], d["estado"], d["pais"]),
    ]
    if d["link"]:
        linhas.append("Link do evento: {}".format(d["link"]))
    linhas += [
        "Apresentação de trabalho: {}".format(d["apresentacao"]),
        "Valor solicitado: {}".format(moeda(centavos(campo(dados, "valor")))),
        "Detalhamento: {}".format(d["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(d["logradouro"], d["numero"]),
    ]
    if d["complemento"]:
        linhas.append("Complemento: {}".format(d["complemento"]))
    linhas += [
        "CEP: {}".format(d["cep"]),
        "{}, {} - {}".format(d["bairro"], d["cidade_end"], d["estado_end"]),
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


@app.post("/solicitacao")
async def solicitacao(request: Request):
    if "json" in request.headers.get("content-type", ""):
        recebido = await request.json()
    else:
        recebido = dict(await request.form())
    dados = {nome: str(valor) for nome, valor in recebido.items()}
    erros = validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": montar_oficio(dados)}
