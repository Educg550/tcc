import re
from pathlib import Path
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()
BASE = Path(__file__).resolve().parent


def cpf_valido(texto):
    digitos = re.sub(r"\D", "", texto)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        total = sum(int(digitos[j]) * ((i + 1) - (j + 1)) for j in range(i))
        resto = (total * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def data_valida(texto):
    dia, mes, ano = texto.split("/")
    if len(ano) != 4:
        return False
    try:
        date(int(ano), int(mes), int(dia))
    except ValueError:
        return False
    return True


def email_valido(texto):
    local, _, dominio = texto.rpartition("@")
    return bool(local) and bool(dominio) and "." in dominio


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.post("/api/solicitacao")
async def solicitacao(corpo: dict):
    aba = corpo.get("aba", "ALUNOS")
    d = corpo.get("dados", {})

    def valor(campo):
        return (d.get(campo) or "").strip()

    obrigatorios = [
        "nome", "nusp", "programa", "email", "evento_nome", "evento_periodo",
        "evento_cidade", "evento_estado", "evento_pais", "valor", "detalhamento",
        "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba == "ALUNOS":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not valor(c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if valor("nusp") and not valor("nusp").isdigit():
        erros.append("N. USP deve conter apenas números")
    if valor("agencia") and not valor("agencia").isdigit():
        erros.append("Número da agência deve conter apenas números")

    digitos_valor = re.sub(r"\D", "", valor("valor"))
    if valor("valor") and not (digitos_valor.isdigit() and int(digitos_valor) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if valor("email") and not email_valido(valor("email")):
        erros.append("E-mail inválido")
    if valor("cpf"):
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", valor("cpf")):
            if not cpf_valido(valor("cpf")):
                erros.append("CPF inválido")
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")
    if valor("cep") and not re.fullmatch(r"\d{5}-\d{3}", valor("cep")):
        erros.append("CEP deve estar no formato 00000-000")
    if valor("nascimento"):
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", valor("nascimento")):
            if not data_valida(valor("nascimento")):
                erros.append("Data de nascimento inválida")
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if erros:
        return JSONResponse({"ok": False, "erros": erros}, status_code=400)

    valor_formatado = "R$ " + "{:.2f}".format(int(digitos_valor) / 100).replace(",", "@").replace(".", ",").replace("@", ".")
    import locale

    linhas = [
        "Interessada(o): {} - {}".format(valor("nome"), valor("nusp")),
        "E-mail: {}".format(valor("email")),
        "Assunto: Solicitação de Auxílio Financeiro - {}".format(valor("tipo_auxilio") if aba == "ALUNOS" else "Verba do programa"),
        "Programa: {} - {}".format(valor("programa"), valor("nivel")) if aba == "ALUNOS" else "Programa: {}".format(valor("programa")),
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(valor("programa")),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(valor("evento_nome")),
        "Período: {}".format(valor("evento_periodo")),
        "Local: {} - {} - {}".format(valor("evento_cidade"), valor("evento_estado"), valor("evento_pais")),
    ]
    if valor("evento_link"):
        linhas.append("Link do evento: {}".format(valor("evento_link")))
    linhas += [
        "Apresentação de trabalho: {}".format(valor("apresentacao")),
        "Valor solicitado: {}".format(valor_formatado),
        "Detalhamento: {}".format(valor("detalhamento")),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(valor("logradouro"), valor("numero")),
    ]
    if valor("complemento"):
        linhas.append("Complemento: {}".format(valor("complemento")))
    linhas += [
        "CEP: {}".format(valor("cep")),
        "{}, {} - {}".format(valor("bairro"), valor("cidade"), valor("estado")),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(valor("nascimento")),
        "CPF: {}".format(valor("cpf")),
        "RG / RNM: {}".format(valor("rg")),
        "Banco: {}".format(valor("banco")),
        "Agência: {}".format(valor("agencia")),
        "Conta: {}".format(valor("conta")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return {"ok": True, "oficio": "\n".join(linhas)}


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
