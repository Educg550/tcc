import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email",
    "evento_nome", "evento_periodo", "evento_cidade", "evento_estado", "evento_pais",
    "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_ALUNOS = ["nivel", "tipo_auxilio"]


def _cpf_valido(cpf: str) -> bool:
    d = re.sub(r"\D", "", cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(d[j]) * (i + 1 - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(d[i]):
            return False
    return True


def _data_valida(valor: str) -> bool:
    try:
        datetime.strptime(valor, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validar(d: dict, tipo: str):
    erros = []
    campos = CAMPOS_OBRIGATORIOS + (CAMPOS_ALUNOS if tipo == "alunos" else [])
    if any(not str(d.get(c, "")).strip() for c in campos):
        erros.append("Preencha todos os campos")

    n_usp = str(d.get("n_usp", "")).strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(d.get("agencia", "")).strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(d.get("valor", "")).strip()
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = str(d.get("email", "")).strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = str(d.get("cpf", "")).strip()
    if cpf and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = str(d.get("cep", "")).strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_nasc = str(d.get("data_nascimento", "")).strip()
    if data_nasc and not re.match(r"^\d{2}/\d{2}/\d{4}$", data_nasc):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data_nasc and not _data_valida(data_nasc):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d: dict, tipo: str) -> str:
    if tipo == "alunos":
        assunto = str(d.get("tipo_auxilio", "")).strip()
        linha_programa = f"Programa: {d.get('programa', '')} - {d.get('nivel', '')}"
    else:
        assunto = "Verba do programa"
        linha_programa = f"Programa: {d.get('programa', '')}"

    linhas = [
        f"Interessada(o): {d.get('nome', '')} - {d.get('n_usp', '')}",
        f"E-mail: {d.get('email', '')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{d.get('programa', '')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.get('evento_nome', '')}",
        f"Período: {d.get('evento_periodo', '')}",
        f"Local: {d.get('evento_cidade', '')} - {d.get('evento_estado', '')} - {d.get('evento_pais', '')}",
    ]

    link = str(d.get("evento_link", "")).strip()
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {d.get('apresentacao', '')}",
        f"Valor solicitado: {d.get('valor', '')}",
        f"Detalhamento: {d.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.get('logradouro', '')}, {d.get('numero', '')}",
    ]

    complemento = str(d.get("complemento", "")).strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {d.get('cep', '')}",
        f"{d.get('bairro', '')}, {d.get('cidade', '')} - {d.get('estado', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.get('data_nascimento', '')}",
        f"CPF: {d.get('cpf', '')}",
        f"RG / RNM: {d.get('rg', '')}",
        f"Banco: {d.get('banco', '')}",
        f"Agência: {d.get('agencia', '')}",
        f"Conta: {d.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


@app.post("/api/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    tipo = dados.get("tipo", "alunos")
    erros = validar(dados, tipo)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"oficio": gerar_oficio(dados, tipo)})
