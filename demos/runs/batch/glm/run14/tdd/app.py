import datetime
import os
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"

app = FastAPI(title="Pós-Graduação IME-USP - Solicitação de Auxílio Financeiro")

# Monta os arquivos estáticos: style.css, app.js e a pasta assets/
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


class Solicitacao(BaseModel):
    tipo: str  # "alunos" ou "docentes"
    nome: str = ""
    numero_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


# --------------------------------------------------------------------------
# Formatação
# --------------------------------------------------------------------------

def formatar_valor(digitos: str) -> str:
    """Converte dígitos em valor monetário brasileiro.

    Os dígitos representam os centavos. Ex.: "150000" -> "R$ 1.500,00".
    """
    digitos = re.sub(r"\D", "", digitos)
    if not digitos:
        return "R$ 0,00"
    centavos = int(digitos)
    reais, cent = divmod(centavos, 100)
    parte_inteira = f"{reais:,}".replace(",", ".")
    return f"R$ {parte_inteira},{cent:02d}"


def formatar_cpf(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) != 11:
        return valor
    return f"{digitos[0:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:11]}"


def formatar_cep(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) != 8:
        return valor
    return f"{digitos[0:5]}-{digitos[5:8]}"


def formatar_data(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) != 8:
        return valor
    return f"{digitos[0:2]}/{digitos[2:4]}/{digitos[4:8]}"


# --------------------------------------------------------------------------
# Validação
# --------------------------------------------------------------------------

CAMPOS_OBRIGATORIOS = [
    "nome", "numero_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_OBRIGATORIOS_ALUNOS = CAMPOS_OBRIGATORIOS + ["nivel", "tipo_auxilio"]


def validar_email(valor: str) -> bool:
    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(padrao, valor) is not None


def validar_cpf(digitos: str) -> bool:
    """Valida os dígitos verificadores do CPF."""
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito1 = 0 if resto == 10 else resto
    if digito1 != int(digitos[9]):
        return False
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito2 = 0 if resto == 10 else resto
    return digito2 == int(digitos[10])


def validar_data(dia: int, mes: int, ano: int) -> bool:
    try:
        datetime.date(ano, mes, dia)
        return True
    except ValueError:
        return False


def validar(s: Solicitacao) -> List[str]:
    erros: List[str] = []
    obrigatorios = CAMPOS_OBRIGATORIOS_ALUNOS if s.tipo == "alunos" else CAMPOS_OBRIGATORIOS
    vazios = [campo for campo in obrigatorios if not getattr(s, campo).strip()]
    if vazios:
        erros.append("Preencha todos os campos")

    numero_usp = s.numero_usp.strip()
    if numero_usp and not numero_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = s.agencia.strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = s.valor.strip()
    if valor:
        valor_limpo = re.sub(r"[R$\s\.,]", "", valor)
        if not valor_limpo.isdigit() or int(valor_limpo) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = s.email.strip()
    if email and not validar_email(email):
        erros.append("E-mail inválido")

    cpf = s.cpf.strip()
    if cpf:
        cpf_limpo = re.sub(r"\D", "", cpf)
        if len(cpf_limpo) != 11 or not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not validar_cpf(cpf_limpo):
            erros.append("CPF inválido")

    cep = s.cep.strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = s.data_nascimento.strip()
    if data and not re.match(r"^\d{2}/\d{2}/\d{4}$", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data:
        partes = data.split("/")
        dia, mes, ano = int(partes[0]), int(partes[1]), int(partes[2])
        if not validar_data(dia, mes, ano):
            erros.append("Data de nascimento inválida")

    return erros


# --------------------------------------------------------------------------
# Geração do ofício
# --------------------------------------------------------------------------

def gerar_oficio(s: Solicitacao) -> str:
    valor_fmt = formatar_valor(s.valor)
    cpf_fmt = formatar_cpf(s.cpf)
    cep_fmt = formatar_cep(s.cep)
    data_fmt = formatar_data(s.data_nascimento)

    if s.tipo == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"

    linhas: List[str] = [
        f"Interessada(o): {s.nome} - {s.numero_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.extend([
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ])
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas.extend([
        f"CEP: {cep_fmt}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data_fmt}",
        f"CPF: {cpf_fmt}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


# --------------------------------------------------------------------------
# Rotas
# --------------------------------------------------------------------------

@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@app.get("/style.css")
def style():
    return FileResponse(STATIC_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
def app_js():
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


@app.post("/api/solicitacao")
def receber_solicitacao(s: Solicitacao):
    erros = validar(s)
    if erros:
        return JSONResponse(content={"erros": erros, "formatados": {}})
    return {
        "erros": [],
        "oficio": gerar_oficio(s),
        "formatados": {
            "valor": formatar_valor(s.valor),
            "cpf": formatar_cpf(s.cpf),
            "cep": formatar_cep(s.cep),
            "data_nascimento": formatar_data(s.data_nascimento),
        },
    }
