import calendar
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI()

OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor", "detalhamento", "apresentacao", "nascimento",
    "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]


def v(dados, chave):
    return str(dados.get(chave, "") or "").strip()


def cpf_valido(cpf):
    numeros = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(set(numeros)) == 1:
        return False
    for i in (9, 10):
        soma = sum(numeros[j] * ((i + 1) - j) for j in range(i))
        if (soma * 10) % 11 % 10 != numeros[i]:
            return False
    return True


def validar(dados, aba):
    erros = []
    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if aba == "aluno" else [])
    if any(not v(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = v(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas n\u00fameros")

    agencia = v(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    valor = v(dados, "valor")
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = v(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inv\u00e1lido")

    cpf = v(dados, "cpf")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inv\u00e1lido")

    cep = v(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = v(dados, "nascimento")
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(p) for p in nascimento.split("/"))
            if not (1 <= mes <= 12) or not (1 <= dia <= calendar.monthrange(ano, mes)[1]):
                erros.append("Data de nascimento inv\u00e1lida")

    return erros


def gerar_oficio(dados, aba):
    programa = v(dados, "programa")
    linhas = [
        "Interessada(o): {} - {}".format(v(dados, "nome"), v(dados, "n_usp")),
        "E-mail: {}".format(v(dados, "email")),
    ]
    if aba == "aluno":
        linhas.append("Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - {}".format(v(dados, "tipo_auxilio")))
        linhas.append("Programa: {} - {}".format(programa, v(dados, "nivel")))
    else:
        linhas.append("Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(programa))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a".format(programa),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(v(dados, "evento")),
        "Per\u00edodo: {}".format(v(dados, "periodo")),
        "Local: {} - {} - {}".format(v(dados, "cidade_evento"), v(dados, "estado_evento"), v(dados, "pais_evento")),
    ]

    if v(dados, "link_evento"):
        linhas.append("Link do evento: {}".format(v(dados, "link_evento")))

    linhas += [
        "Apresenta\u00e7\u00e3o de trabalho: {}".format(v(dados, "apresentacao")),
        "Valor solicitado: {}".format(v(dados, "valor")),
        "Detalhamento: {}".format(v(dados, "detalhamento")),
        "",
        "Endere\u00e7o da(o) interessada(o)",
        "{}, {}".format(v(dados, "logradouro"), v(dados, "numero")),
    ]

    if v(dados, "complemento"):
        linhas.append("Complemento: {}".format(v(dados, "complemento")))

    linhas += [
        "CEP: {}".format(v(dados, "cep")),
        "{}, {} - {}".format(v(dados, "bairro"), v(dados, "cidade"), v(dados, "estado")),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(v(dados, "nascimento")),
        "CPF: {}".format(v(dados, "cpf")),
        "RG / RNM: {}".format(v(dados, "rg")),
        "Banco: {}".format(v(dados, "banco")),
        "Ag\u00eancia: {}".format(v(dados, "agencia")),
        "Conta: {}".format(v(dados, "conta")),
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)


def responder(dados, aba):
    erros = validar(dados, aba)
    if erros:
        return JSONResponse({"valido": False, "mensagens": erros, "titulo": "", "oficio": ""})
    return JSONResponse(
        {
            "valido": True,
            "mensagens": [],
            "titulo": "Solicita\u00e7\u00e3o registrada",
            "oficio": gerar_oficio(dados, aba),
        }
    )


@app.post("/api/solicitacao/aluno")
async def solicitacao_aluno(request: Request):
    return responder(await request.json(), "aluno")


@app.post("/api/solicitacao/docente")
async def solicitacao_docente(request: Request):
    return responder(await request.json(), "docente")


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
