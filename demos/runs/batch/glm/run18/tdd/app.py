import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


class Campo(BaseModel):
    valor: str
    obrigatorio: bool = True


class Solicitacao(BaseModel):
    aba: str
    campos: dict


@app.get("/")
def index():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/style.css")
def style():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


CAMPOS_OPCIONAIS = {"link_evento", "complemento"}


def _vazio(v):
    return v is None or str(v).strip() == ""


def _validar(d):
    erros = []
    faltando = [
        c for c, v in d.items()
        if c not in CAMPOS_OPCIONAIS and _vazio(v)
    ]
    if faltando:
        erros.append("Preencha todos os campos")
    n_usp = str(d.get("n_usp", ""))
    if not _vazio(n_usp) and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    agencia = str(d.get("agencia", ""))
    if not _vazio(agencia) and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = str(d.get("valor", ""))
    if not _vazio(valor) and not valor.isdigit():
        erros.append("Valor solicitado deve ser maior que 0")
    email = str(d.get("email", ""))
    if not _vazio(email) and "@" not in email:
        erros.append("E-mail inválido")
    cpf = str(d.get("cpf", ""))
    if not _vazio(cpf) and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    cep = str(d.get("cep", ""))
    if not _vazio(cep) and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    data = str(d.get("data_nascimento", ""))
    if not _vazio(data) and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    return erros


@app.post("/enviar")
def enviar(s: Solicitacao):
    d = s.campos
    erros = _validar(d)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    if not _cpf_valido(d["cpf"]):
        return JSONResponse({"ok": False, "erros": ["CPF inválido"]})
    if not _data_valida(d["data_nascimento"]):
        return JSONResponse({"ok": False, "erros": ["Data de nascimento inválida"]})
    return JSONResponse({"ok": True, "oficio": _oficio(s.aba, d)})


def _cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    s = sum(d[i] * (10 - i) for i in range(9))
    if (s * 10) % 11 % 10 != d[9]:
        return False
    s = sum(d[i] * (11 - i) for i in range(10))
    return (s * 10) % 11 % 10 == d[10]


def _data_valida(data):
    dia, mes, ano = (int(x) for x in data.split("/"))
    try:
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _formatar(valor):
    centavos = int("".join(c for c in valor if c.isdigit()))
    texto = str(centavos)
    texto = texto.zfill(3)
    reais, cents = texto[:-2], texto[-2:]
    grupos = []
    while len(reais) > 3:
        grupos.insert(0, reais[-3:])
        reais = reais[:-3]
    grupos.insert(0, reais)
    return "R$ " + ".".join(grupos) + "," + cents


def _oficio(aba, d):
    linhas = [
        "Interessada(o): %s - %s" % (d["nome"], d["n_usp"]),
        "E-mail: %s" % d["email"],
    ]
    if aba == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - %s" % d["tipo_auxilio"])
        linhas.append("Programa: %s - %s" % (d["programa"], d["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: %s" % d["programa"])
    linhas.append("")
    linhas.append("A CCP-%s aprovou na data de hoje, a solicitação de auxílio financeiro para a" % d["programa"])
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: %s" % d["nome_evento"])
    linhas.append("Período: %s" % d["periodo"])
    linhas.append("Local: %s - %s - %s" % (d["cidade_evento"], d["estado_evento"], d["pais_evento"]))
    if d.get("link_evento"):
        linhas.append("Link do evento: %s" % d["link_evento"])
    linhas.append("Apresentação de trabalho: %s" % d["apresentacao"])
    linhas.append("Valor solicitado: %s" % _formatar(d["valor"]))
    linhas.append("Detalhamento: %s" % d["detalhamento"])
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append("%s, %s" % (d["logradouro"], d["numero"]))
    if d.get("complemento"):
        linhas.append("Complemento: %s" % d["complemento"])
    linhas.append("CEP: %s" % d["cep"])
    linhas.append("%s, %s - %s" % (d["bairro"], d["cidade"], d["estado"]))
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
