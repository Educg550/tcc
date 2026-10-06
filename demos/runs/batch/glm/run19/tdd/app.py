"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/static/assets", StaticFiles(directory=str(BASE / "assets")), name="assets")

OBRIGATORIOS_COMUNS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade",
    "estado", "pais", "valor", "detalhamento", "apresentacao", "nascimento",
    "logradouro", "numero", "bairro", "cep", "cidade_end", "estado_end",
    "cpf", "rg", "banco", "agencia", "conta",
]
OBRIGATORIOS_ALUNOS = ["nivel", "tipo_auxilio"] + OBRIGATORIOS_COMUNS


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/static/style.css")
def style_css() -> FileResponse:
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/static/app.js")
def app_js() -> FileResponse:
    return FileResponse(BASE / "app.js", media_type="application/javascript")


@app.post("/solicitar")
def solicitar(dados: dict[str, Any]) -> dict[str, Any]:
    erros = validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "titulo": "Solicitação registrada", "oficio": montar_oficio(dados)}


def _texto(valor: Any) -> str:
    return "" if valor is None else str(valor).strip()


def _vazio(valor: Any) -> bool:
    return _texto(valor) == ""


def _centavos(valor: Any) -> int | None:
    if isinstance(valor, int):
        return valor
    digitos = re.sub(r"\D", "", _texto(valor))
    return int(digitos) if digitos else None


def _formatar_valor(centavos: int) -> str:
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def _cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[i]) * (posicao + 1 - i) for i in range(posicao))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[posicao]):
            return False
    return True


def _data_valida(data_txt: str) -> bool:
    dia, mes, ano = (int(parte) for parte in data_txt.split("/"))
    try:
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def validar(dados: dict[str, Any]) -> list[str]:
    tipo = _texto(dados.get("tipo")) or "alunos"
    obrigatorios = OBRIGATORIOS_ALUNOS if tipo == "alunos" else OBRIGATORIOS_COMUNS
    erros: list[str] = []

    if any(_vazio(dados.get(campo)) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados.get("n_usp"))
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados.get("agencia"))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    if not _vazio(dados.get("valor")):
        centavos = _centavos(dados.get("valor"))
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados.get("email"))
    if email and ("@" not in email or email.rsplit("@", 1)[-1] == ""):
        erros.append("E-mail inválido")

    cpf = _texto(dados.get("cpf"))
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = _texto(dados.get("cep"))
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _texto(dados.get("nascimento"))
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not _data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(dados: dict[str, Any]) -> str:
    programa = _texto(dados.get("programa"))
    if _texto(dados.get("tipo")) == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {programa}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - " + _texto(dados.get("tipo_auxilio"))
        linha_programa = f"Programa: {programa} - {_texto(dados.get('nivel'))}"

    linhas = [
        f"Interessada(o): {_texto(dados.get('nome'))} - {_texto(dados.get('n_usp'))}",
        f"E-mail: {_texto(dados.get('email'))}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados.get('evento'))}",
        f"Período: {_texto(dados.get('periodo'))}",
        f"Local: {_texto(dados.get('cidade'))} - {_texto(dados.get('estado'))} - {_texto(dados.get('pais'))}",
    ]

    link = _texto(dados.get("link"))
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {_texto(dados.get('apresentacao'))}",
        f"Valor solicitado: {_formatar_valor(_centavos(dados.get('valor')) or 0)}",
        f"Detalhamento: {_texto(dados.get('detalhamento'))}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_texto(dados.get('logradouro'))}, {_texto(dados.get('numero'))}",
    ]

    complemento = _texto(dados.get("complemento"))
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {_texto(dados.get('cep'))}",
        f"{_texto(dados.get('bairro'))}, {_texto(dados.get('cidade_end'))} - {_texto(dados.get('estado_end'))}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_texto(dados.get('nascimento'))}",
        f"CPF: {_texto(dados.get('cpf'))}",
        f"RG / RNM: {_texto(dados.get('rg'))}",
        f"Banco: {_texto(dados.get('banco'))}",
        f"Agência: {_texto(dados.get('agencia'))}",
        f"Conta: {_texto(dados.get('conta'))}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)
