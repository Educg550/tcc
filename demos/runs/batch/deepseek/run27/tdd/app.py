"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=str(BASE / "assets")), name="assets")


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


CAMPOS_COMUNS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]
CAMPOS_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]


def _texto(dados, campo):
    return str(dados.get(campo, "")).strip()


def _centavos(texto):
    digitos = re.sub(r"[^0-9]", "", texto)
    return int(digitos) if digitos else 0


def _formatar_moeda(texto):
    inteiro, resto = divmod(_centavos(texto), 100)
    return "R$ " + f"{inteiro:,}".replace(",", ".") + f",{resto:02d}"


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"[^0-9]", "", cpf)]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def _validar(dados):
    campos = list(CAMPOS_COMUNS)
    if dados.get("aba", "alunos") == "alunos":
        campos += CAMPOS_ALUNOS

    erros = []
    if any(not _texto(dados, campo) for campo in campos):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "N. USP")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "NÚMERO DA AGÊNCIA")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "VALOR SOLICITADO (R$)")
    if valor and _centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "E-MAIL")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "CEP")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = _texto(dados, "DATA DE NASCIMENTO")
    if data:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados):
    alunos = dados.get("aba", "alunos") == "alunos"

    if alunos:
        assunto = "Solicitação de Auxílio Financeiro - " + _texto(dados, "TIPO DE AUXÍLIO")
        programa = "Programa: " + _texto(dados, "PROGRAMA") + " - " + _texto(dados, "NÍVEL")
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + _texto(dados, "PROGRAMA")

    linhas = [
        "Interessada(o): " + _texto(dados, "NOME COMPLETO - SEM ABREVIAR") + " - " + _texto(dados, "N. USP"),
        "E-mail: " + _texto(dados, "E-MAIL"),
        "Assunto: " + assunto,
        programa,
        "",
        "A CCP-" + _texto(dados, "PROGRAMA") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + _texto(dados, "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
        "Período: " + _texto(dados, "PERÍODO DO EVENTO, EXAME OU DEFESA"),
        "Local: "
        + _texto(dados, "CIDADE DO EVENTO, EXAME OU DEFESA")
        + " - "
        + _texto(dados, "ESTADO DO EVENTO, EXAME OU DEFESA")
        + " - "
        + _texto(dados, "PAÍS DO EVENTO, EXAME OU DEFESA"),
    ]

    link = _texto(dados, "LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append("Link do evento: " + link)

    linhas += [
        "Apresentação de trabalho: " + _texto(dados, "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
        "Valor solicitado: " + _formatar_moeda(_texto(dados, "VALOR SOLICITADO (R$)")),
        "Detalhamento: " + _texto(dados, "DETALHAMENTO DO PEDIDO"),
        "",
        "Endereço da(o) interessada(o)",
        _texto(dados, "LOGRADOURO") + ", " + _texto(dados, "NÚMERO"),
    ]

    complemento = _texto(dados, "COMPLEMENTO")
    if complemento:
        linhas.append("Complemento: " + complemento)

    linhas += [
        "CEP: " + _texto(dados, "CEP"),
        _texto(dados, "BAIRRO") + ", " + _texto(dados, "CIDADE") + " - " + _texto(dados, "ESTADO"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + _texto(dados, "DATA DE NASCIMENTO"),
        "CPF: " + _texto(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
        "RG / RNM: " + _texto(dados, "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
        "Banco: " + _texto(dados, "NOME DO BANCO"),
        "Agência: " + _texto(dados, "NÚMERO DA AGÊNCIA"),
        "Conta: " + _texto(dados, "NÚMERO DA CONTA"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitar(dados: dict):
    erros = _validar(dados)
    if erros:
        return {"erros": erros}
    return {"titulo": "Solicitação registrada", "oficio": _oficio(dados)}
