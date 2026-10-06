"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

CAMPOS_COMUNS = (
    "nome",
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
)

CAMPOS_DE_ALUNOS = ("nivel", "tipo_auxilio")

RE_SO_DIGITOS = re.compile(r"\d+")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+")
RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")


def _texto(dados: dict, campo: str) -> str:
    return str(dados.get(campo) or "").strip()


def _valor_positivo(texto: str) -> bool:
    limpo = texto.replace("R$", "").strip()
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo) > 0
    except ValueError:
        return False


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(digitos[i] * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10) % 11 % 10 != digitos[tamanho]:
            return False
    return True


def _data_existente(texto: str) -> bool:
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(dados: dict) -> list[str]:
    aba = _texto(dados, "aba") or "alunos"
    obrigatorios = CAMPOS_COMUNS + (CAMPOS_DE_ALUNOS if aba != "docentes" else ())
    erros: list[str] = []

    if any(_texto(dados, campo) == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not RE_SO_DIGITOS.fullmatch(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not RE_SO_DIGITOS.fullmatch(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor")
    if valor and not _valor_positivo(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not RE_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not RE_CPF.fullmatch(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and not RE_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _texto(dados, "data_nascimento")
    if nascimento:
        if not RE_DATA.fullmatch(nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_existente(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados: dict) -> str:
    def v(campo: str) -> str:
        return _texto(dados, campo)

    if v("aba") == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {v('programa')}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {v('tipo_auxilio')}"
        programa = f"Programa: {v('programa')} - {v('nivel')}"

    linhas = [
        f"Interessada(o): {v('nome')} - {v('n_usp')}",
        f"E-mail: {v('email')}",
        f"Assunto: {assunto}",
        programa,
        "",
        f"A CCP-{v('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v('evento')}",
        f"Período: {v('periodo')}",
        f"Local: {v('cidade_evento')} - {v('estado_evento')} - {v('pais_evento')}",
    ]

    if v("link_evento"):
        linhas.append(f"Link do evento: {v('link_evento')}")

    linhas += [
        f"Apresentação de trabalho: {v('apresentacao')}",
        f"Valor solicitado: {v('valor')}",
        f"Detalhamento: {v('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v('logradouro')}, {v('numero')}",
    ]

    if v("complemento"):
        linhas.append(f"Complemento: {v('complemento')}")

    linhas += [
        f"CEP: {v('cep')}",
        f"{v('bairro')}, {v('cidade')} - {v('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v('data_nascimento')}",
        f"CPF: {v('cpf')}",
        f"RG / RNM: {v('rg')}",
        f"Banco: {v('banco')}",
        f"Agência: {v('agencia')}",
        f"Conta: {v('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(dados: dict[str, Any] = Body(...)):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="static")
