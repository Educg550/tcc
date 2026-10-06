import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent

app = FastAPI()

CAMPOS_TEXTO = [
    "nome_completo",
    "programa",
    "email",
    "nome_evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "detalhamento",
    "apresentacao",
    "logradouro",
    "numero",
    "bairro",
    "cidade",
    "estado",
    "rg",
    "banco",
    "conta",
]


class Solicitacao(BaseModel):
    aba: str = ""
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
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


def so_digitos(valor):
    return valor.isdigit() and len(valor) > 0


def valor_inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def email_valido(valor):
    return "@" in valor and "." in valor.split("@")[-1] and " " not in valor


def cpf_valido(valor):
    numeros = re.sub(r"\D", "", valor)
    if len(numeros) != 11:
        return False
    digitos = [int(c) for c in numeros]
    peso = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(d * p for d, p in zip(digitos[:9], peso))
    resto = soma % 11
    esperado1 = 0 if resto < 2 else 11 - resto
    if digitos[9] != esperado1:
        return False
    peso = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(d * p for d, p in zip(digitos[:10], peso))
    resto = soma % 11
    esperado2 = 0 if resto < 2 else 11 - resto
    return digitos[10] == esperado2


def data_valida(valor):
    partes = valor.split("/")
    if len(partes) != 3:
        return False
    try:
        dia, mes, ano = (int(p) for p in partes)
    except ValueError:
        return False
    try:
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formatar_valor(valor):
    centavos = valor_inteiro(valor)
    reais, resto = divmod(centavos, 100)
    texto = f"{reais:,}".replace(",", ".")
    return f"R$ {texto},{resto:02d}"


def validar(d):
    erros = []
    obrigatorio_faltando = False

    for campo in CAMPOS_TEXTO:
        if not d[campo].strip():
            obrigatorio_faltando = True

    if d["aba"] == "alunos":
        if not d["nivel"].strip() or not d["tipo_auxilio"].strip():
            obrigatorio_faltando = True

    if not d["n_usp"].strip() or not d["agencia"].strip() \
            or not d["valor_solicitado"].strip() \
            or not d["data_nascimento"].strip() or not d["cep"].strip() \
            or not d["cpf"].strip():
        obrigatorio_faltando = True

    if obrigatorio_faltando:
        erros.append("Preencha todos os campos")

    if d["n_usp"] and not so_digitos(d["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if d["agencia"] and not so_digitos(d["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    valor = valor_inteiro(d["valor_solicitado"])
    if d["valor_solicitado"] and (valor is None or valor <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if d["email"] and not email_valido(d["email"]):
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
        elif not data_valida(d["data_nascimento"]):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d):
    linhas = []
    linhas.append(f"Interessada(o): {d['nome_completo']} - {d['n_usp']}")
    linhas.append(f"E-mail: {d['email']}")
    if d["aba"] == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}")
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d['programa']}")
    linhas.append("")
    linhas.append(
        f"A CCP-{d['programa']} aprovou na data de hoje, "
        "a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:"
    )
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {d['nome_evento']}")
    linhas.append(f"Período: {d['periodo']}")
    linhas.append(f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}")
    if d["link_evento"].strip():
        linhas.append(f"Link do evento: {d['link_evento']}")
    linhas.append(f"Apresentação de trabalho: {d['apresentacao']}")
    linhas.append(f"Valor solicitado: {formatar_valor(d['valor_solicitado'])}")
    linhas.append(f"Detalhamento: {d['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['logradouro']}, {d['numero']}")
    if d["complemento"].strip():
        linhas.append(f"Complemento: {d['complemento']}")
    linhas.append(f"CEP: {d['cep']}")
    linhas.append(f"{d['bairro']}, {d['cidade']} - {d['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d['data_nascimento']}")
    linhas.append(f"CPF: {d['cpf']}")
    linhas.append(f"RG / RNM: {d['rg']}")
    linhas.append(f"Banco: {d['banco']}")
    linhas.append(f"Agência: {d['agencia']}")
    linhas.append(f"Conta: {d['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def criar_solicitacao(solicitacao: Solicitacao):
    d = solicitacao.model_dump()
    erros = validar(d)
    if erros:
        return {"valido": False, "erros": erros}
    return {"valido": True, "erros": [], "oficio": gerar_oficio(d)}


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html", media_type="text/html")


app.mount("/assets", StaticFiles(directory=str(ROOT / "assets")), name="assets")
