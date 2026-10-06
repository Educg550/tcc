import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

ALUNOS_OBRIGATORIOS = [
    "nome_completo", "nusp", "programa", "nivel", "tipo_auxilio", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentar_trabalho", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "numero_agencia",
    "numero_conta",
]

DOCENTES_OBRIGATORIOS = [
    "nome_completo", "nusp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentar_trabalho", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "numero_agencia",
    "numero_conta",
]


def _digits(s):
    return re.sub(r"\D", "", s or "")


def format_valor(raw):
    cents = int(_digits(raw) or 0)
    inteiro, resto = divmod(cents, 100)
    s = f"{inteiro:02d}"
    while len(s) > 3:
        s = s[:-3] + "." + s[-3:]
    return f"R$ {s},{resto:02d}"


def format_cpf(raw):
    d = _digits(raw)[:11]
    out = ""
    for i, c in enumerate(d):
        if i == 3 or i == 6:
            out += "."
        if i == 9:
            out += "-"
        out += c
    return out


def format_cep(raw):
    d = _digits(raw)[:8]
    if len(d) > 5:
        return d[:5] + "-" + d[5:]
    return d


def format_data(raw):
    d = _digits(raw)[:8]
    parts = []
    for i in range(0, len(d), 2):
        parts.append(d[i:i + 2])
    return "/".join(parts)


def cpf_valido(cpf):
    d = _digits(cpf)
    if len(d) != 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * (i + 1 - j) for j in range(i))
        if (soma * 10) % 11 % 10 != int(d[i]):
            return False
    return True


def data_valida(s):
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def email_valido(s):
    if "@" not in s:
        return False
    _, _, dominio = s.rpartition("@")
    return bool(dominio) and "." in dominio


def validar(aba, d):
    obrigatorios = ALUNOS_OBRIGATORIOS if aba == "alunos" else DOCENTES_OBRIGATORIOS
    erros = []
    if any(not (d.get(c) or "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if not _digits(d["nusp"]) == d["nusp"] or not d["nusp"]:
        if d["nusp"] and not d["nusp"].isdigit():
            erros.append("N. USP deve conter apenas números")
    if d["numero_agencia"] and not d["numero_agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = _digits(d["valor_solicitado"])
    if not valor or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if d["email"] and not email_valido(d["email"]):
        erros.append("E-mail inválido")
    if d["cpf"] and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif d["cpf"] and not cpf_valido(d["cpf"]):
        erros.append("CPF inválido")
    if d["cep"] and not re.fullmatch(r"\d{5}-\d{3}", d["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if d["data_nascimento"]:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d["data_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(d["data_nascimento"]):
            erros.append("Data de nascimento inválida")
    return erros


def oficio(aba, d):
    linhas = []
    linhas.append(f"Interessada(o): {d['nome_completo']} - {d['nusp']}")
    linhas.append(f"E-mail: {d['email']}")
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}")
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d['programa']}")
    linhas.append("")
    linhas.append("A CCP-" + d["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {d['nome_evento']}")
    linhas.append(f"Período: {d['periodo_evento']}")
    linhas.append(f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}")
    if d["link_evento"].strip():
        linhas.append(f"Link do evento: {d['link_evento']}")
    linhas.append(f"Apresentação de trabalho: {d['apresentar_trabalho']}")
    linhas.append(f"Valor solicitado: {format_valor(d['valor_solicitado'])}")
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
    linhas.append(f"RG / RNM: {d['rg_rnm']}")
    linhas.append(f"Banco: {d['nome_banco']}")
    linhas.append(f"Agência: {d['numero_agencia']}")
    linhas.append(f"Conta: {d['numero_conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitacao(payload: dict):
    aba = payload.get("aba", "alunos")
    erros = validar(aba, payload)
    if erros:
        return {"errors": erros, "oficio": None, "solicitacao_registrada": False}
    return {"errors": [], "oficio": oficio(aba, payload), "Solicitação registrada": True}


@app.get("/format/valor")
async def format_valor_ep(raw: str):
    return {"formatted": format_valor(raw)}


@app.get("/format/cpf")
async def format_cpf_ep(raw: str):
    return {"formatted": format_cpf(raw)}


@app.get("/format/cep")
async def format_cep_ep(raw: str):
    return {"formatted": format_cep(raw)}


@app.get("/format/data")
async def format_data_ep(raw: str):
    return {"formatted": format_data(raw)}


@app.get("/")
async def index():
    with open("index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


app.mount("/", StaticFiles(directory=".", html=True), name="statics")
