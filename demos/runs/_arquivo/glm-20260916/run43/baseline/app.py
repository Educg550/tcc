import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

app = FastAPI()

CAMPOS = [
    "nome", "nusp", "programa", "nivel", "tipo_auxilio", "email", "evento",
    "periodo", "cidade_evento", "estado_evento", "pais_evento", "link",
    "valor", "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "complemento", "bairro", "cep", "cidade", "estado", "cpf",
    "rg", "banco", "agencia", "conta",
]


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * (i + 1 - j) for j in range(i))
        if (soma * 10) % 11 % 10 != digitos[i]:
            return False
    return True


def validar(d, tipo):
    obrigatorios = [c for c in CAMPOS if c not in ("link", "complemento")]
    if tipo == "docentes":
        obrigatorios = [c for c in obrigatorios if c not in ("nivel", "tipo_auxilio")]

    erros = []
    if any(not d[c] for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if d["nusp"] and not re.fullmatch(r"[0-9]+", d["nusp"]):
        erros.append("N. USP deve conter apenas números")
    if d["agencia"] and not re.fullmatch(r"[0-9]+", d["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    centavos = re.sub(r"[^0-9]", "", d["valor"])
    if d["valor"] and (not centavos or int(centavos) == 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if d["email"] and ("@" not in d["email"] or not d["email"].split("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", d["cpf"]))
    cep_no_formato = bool(re.fullmatch(r"[0-9]{5}-[0-9]{3}", d["cep"]))
    data_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", d["data_nascimento"]))

    if d["cpf"] and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if d["cep"] and not cep_no_formato:
        erros.append("CEP deve estar no formato 00000-000")
    if d["data_nascimento"] and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if d["cpf"] and cpf_no_formato and not cpf_valido(d["cpf"]):
        erros.append("CPF inválido")
    if d["data_nascimento"] and data_no_formato:
        try:
            datetime.strptime(d["data_nascimento"], "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def moeda(valor):
    digitos = re.sub(r"[^0-9]", "", valor)
    centavos = digitos[-2:].rjust(2, "0")
    reais = re.sub(r"\B(?=(\d{3})+(?!\d))", ".", digitos[:-2] or "0")
    return f"R$ {reais},{centavos}"


def oficio(d, tipo):
    if tipo == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}"
        linha_programa = f"Programa: {d['programa']} - {d['nivel']}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {d['programa']}"

    linhas = [
        f"Interessada(o): {d['nome']} - {d['nusp']}",
        f"E-mail: {d['email']}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{d['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['evento']}",
        f"Período: {d['periodo']}",
        f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}",
    ]
    if d["link"]:
        linhas.append(f"Link do evento: {d['link']}")
    linhas += [
        f"Apresentação de trabalho: {d['apresentacao']}",
        f"Valor solicitado: {moeda(d['valor'])}",
        f"Detalhamento: {d['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d['logradouro']}, {d['numero']}",
    ]
    if d["complemento"]:
        linhas.append(f"Complemento: {d['complemento']}")
    linhas += [
        f"CEP: {d['cep']}",
        f"{d['bairro']}, {d['cidade']} - {d['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d['data_nascimento']}",
        f"CPF: {d['cpf']}",
        f"RG / RNM: {d['rg']}",
        f"Banco: {d['banco']}",
        f"Agência: {d['agencia']}",
        f"Conta: {d['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitacao(request: Request):
    corpo = await request.()
    tipo = "docentes" if corpo.get("tipo") == "docentes" else "alunos"
    d = {campo: str(corpo.get(campo, "")).strip() for campo in CAMPOS}
    erros = validar(d, tipo)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": oficio(d, tipo)}


@app.get("/")
async def index():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
async def estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
async def script():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
