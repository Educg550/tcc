import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")

CAMPOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "link_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "complemento", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
OPCIONAIS = ("nivel", "tipo_auxilio", "link_evento", "complemento")


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


def cpf_valido(digitos):
    if len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * peso for d, peso in zip(digitos, range(tamanho + 1, 1, -1)))
        resto = soma % 11
        if int(digitos[tamanho]) != (0 if resto < 2 else 11 - resto):
            return False
    return True


def moeda(digitos):
    inteiro, centavos = f"{int(digitos) / 100:.2f}".split(".")
    return "R$ " + re.sub(r"\B(?=(\d{3})+(?!\d))", ".", inteiro) + "," + centavos


def validar(d, aba):
    obrigatorios = [campo for campo in CAMPOS if campo not in OPCIONAIS]
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    erros = []

    if any(not d[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if d["n_usp"] and not re.fullmatch(r"[0-9]+", d["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if d["agencia"] and not re.fullmatch(r"[0-9]+", d["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    if d["valor"]:
        digitos = re.sub(r"\D", "", d["valor"])
        if int(digitos or 0) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
        else:
            d["valor"] = moeda(digitos)

    if d["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", d["email"]):
        erros.append("E-mail inválido")

    if d["cpf"]:
        digitos = re.sub(r"\D", "", d["cpf"])
        if re.fullmatch(r"[0-9]{11}", d["cpf"]):
            d["cpf"] = f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
        elif not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", d["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
            d["cpf"] = ""
        if d["cpf"] and not cpf_valido(digitos):
            erros.append("CPF inválido")

    if d["cep"]:
        digitos = re.sub(r"\D", "", d["cep"])
        if re.fullmatch(r"[0-9]{8}", d["cep"]):
            d["cep"] = f"{digitos[:5]}-{digitos[5:]}"
        elif not re.fullmatch(r"[0-9]{5}-[0-9]{3}", d["cep"]):
            erros.append("CEP deve estar no formato 00000-000")
            d["cep"] = ""

    if d["data_nascimento"]:
        digitos = re.sub(r"\D", "", d["data_nascimento"])
        if re.fullmatch(r"[0-9]{8}", d["data_nascimento"]):
            d["data_nascimento"] = f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"
        elif not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", d["data_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
            d["data_nascimento"] = ""
        if d["data_nascimento"]:
            dia, mes, ano = d["data_nascimento"].split("/")
            try:
                date(int(ano), int(mes), int(dia))
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(d, aba):
    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}"
        programa = f"{d['programa']} - {d['nivel']}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = d["programa"]

    linhas = [
        f"Interessada(o): {d['nome']} - {d['n_usp']}",
        f"E-mail: {d['email']}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{d['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['evento']}",
        f"Período: {d['periodo']}",
        f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}",
    ]
    if d["link_evento"]:
        linhas.append(f"Link do evento: {d['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {d['apresentacao']}",
        f"Valor solicitado: {d['valor']}",
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


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    try:
        dados = await request.json()
    except Exception:
        dados = dict(await request.form())
    if not isinstance(dados, dict):
        dados = {}

    aba = "docentes" if "doc" in str(dados.get("aba", "")).lower() else "alunos"
    d = {campo: str(dados.get(campo) or "").strip() for campo in CAMPOS}
    erros = validar(d, aba)
    if erros:
        return {"valido": False, "erros": erros, "oficio": ""}
    return {"valido": True, "erros": [], "oficio": montar_oficio(d, aba)}
