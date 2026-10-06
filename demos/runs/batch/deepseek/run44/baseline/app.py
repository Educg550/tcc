"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

CAMPOS = (
    "nome",
    "nusp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "link",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "complemento",
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
OPCIONAIS = ("link", "complemento")
EXCLUSIVOS_ALUNOS = ("nivel", "tipo_auxilio")


def _texto(valor):
    return valor.strip() if isinstance(valor, str) else ""


def _so_digitos(valor):
    return re.fullmatch(r"[0-9]+", valor) is not None


def _cpf_valido(digitos):
    for i in (9, 10):
        soma = sum(int(digitos[j]) * (i + 1 - j) for j in range(i))
        if (soma * 10) % 11 % 10 != int(digitos[i]):
            return False
    return True


def _data_existe(valor):
    dia, mes, ano = (int(parte) for parte in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _moeda(centavos):
    reais, cent = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def _oficio(c, aba, centavos):
    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = c["programa"]
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {c['tipo_auxilio']}"
        programa = f"{c['programa']} - {c['nivel']}"

    linhas = [
        f"Interessada(o): {c['nome']} - {c['nusp']}",
        f"E-mail: {c['email']}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['evento']}",
        f"Período: {c['periodo']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c["link"]:
        linhas.append(f"Link do evento: {c['link']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao']}",
        f"Valor solicitado: {_moeda(centavos)}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c["complemento"]:
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['data_nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitar(dados: dict):
    aba = "docentes" if dados.get("aba") == "docentes" else "alunos"
    c = {campo: _texto(dados.get(campo)) for campo in CAMPOS}

    obrigatorios = [campo for campo in CAMPOS if campo not in OPCIONAIS]
    if aba == "docentes":
        obrigatorios = [campo for campo in obrigatorios if campo not in EXCLUSIVOS_ALUNOS]

    erros = []

    if any(not c[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if c["nusp"] and not _so_digitos(c["nusp"]):
        erros.append("N. USP deve conter apenas números")
    if c["agencia"] and not _so_digitos(c["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    centavos = None
    if c["valor"]:
        digitos = re.sub(r"\D", "", c["valor"])
        centavos = int(digitos) if digitos else 0
        if centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if c["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", c["email"]):
        erros.append("E-mail inválido")

    cpf_ok = bool(c["cpf"]) and re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", c["cpf"]) is not None
    data_ok = bool(c["data_nascimento"]) and re.fullmatch(
        r"[0-9]{2}/[0-9]{2}/[0-9]{4}", c["data_nascimento"]
    ) is not None

    if c["cpf"] and not cpf_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if c["cep"] and re.fullmatch(r"[0-9]{5}-[0-9]{3}", c["cep"]) is None:
        erros.append("CEP deve estar no formato 00000-000")
    if c["data_nascimento"] and not data_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_ok and not _cpf_valido(re.sub(r"\D", "", c["cpf"])):
        erros.append("CPF inválido")
    if data_ok and not _data_existe(c["data_nascimento"]):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"erros": erros, "oficio": None}

    return {"erros": [], "oficio": _oficio(c, aba, centavos)}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css", include_in_schema=False)
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
