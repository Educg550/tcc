import calendar
import os
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
app.mount("/assets", StaticFiles(directory=os.path.join(BASE, "assets")), name="assets")


@app.get("/")
def raiz():
    return FileResponse(os.path.join(BASE, "index.html"))


@app.get("/style.css")
def estilo():
    return FileResponse(os.path.join(BASE, "style.css"), media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(os.path.join(BASE, "app.js"), media_type="application/javascript")


CAMPOS = [
    "aba", "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "link_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "complemento", "bairro", "cep",
    "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta",
]

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta",
]


def _digito_cpf(digitos, pesos):
    soma = sum(d * p for d, p in zip(digitos, pesos))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11:
        return False
    d1 = _digito_cpf(d[:9], range(10, 1, -1))
    d2 = _digito_cpf(d[:10], range(11, 1, -1))
    return d1 == d[9] and d2 == d[10]


def data_valida(texto):
    dia, mes, ano = (int(p) for p in texto.split("/"))
    if not 1 <= mes <= 12:
        return False
    return 1 <= dia <= calendar.monthrange(ano, mes)[1]


def valor_valido(texto):
    v = texto.strip()
    if v.startswith("R$"):
        v = v[2:].strip()
    v = v.replace(".", "").replace(",", ".")
    try:
        return float(v) > 0
    except ValueError:
        return False


def validar(d, aba):
    erros = []
    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if aba == "alunos" else [])
    if any(not d.get(c, "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = d.get("n_usp", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = d.get("agencia", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = d.get("valor", "").strip()
    if valor and not valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = d.get("email", "").strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = d.get("cpf", "").strip()
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = d.get("cep", "").strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nasc = d.get("data_nascimento", "").strip()
    if nasc:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", nasc):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(nasc):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d, aba):
    programa = d.get("programa", "")
    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = "Programa: " + programa
    else:
        assunto = "Solicitação de Auxílio Financeiro - " + d.get("tipo_auxilio", "")
        linha_programa = "Programa: " + programa + " - " + d.get("nivel", "")

    linhas = [
        "Interessada(o): " + d.get("nome_completo", "") + " - " + d.get("n_usp", ""),
        "E-mail: " + d.get("email", ""),
        "Assunto: " + assunto,
        linha_programa,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + d.get("nome_evento", ""),
        "Período: " + d.get("periodo", ""),
        "Local: " + d.get("cidade_evento", "") + " - " + d.get("estado_evento", "") + " - " + d.get("pais_evento", ""),
    ]
    if d.get("link_evento", "").strip():
        linhas.append("Link do evento: " + d["link_evento"])
    linhas += [
        "Apresentação de trabalho: " + d.get("apresentacao", ""),
        "Valor solicitado: " + d.get("valor", ""),
        "Detalhamento: " + d.get("detalhamento", ""),
        "",
        "Endereço da(o) interessada(o)",
        d.get("logradouro", "") + ", " + d.get("numero", ""),
    ]
    if d.get("complemento", "").strip():
        linhas.append("Complemento: " + d["complemento"])
    linhas += [
        "CEP: " + d.get("cep", ""),
        d.get("bairro", "") + ", " + d.get("cidade_end", "") + " - " + d.get("estado_end", ""),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + d.get("data_nascimento", ""),
        "CPF: " + d.get("cpf", ""),
        "RG / RNM: " + d.get("rg", ""),
        "Banco: " + d.get("banco", ""),
        "Agência: " + d.get("agencia", ""),
        "Conta: " + d.get("conta", ""),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    form = await request.form()
    d = {}
    for campo in CAMPOS:
        valor = form.get(campo)
        d[campo] = valor.strip() if isinstance(valor, str) else ""

    aba = d.get("aba")
    if aba not in ("alunos", "docentes"):
        aba = "alunos"

    erros = validar(d, aba)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": gerar_oficio(d, aba)})
