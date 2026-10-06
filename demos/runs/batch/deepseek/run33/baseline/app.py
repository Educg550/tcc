import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE = Path(__file__).resolve().parent

CAMPOS_ALUNOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]


def _val(d, k):
    v = d.get(k, "")
    return "" if v is None else str(v).strip()


def parse_valor(v):
    v = v.replace("R$", "").strip()
    if not v:
        return None
    if "," in v:
        v = v.replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def cpf_valido(cpf):
    d = re.sub(r"[^0-9]", "", cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * ((i + 1) - j) for j in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != int(d[i]):
            return False
    return True


def gerar_oficio(d, tipo):
    g = lambda k: _val(d, k)
    link = g("link_evento")
    comp = g("complemento")
    if tipo == "docentes":
        assunto = "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        programa = "Programa: " + g("programa")
    else:
        assunto = "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - " + g("tipo_auxilio")
        programa = "Programa: " + g("programa") + " - " + g("nivel")

    linhas = [
        "Interessada(o): " + g("nome") + " - " + g("n_usp"),
        "E-mail: " + g("email"),
        assunto,
        programa,
        "",
        "A CCP-" + g("programa") + " aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + g("evento"),
        "Per\u00edodo: " + g("periodo"),
        "Local: " + g("cidade_evento") + " - " + g("estado_evento") + " - " + g("pais_evento"),
    ]
    if link:
        linhas.append("Link do evento: " + link)
    linhas.append("Apresenta\u00e7\u00e3o de trabalho: " + g("apresentacao"))
    linhas.append("Valor solicitado: " + g("valor"))
    linhas.append("Detalhamento: " + g("detalhamento"))
    linhas.append("")
    linhas.append("Endere\u00e7o da(o) interessada(o)")
    linhas.append(g("logradouro") + ", " + g("numero"))
    if comp:
        linhas.append("Complemento: " + comp)
    linhas.append("CEP: " + g("cep"))
    linhas.append(g("bairro") + ", " + g("cidade") + " - " + g("estado"))
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: " + g("data_nascimento"))
    linhas.append("CPF: " + g("cpf"))
    linhas.append("RG / RNM: " + g("rg"))
    linhas.append("Banco: " + g("banco"))
    linhas.append("Ag\u00eancia: " + g("agencia"))
    linhas.append("Conta: " + g("conta"))
    linhas.append("")
    linhas.append("Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    d = await request.json()
    tipo = d.get("tipo") or "alunos"
    if tipo == "docentes":
        obrigatorios = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]
    else:
        obrigatorios = CAMPOS_ALUNOS

    erros = []

    if any(not _val(d, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _val(d, "n_usp")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas n\u00fameros")

    agencia = _val(d, "agencia")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    valor = _val(d, "valor")
    if valor:
        pv = parse_valor(valor)
        if pv is None or pv <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _val(d, "email")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inv\u00e1lido")

    cpf = _val(d, "cpf")
    cpf_formato_ok = True
    if cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
            cpf_formato_ok = False

    cep = _val(d, "cep")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    dn = _val(d, "data_nascimento")
    dn_formato_ok = True
    if dn:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", dn):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
            dn_formato_ok = False

    if cpf and cpf_formato_ok and not cpf_valido(cpf):
        erros.append("CPF inv\u00e1lido")

    if dn and dn_formato_ok:
        try:
            dia, mes, ano = (int(x) for x in dn.split("/"))
            date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inv\u00e1lida")

    if erros:
        return {"erros": erros}

    return {"oficio": gerar_oficio(d, tipo)}


app.mount("/", StaticFiles(directory=str(BASE), html=True), name="static")
