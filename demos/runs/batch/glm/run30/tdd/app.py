from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

CAMPOS_OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end",
    "estado_end", "cpf", "rg", "banco", "agencia", "conta",
)
CAMPOS_OBRIGATORIOS_DOCENTES = (
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end",
    "estado_end", "cpf", "rg", "banco", "agencia", "conta",
)
CAMPOS_OPCIONAIS = ("link", "complemento")

MSG_CAMPOS = "Preencha todos os campos"
MSG_NUSP = "N. USP deve conter apenas números"
MSG_AGENCIA = "Número da agência deve conter apenas números"
MSG_VALOR = "Valor solicitado deve ser maior que 0"
MSG_EMAIL = "E-mail inválido"
MSG_CPF_FMT = "CPF deve estar no formato 000.000.000-00"
MSG_CEP = "CEP deve estar no formato 00000-000"
MSG_DATA_FMT = "Data de nascimento deve estar no formato dd/mm/aaaa"
MSG_CPF_INV = "CPF inválido"
MSG_DATA_INV = "Data de nascimento inválida"

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_cpf(cpf: str) -> bool:
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    soma = sum((10 - i) * d for i, d in enumerate(digitos[:9]))
    d1 = (soma * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != digitos[9]:
        return False
    soma2 = sum((11 - i) * d for i, d in enumerate(digitos[:10]))
    d2 = (soma2 * 10) % 11
    if d2 == 10:
        d2 = 0
    return d2 == digitos[10]


def validar_data(dia: int, mes: int, ano: int) -> bool:
    dias_por_mes = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if mes < 1 or mes > 12:
        return False
    if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0):
        dias_por_mes[1] = 29
    return 1 <= dia <= dias_por_mes[mes - 1]


def formatar_valor(valor: str) -> str:
    v = valor.replace(".", "").replace(",", "").strip()
    cents = int(v)
    inteiro, centavos = divmod(cents, 100)
    texto = f"{inteiro:,}".replace(",", ".")
    return f"R$ {texto},{centavos:02d}"


def verificar_campos(dados: dict, aba: str) -> list[str]:
    erros = []

    obrigatorios = CAMPOS_OBRIGATORIOS_DOCENTES if aba == "docentes" else CAMPOS_OBRIGATORIOS
    if any(str(dados.get(c, "")).strip() == "" for c in obrigatorios):
        erros.append(MSG_CAMPOS)

    n_usp = str(dados.get("n_usp", ""))
    if n_usp and not n_usp.isdigit():
        erros.append(MSG_NUSP)

    agencia = str(dados.get("agencia", ""))
    if agencia and not agencia.isdigit():
        erros.append(MSG_AGENCIA)

    valor_raw = str(dados.get("valor", "")).strip()
    if valor_raw:
        try:
            cents = int(valor_raw.replace(".", "").replace(",", "").strip())
        except ValueError:
            cents = 0
        if cents <= 0:
            erros.append(MSG_VALOR)

    email = str(dados.get("email", "")).strip()
    if email and not RE_EMAIL.match(email):
        erros.append(MSG_EMAIL)

    cpf = str(dados.get("cpf", "")).strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append(MSG_CPF_FMT)
        elif not validar_cpf(cpf):
            erros.append(MSG_CPF_INV)

    cep = str(dados.get("cep", "")).strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append(MSG_CEP)

    data = str(dados.get("data_nascimento", "")).strip()
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append(MSG_DATA_FMT)
        else:
            dia, mes, ano = int(data[:2]), int(data[3:5]), int(data[6:10])
            if not validar_data(dia, mes, ano):
                erros.append(MSG_DATA_INV)

    return erros


def gerar_oficio(dados: dict, aba: str) -> str:
    hoje = date.today().strftime("%d/%m/%Y")
    linhas: list[str] = []
    linhas.append(f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}")
    linhas.append(f"E-mail: {dados['email']}")
    if aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    linhas.append("")
    linhas.append(
        f"A CCP-{dados['programa']} aprovou na data de hoje ({hoje}), a solicitação "
        "de auxílio financeiro para a interessada(o) acima, conforme segue:"
    )
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {dados['nome_evento']}")
    linhas.append(f"Período: {dados['periodo']}")
    linhas.append(f"Local: {dados['cidade']} - {dados['estado']} - {dados['pais']}")
    if dados.get("link", "").strip():
        linhas.append(f"Link do evento: {dados['link'].strip()}")
    linhas.append(f"Apresentação de trabalho: {dados['apresentacao']}")
    linhas.append(f"Valor solicitado: {formatar_valor(str(dados['valor']))}")
    linhas.append(f"Detalhamento: {dados['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{dados['logradouro']}, {dados['numero']}")
    if dados.get("complemento", "").strip():
        linhas.append(f"Complemento: {dados['complemento'].strip()}")
    linhas.append(f"CEP: {dados['cep']}")
    linhas.append(f"{dados['bairro']}, {dados['cidade_end']} - {dados['estado_end']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {dados['data_nascimento']}")
    linhas.append(f"CPF: {dados['cpf']}")
    linhas.append(f"RG / RNM: {dados['rg']}")
    linhas.append(f"Banco: {dados['banco']}")
    linhas.append(f"Agência: {dados['agencia']}")
    linhas.append(f"Conta: {dados['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "index.html", media_type="text/html")


@app.post("/solicitacao")
async def criar_solicitacao(request: Request):
    form = await request.form()
    dados = {k: str(v) for k, v in form.items()}
    aba = dados.get("aba", "alunos")
    erros = verificar_campos(dados, aba)
    if erros:
        return {"ok": False, "erros": erros, "oficio": None}
    return {"ok": True, "erros": [], "oficio": gerar_oficio(dados, aba)}


app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")


@app.get("/style.css")
async def style():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def script():
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")
