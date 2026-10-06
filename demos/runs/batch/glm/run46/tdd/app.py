"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

_RAIZ = Path(__file__).resolve().parent

_OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


def _texto(dados, campo):
    valor = dados.get(campo, "")
    return valor.strip() if isinstance(valor, str) else ""


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def _cpf_valido(cpf):
    if cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    if soma * 10 % 11 % 10 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    return soma * 10 % 11 % 10 == int(cpf[10])


def _data_valida(nascimento):
    try:
        date(int(nascimento[4:]), int(nascimento[2:4]), int(nascimento[:2]))
    except ValueError:
        return False
    return True


def _erros(dados, tipo):
    obrigatorios = _OBRIGATORIOS
    if tipo == "aluno":
        obrigatorios = obrigatorios + ["nivel", "tipo_auxilio"]

    erros = []
    if any(_texto(dados, campo) == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor")
    if re.fullmatch(r"\d+", valor) is None or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None:
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf and re.fullmatch(r"\d{11}", cpf) is None:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and re.fullmatch(r"\d{8}", cep) is None:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _texto(dados, "data_nascimento")
    if nascimento and re.fullmatch(r"\d{8}", nascimento) is None:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not _data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, tipo):
    programa = _texto(dados, "programa")
    if tipo == "docente":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = "Programa: " + programa
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + _texto(dados, "tipo_auxilio")
        linha_programa = "Programa: " + programa + " - " + _texto(dados, "nivel")

    linhas = [
        "Interessada(o): " + _texto(dados, "nome_completo") + " - " + _texto(dados, "n_usp"),
        "E-mail: " + _texto(dados, "email"),
        assunto,
        linha_programa,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + _texto(dados, "nome_evento"),
        "Período: " + _texto(dados, "periodo"),
        "Local: "
        + _texto(dados, "cidade_evento")
        + " - "
        + _texto(dados, "estado_evento")
        + " - "
        + _texto(dados, "pais_evento"),
    ]

    link = _texto(dados, "link_evento")
    if link:
        linhas.append("Link do evento: " + link)

    linhas += [
        "Apresentação de trabalho: " + _texto(dados, "apresentacao"),
        "Valor solicitado: " + _moeda(int(_texto(dados, "valor"))),
        "Detalhamento: " + _texto(dados, "detalhamento"),
        "",
        "Endereço da(o) interessada(o)",
        _texto(dados, "logradouro") + ", " + _texto(dados, "numero"),
    ]

    complemento = _texto(dados, "complemento")
    if complemento:
        linhas.append("Complemento: " + complemento)

    cpf = _texto(dados, "cpf")
    cep = _texto(dados, "cep")
    nascimento = _texto(dados, "data_nascimento")
    linhas += [
        "CEP: " + cep[:5] + "-" + cep[5:],
        _texto(dados, "bairro") + ", " + _texto(dados, "cidade") + " - " + _texto(dados, "estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + nascimento[:2] + "/" + nascimento[2:4] + "/" + nascimento[4:],
        "CPF: " + cpf[:3] + "." + cpf[3:6] + "." + cpf[6:9] + "-" + cpf[9:],
        "RG / RNM: " + _texto(dados, "rg"),
        "Banco: " + _texto(dados, "banco"),
        "Agência: " + _texto(dados, "agencia"),
        "Conta: " + _texto(dados, "conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def criar_solicitacao(dados: dict):
    tipo = "docente" if dados.get("tipo") == "docente" else "aluno"
    erros = _erros(dados, tipo)
    if erros:
        return JSONResponse(status_code=422, content={"ok": False, "erros": erros})
    return {"ok": True, "oficio": _oficio(dados, tipo)}


@app.get("/")
@app.get("/index.html")
def indice():
    return FileResponse(_RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(_RAIZ / "style.css")


@app.get("/app.js")
def roteiro():
    return FileResponse(_RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=_RAIZ / "assets"), name="assets")
