import re
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str = "alunos"
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link: str = ""
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


def _parse_valor(v):
    s = v.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _formatar_valor(v):
    val = _parse_valor(v)
    if val is None:
        return v
    total = round(val * 100)
    reais = total // 100
    cents = total % 100
    milhar = "{:,}".format(reais).replace(",", ".")
    return "R$ {},{:02d}".format(milhar, cents)


def _cpf_valido(cpf):
    d = re.sub(r"\D", "", cpf)
    if len(d) != 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * ((i + 1) - j) for j in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != int(d[i]):
            return False
    return True


def validar(s):
    erros = []
    obrigatorios = [
        s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
        s.detalhamento, s.apresentacao, s.data_nascimento,
        s.logradouro, s.numero, s.bairro, s.cep, s.cidade, s.estado,
        s.cpf, s.rg, s.banco, s.agencia, s.conta,
    ]
    if s.tipo == "alunos":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not str(f).strip() for f in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.nusp.strip() and not re.fullmatch(r"\d+", s.nusp.strip()):
        erros.append("N. USP deve conter apenas n\u00fameros")

    if s.agencia.strip() and not re.fullmatch(r"\d+", s.agencia.strip()):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    if s.valor.strip():
        v = _parse_valor(s.valor)
        if v is None or v <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if s.email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s.email.strip()):
        erros.append("E-mail inv\u00e1lido")

    if s.cpf.strip():
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf.strip()):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(s.cpf):
            erros.append("CPF inv\u00e1lido")

    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    if s.data_nascimento.strip():
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento.strip()):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(s.data_nascimento.strip(), "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inv\u00e1lida")

    return erros


def gerar_oficio(s):
    if s.tipo == "docentes":
        assunto = "Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        programa = s.programa
    else:
        assunto = "Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - {}".format(s.tipo_auxilio)
        programa = "{} - {}".format(s.programa, s.nivel)

    linhas = [
        "Interessada(o): {} - {}".format(s.nome, s.nusp),
        "E-mail: {}".format(s.email),
        "Assunto: {}".format(assunto),
        "Programa: {}".format(programa),
        "",
        "A CCP-{} aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a".format(s.programa),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(s.evento),
        "Per\u00edodo: {}".format(s.periodo),
        "Local: {} - {} - {}".format(s.cidade_evento, s.estado_evento, s.pais_evento),
    ]
    if s.link.strip():
        linhas.append("Link do evento: {}".format(s.link))
    linhas += [
        "Apresenta\u00e7\u00e3o de trabalho: {}".format(s.apresentacao),
        "Valor solicitado: {}".format(_formatar_valor(s.valor)),
        "Detalhamento: {}".format(s.detalhamento),
        "",
        "Endere\u00e7o da(o) interessada(o)",
        "{}, {}".format(s.logradouro, s.numero),
    ]
    if s.complemento.strip():
        linhas.append("Complemento: {}".format(s.complemento))
    linhas += [
        "CEP: {}".format(s.cep),
        "{}, {} - {}".format(s.bairro, s.cidade, s.estado),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(s.data_nascimento),
        "CPF: {}".format(s.cpf),
        "RG / RNM: {}".format(s.rg),
        "Banco: {}".format(s.banco),
        "Ag\u00eancia: {}".format(s.agencia),
        "Conta: {}".format(s.conta),
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    ct = request.headers.get("content-type", "")
    if "application/json" in ct:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)
    s = Solicitacao(**data)
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(s)}


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/index.html")
def index_html():
    return FileResponse("index.html")


@app.get("/style.css")
def style_css():
    return FileResponse("style.css")


@app.get("/app.js")
def app_js():
    return FileResponse("app.js")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
