import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def raiz():
    return FileResponse("index.html", media_type="text/html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse("app.js", media_type="application/javascript")


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")


def _texto(d, chave):
    return str(d.get(chave, "") or "").strip()


def valor_valido(v):
    s = re.sub(r"[^\d,]", "", v).replace(",", ".")
    try:
        return float(s) > 0
    except ValueError:
        return False


def cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11 or len(set(nums)) == 1:
        return False
    s = sum(nums[i] * (10 - i) for i in range(9))
    d1 = 11 - (s % 11)
    if d1 >= 10:
        d1 = 0
    s = sum(nums[i] * (11 - i) for i in range(10))
    d2 = 11 - (s % 11)
    if d2 >= 10:
        d2 = 0
    return d1 == nums[9] and d2 == nums[10]


def data_valida(data_nasc):
    try:
        dia, mes, ano = (int(p) for p in data_nasc.split("/"))
        date(ano, mes, dia)
        return True
    except (ValueError, TypeError):
        return False


def validar(d):
    erros = []
    obrig = list(OBRIGATORIOS)
    if d.get("aba") == "alunos":
        obrig += ["nivel", "tipo_auxilio"]
    if any(not _texto(d, k) for k in obrig):
        erros.append("Preencha todos os campos")

    n_usp = _texto(d, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(d, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(d, "valor")
    if valor and not valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(d, "email")
    if email and not RE_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")

    cpf = _texto(d, "cpf")
    if cpf:
        if not RE_CPF.fullmatch(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(d, "cep")
    if cep and not RE_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_nasc = _texto(d, "data_nascimento")
    if data_nasc:
        if not RE_DATA.fullmatch(data_nasc):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(data_nasc):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d):
    if d.get("aba") == "alunos":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + _texto(d, "tipo_auxilio")
        programa = "Programa: " + _texto(d, "programa") + " - " + _texto(d, "nivel")
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + _texto(d, "programa")

    linhas = [
        "Interessada(o): {} - {}".format(_texto(d, "nome"), _texto(d, "n_usp")),
        "E-mail: {}".format(_texto(d, "email")),
        assunto,
        programa,
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(_texto(d, "programa")),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(_texto(d, "nome_evento")),
        "Período: {}".format(_texto(d, "periodo")),
        "Local: {} - {} - {}".format(_texto(d, "cidade_evento"), _texto(d, "estado_evento"), _texto(d, "pais_evento")),
    ]
    if _texto(d, "link_evento"):
        linhas.append("Link do evento: {}".format(_texto(d, "link_evento")))
    linhas += [
        "Apresentação de trabalho: {}".format(_texto(d, "apresentacao")),
        "Valor solicitado: {}".format(_texto(d, "valor")),
        "Detalhamento: {}".format(_texto(d, "detalhamento")),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(_texto(d, "logradouro"), _texto(d, "numero")),
    ]
    if _texto(d, "complemento"):
        linhas.append("Complemento: {}".format(_texto(d, "complemento")))
    linhas += [
        "CEP: {}".format(_texto(d, "cep")),
        "{}, {} - {}".format(_texto(d, "bairro"), _texto(d, "cidade"), _texto(d, "estado")),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(_texto(d, "data_nascimento")),
        "CPF: {}".format(_texto(d, "cpf")),
        "RG / RNM: {}".format(_texto(d, "rg")),
        "Banco: {}".format(_texto(d, "banco")),
        "Agência: {}".format(_texto(d, "agencia")),
        "Conta: {}".format(_texto(d, "conta")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(dados)}
