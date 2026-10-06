"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS = [
    "nome", "nusp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentar",
    "data_nasc", "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]

RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_DATA = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11:
        return False
    for i, peso in ((10, 11), (11, 10)):
        soma = sum(digitos[j] * (peso - j) for j in range(i - 1))
        if (soma * 10) % 11 % 10 != digitos[i]:
            return False
    return True


def _data_valida(data):
    m = RE_DATA.match(data)
    if not m:
        return False
    dia, mes, _ = (int(x) for x in m.groups())
    if not 1 <= mes <= 12:
        return False
    ultimo = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
    return 1 <= dia <= ultimo


def _valor_reais(valor):
    digitos = re.sub(r"\D", "", valor)
    return bool(digitos) and int(digitos) > 0


def _validar(d):
    erros = []
    faltando = not d.get("nome", "") or not all(d.get(c, "") for c in CAMPOS)
    if faltando:
        erros.append("Preencha todos os campos")
    if d.get("nusp", "") and not d["nusp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if d.get("agencia", "") and not d["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    if d.get("valor", "") and not _valor_reais(d["valor"]):
        erros.append("Valor solicitado deve ser maior que 0")
    if d.get("email", ""):
        local, _, dominio = d["email"].partition("@")
        if not local or not dominio:
            erros.append("E-mail inválido")
    if d.get("cpf", ""):
        if not RE_CPF.match(d["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(d["cpf"]):
            erros.append("CPF inválido")
    if d.get("cep", "") and not RE_CEP.match(d["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if d.get("data_nasc", ""):
        if not RE_DATA.match(d["data_nasc"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(d["data_nasc"]):
            erros.append("Data de nascimento inválida")
    return erros


def _oficio(d, aba):
    assunto = d.get("tipo_auxilio", "") if aba == "alunos" else "Verba do programa"
    programa = d.get("programa", "")
    nivel = d.get("nivel", "")
    linha_programa = f"Programa: {programa} - {nivel}" if aba == "alunos" else f"Programa: {programa}"
    linhas = [
        f"Interessada(o): {d.get('nome', '')} - {d.get('nusp', '')}",
        f"E-mail: {d.get('email', '')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.get('evento', '')}",
        f"Período: {d.get('periodo', '')}",
        f"Local: {d.get('cidade_evento', '')} - {d.get('estado_evento', '')} - {d.get('pais_evento', '')}",
    ]
    if d.get("link", ""):
        linhas.append(f"Link do evento: {d['link']}")
    linhas += [
        f"Apresentação de trabalho: {d.get('apresentar', '')}",
        f"Valor solicitado: {d.get('valor', '')}",
        f"Detalhamento: {d.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.get('logradouro', '')}, {d.get('numero', '')}",
    ]
    if d.get("complemento", ""):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas += [
        f"CEP: {d.get('cep', '')}",
        f"{d.get('bairro', '')}, {d.get('cidade', '')} - {d.get('estado', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.get('data_nasc', '')}",
        f"CPF: {d.get('cpf', '')}",
        f"RG / RNM: {d.get('rg', '')}",
        f"Banco: {d.get('banco', '')}",
        f"Agência: {d.get('agencia', '')}",
        f"Conta: {d.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/alunos")
async def alunos(request: Request):
    d = await request.json()
    erros = _validar(d)
    if erros:
        return {"errors": erros}
    return {"oficio": _oficio(d, "alunos")}


@app.post("/docentes")
async def docentes(request: Request):
    d = await request.json()
    erros = _validar(d)
    if erros:
        return {"errors": erros}
    return {"oficio": _oficio(d, "docentes")}


@app.get("/")
async def index():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory="."), name="static")
