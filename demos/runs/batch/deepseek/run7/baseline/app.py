import datetime
import os
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

CAMPOS_ALUNOS = [
    "nome", "nusp", "programa", "nivel", "tipo_auxilio", "email", "evento",
    "periodo", "ev_cidade", "ev_estado", "ev_pais", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "end_cidade", "end_estado", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]


def _digitos(t):
    return re.sub(r"\D", "", t or "")


def _valor_numero(t):
    t = t.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(t)
    except ValueError:
        return 0.0


def _cpf_valido(cpf):
    c = [int(x) for x in _digitos(cpf)]
    if len(c) != 11 or len(set(c)) == 1:
        return False
    for i in (9, 10):
        s = sum(c[j] * (i + 1 - j) for j in range(i))
        d = (s * 10) % 11
        if d == 10:
            d = 0
        if d != c[i]:
            return False
    return True


def _data_valida(t):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", t)
    try:
        datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return False
    return True


def validar(d):
    campos = CAMPOS_ALUNOS if d.get("aba") == "alunos" else CAMPOS_DOCENTES
    erros = []

    if any(not (d.get(c) or "").strip() for c in campos):
        erros.append("Preencha todos os campos")

    nusp = (d.get("nusp") or "").strip()
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = (d.get("agencia") or "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = (d.get("valor") or "").strip()
    if valor and _valor_numero(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = (d.get("email") or "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = (d.get("cpf") or "").strip()
    cpf_fmt = False
    if cpf:
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            cpf_fmt = True
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")

    cep = (d.get("cep") or "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = (d.get("data_nascimento") or "").strip()
    data_fmt = False
    if data:
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            data_fmt = True
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_fmt and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_fmt and not _data_valida(data):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d):
    linhas = []
    linhas.append("Interessada(o): %s - %s" % (d["nome"], d["nusp"]))
    linhas.append("E-mail: %s" % d["email"])
    if d.get("aba") == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - %s" % d["tipo_auxilio"])
        linhas.append("Programa: %s - %s" % (d["programa"], d["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: %s" % d["programa"])
    linhas.append("")
    linhas.append(
        "A CCP-%s aprovou na data de hoje, a solicitação de auxílio financeiro para a"
        % d["programa"]
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: %s" % d["evento"])
    linhas.append("Período: %s" % d["periodo"])
    linhas.append(
        "Local: %s - %s - %s" % (d["ev_cidade"], d["ev_estado"], d["ev_pais"])
    )
    link = (d.get("link") or "").strip()
    if link:
        linhas.append("Link do evento: %s" % link)
    linhas.append("Apresentação de trabalho: %s" % d["apresentacao"])
    linhas.append("Valor solicitado: %s" % d["valor"])
    linhas.append("Detalhamento: %s" % d["detalhamento"])
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append("%s, %s" % (d["logradouro"], d["numero"]))
    complemento = (d.get("complemento") or "").strip()
    if complemento:
        linhas.append("Complemento: %s" % complemento)
    linhas.append("CEP: %s" % d["cep"])
    linhas.append("%s, %s - %s" % (d["bairro"], d["end_cidade"], d["end_estado"]))
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: %s" % d["data_nascimento"])
    linhas.append("CPF: %s" % d["cpf"])
    linhas.append("RG / RNM: %s" % d["rg"])
    linhas.append("Banco: %s" % d["banco"])
    linhas.append("Agência: %s" % d["agencia"])
    linhas.append("Conta: %s" % d["conta"])
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    d = await request.json()
    erros = validar(d)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(d)}


@app.get("/")
def raiz():
    return FileResponse(os.path.join(BASE, "index.html"))


@app.get("/style.css")
def estilo():
    return FileResponse(os.path.join(BASE, "style.css"))


@app.get("/app.js")
def script():
    return FileResponse(os.path.join(BASE, "app.js"))


app.mount("/assets", StaticFiles(directory=os.path.join(BASE, "assets")), name="assets")
