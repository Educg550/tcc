import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


CAMPOS_COMUNS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

FORMATO_CPF = "[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}"
FORMATO_CEP = "[0-9]{5}-[0-9]{3}"
FORMATO_DATA = "[0-9]{2}/[0-9]{2}/[0-9]{4}"


def so_digitos(texto):
    return bool(re.fullmatch("[0-9]+", texto))


def cpf_conferido(cpf):
    digitos = [int(c) for c in re.sub("[^0-9]", "", cpf)]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        verificador = (soma * 10) % 11
        if verificador == 10:
            verificador = 0
        if verificador != digitos[posicao]:
            return False
    return True


def data_existe(valor):
    dia, mes, ano = (int(parte) for parte in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formata_valor(centavos):
    reais = centavos // 100
    resto = centavos % 100
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def gera_oficio(campo, aba, centavos):
    linhas = [
        "Interessada(o): " + campo("nome") + " - " + campo("n_usp"),
        "E-mail: " + campo("email"),
    ]
    if aba == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - " + campo("tipo_auxilio"))
        linhas.append("Programa: " + campo("programa") + " - " + campo("nivel"))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: " + campo("programa"))
    linhas += [
        "",
        "A CCP-" + campo("programa") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + campo("evento"),
        "Período: " + campo("periodo"),
        "Local: " + campo("cidade_evento") + " - " + campo("estado_evento") + " - " + campo("pais_evento"),
    ]
    if campo("link_evento"):
        linhas.append("Link do evento: " + campo("link_evento"))
    linhas += [
        "Apresentação de trabalho: " + campo("apresentacao"),
        "Valor solicitado: " + formata_valor(centavos),
        "Detalhamento: " + campo("detalhamento"),
        "",
        "Endereço da(o) interessada(o)",
        campo("logradouro") + ", " + campo("numero"),
    ]
    if campo("complemento"):
        linhas.append("Complemento: " + campo("complemento"))
    linhas += [
        "CEP: " + campo("cep"),
        campo("bairro") + ", " + campo("cidade") + " - " + campo("estado"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + campo("nascimento"),
        "CPF: " + campo("cpf"),
        "RG / RNM: " + campo("rg"),
        "Banco: " + campo("banco"),
        "Agência: " + campo("agencia"),
        "Conta: " + campo("conta"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(payload: dict):
    aba = payload.get("aba")

    def campo(nome):
        return str(payload.get(nome) or "").strip()

    obrigatorios = list(CAMPOS_COMUNS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not campo(nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campo("n_usp")
    if n_usp and not so_digitos(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = campo("agencia")
    if agencia and not so_digitos(agencia):
        erros.append("Número da agência deve conter apenas números")

    centavos = None
    valor = campo("valor")
    if valor:
        digitos = re.sub("[^0-9]", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
        else:
            centavos = int(digitos)

    email = campo("email")
    if email and not re.fullmatch("[^@ ]+@[^@ ]+[.][^@ ]+", email):
        erros.append("E-mail inválido")

    cpf = campo("cpf")
    cpf_formato_ok = bool(re.fullmatch(FORMATO_CPF, cpf)) if cpf else False
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = campo("cep")
    if cep and not re.fullmatch(FORMATO_CEP, cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campo("nascimento")
    nascimento_formato_ok = bool(re.fullmatch(FORMATO_DATA, nascimento)) if nascimento else False
    if nascimento and not nascimento_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato_ok and not cpf_conferido(cpf):
        erros.append("CPF inválido")

    if nascimento_formato_ok and not data_existe(nascimento):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"erros": erros}

    return {"oficio": gera_oficio(campo, aba, centavos)}
