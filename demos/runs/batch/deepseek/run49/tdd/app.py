import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


CAMPOS_OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]


def _texto(dados, chave):
    return str(dados.get(chave, "") or "").strip()


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    for i in (9, 10):
        soma = sum(digitos[j] * ((i + 1) - j) for j in range(i))
        verificador = (soma * 10) % 11
        if verificador == 10:
            verificador = 0
        if verificador != digitos[i]:
            return False
    return True


def validar(dados):
    erros = []
    eh_aluno = "nivel" in dados or "tipo_auxilio" in dados

    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if eh_aluno:
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not _texto(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas n\u00fameros")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    valor = _texto(dados, "valor")
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inv\u00e1lido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inv\u00e1lido")

    cep = _texto(dados, "cep")
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _texto(dados, "data_nascimento")
    if nascimento:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(p) for p in nascimento.split("/"))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inv\u00e1lida")

    return erros


def formatar_valor(valor):
    digitos = re.sub(r"\D", "", str(valor))
    total = int(digitos or 0)
    reais, centavos = divmod(total, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def gerar_oficio(dados):
    eh_aluno = "nivel" in dados or "tipo_auxilio" in dados

    if eh_aluno:
        assunto = "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - " + _texto(dados, "tipo_auxilio")
        programa = "Programa: " + _texto(dados, "programa") + " - " + _texto(dados, "nivel")
    else:
        assunto = "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        programa = "Programa: " + _texto(dados, "programa")

    linhas = [
        "Interessada(o): " + _texto(dados, "nome_completo") + " - " + _texto(dados, "n_usp"),
        "E-mail: " + _texto(dados, "email"),
        assunto,
        programa,
        "",
        "A CCP-" + _texto(dados, "programa")
        + " aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + _texto(dados, "evento"),
        "Per\u00edodo: " + _texto(dados, "periodo"),
        "Local: "
        + _texto(dados, "cidade_evento")
        + " - "
        + _texto(dados, "estado_evento")
        + " - "
        + _texto(dados, "pais_evento"),
    ]
    if _texto(dados, "link_evento"):
        linhas.append("Link do evento: " + _texto(dados, "link_evento"))
    linhas += [
        "Apresenta\u00e7\u00e3o de trabalho: " + _texto(dados, "apresentacao"),
        "Valor solicitado: " + formatar_valor(_texto(dados, "valor")),
        "Detalhamento: " + _texto(dados, "detalhamento"),
        "",
        "Endere\u00e7o da(o) interessada(o)",
        _texto(dados, "logradouro") + ", " + _texto(dados, "numero"),
    ]
    if _texto(dados, "complemento"):
        linhas.append("Complemento: " + _texto(dados, "complemento"))
    linhas += [
        "CEP: " + _texto(dados, "cep"),
        _texto(dados, "bairro") + ", " + _texto(dados, "cidade") + " - " + _texto(dados, "estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + _texto(dados, "data_nascimento"),
        "CPF: " + _texto(dados, "cpf"),
        "RG / RNM: " + _texto(dados, "rg"),
        "Banco: " + _texto(dados, "banco"),
        "Ag\u00eancia: " + _texto(dados, "agencia"),
        "Conta: " + _texto(dados, "conta"),
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/style.css")
def estilos():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


@app.post("/solicitacao")
def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"erros": [], "oficio": gerar_oficio(dados)}
