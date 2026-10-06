import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

CAMPOS = [
    "nome", "nusps", "programa", "nivel", "tipo_auxilio", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "link_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "complemento", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
OPCIONAIS = {
    "alunos": {"link_evento", "complemento"},
    "docentes": {"link_evento", "complemento", "nivel", "tipo_auxilio"},
}
CPF_FORMATO = re.compile(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
DATA_FORMATO = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")


class Solicitacao(BaseModel):
    aba: str = "alunos"
    nome: str = ""
    nusps: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
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


app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


@app.post("/api/solicitacao")
def registrar(solicitacao: Solicitacao):
    dados = {campo: getattr(solicitacao, campo).strip() for campo in CAMPOS}
    erros = validar(solicitacao.aba, dados)
    if erros:
        return {"erros": erros}
    return {"oficio": redigir(solicitacao.aba, dados)}


def validar(aba, d):
    erros = []
    if any(not d[campo] for campo in CAMPOS if campo not in OPCIONAIS[aba]):
        erros.append("Preencha todos os campos")
    if d["nusps"] and not re.fullmatch(r"[0-9]+", d["nusps"]):
        erros.append("N. USP deve conter apenas números")
    if d["agencia"] and not re.fullmatch(r"[0-9]+", d["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if d["valor"]:
        centavos = re.sub(r"[^0-9]", "", d["valor"])
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if d["email"] and ("@" not in d["email"] or not d["email"].split("@", 1)[1]):
        erros.append("E-mail inválido")
    cpf_formatado = bool(d["cpf"]) and bool(CPF_FORMATO.fullmatch(d["cpf"]))
    if d["cpf"] and not cpf_formatado:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if d["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", d["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    data_formatada = bool(d["data_nascimento"]) and bool(DATA_FORMATO.fullmatch(d["data_nascimento"]))
    if d["data_nascimento"] and not data_formatada:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_formatado and not digitos_verificadores_conferem(d["cpf"]):
        erros.append("CPF inválido")
    if data_formatada:
        try:
            datetime.strptime(d["data_nascimento"], "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def digitos_verificadores_conferem(cpf):
    n = [int(c) for c in cpf if c.isdigit()]
    dv1 = sum(n[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
    dv2 = sum(n[i] * (11 - i) for i in range(10)) * 10 % 11 % 10
    return [dv1, dv2] == n[9:11]


def redigir(aba, d):
    linhas = [
        f"Interessada(o): {d['nome']} - {d['nusps']}",
        f"E-mail: {d['email']}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}")
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d['programa']}")
    linhas += [
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
        f"Valor solicitado: {formatar_moeda(d['valor'])}",
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


def formatar_moeda(valor):
    centavos = int(re.sub(r"[^0-9]", "", valor))
    inteiro, centavos = divmod(centavos, 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{centavos:02d}"


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css", include_in_schema=False)
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
