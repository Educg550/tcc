import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


# --------------------------------------------------------------------------
# Validação
# --------------------------------------------------------------------------

CAMPOS_OBRIGATORIOS = [
    "nome",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
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

RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _texto(valor) -> str:
    return str(valor if valor is not None else "").strip()


def _apenas_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def valor_valido(texto: str) -> bool:
    digitos = _apenas_digitos(texto)
    return bool(digitos) and int(digitos) > 0


def email_valido(texto: str) -> bool:
    return RE_EMAIL.fullmatch(texto) is not None


def cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in _apenas_digitos(cpf)]
    if len(digitos) != 11:
        return False
    for i in range(9, 11):
        soma = sum(digitos[j] * ((i + 1) - j) for j in range(i))
        verificador = (soma * 10) % 11 % 10
        if verificador != digitos[i]:
            return False
    return True


def data_valida(texto: str) -> bool:
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(aba: str, dados: dict) -> list:
    erros = []

    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios.append("nivel")
        obrigatorios.append("tipo_auxilio")

    if any(not _texto(dados.get(campo)) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados.get("n_usp"))
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados.get("agencia"))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados.get("valor"))
    if valor and not valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados.get("email"))
    if email and not email_valido(email):
        erros.append("E-mail inválido")

    cpf = _texto(dados.get("cpf"))
    cpf_formato_ok = bool(cpf) and RE_CPF.fullmatch(cpf) is not None
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = _texto(dados.get("cep"))
    if cep and not RE_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_nascimento = _texto(dados.get("data_nascimento"))
    data_formato_ok = bool(data_nascimento) and RE_DATA.fullmatch(data_nascimento) is not None
    if data_nascimento and not data_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato_ok and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_formato_ok and not data_valida(data_nascimento):
        erros.append("Data de nascimento inválida")

    return erros


# --------------------------------------------------------------------------
# Ofício
# --------------------------------------------------------------------------


def formatar_valor(texto: str) -> str:
    digitos = _apenas_digitos(texto)
    if not digitos:
        return ""
    inteiro, centavos = divmod(int(digitos), 100)
    return "R$ " + f"{inteiro:,}".replace(",", ".") + f",{centavos:02d}"


def gerar_oficio(aba: str, dados: dict) -> str:
    g = lambda campo: _texto(dados.get(campo))

    if aba == "alunos":
        assunto = g("tipo_auxilio")
        programa = f'{g("programa")} - {g("nivel")}'
    else:
        assunto = "Verba do programa"
        programa = g("programa")

    linhas = [
        f'Interessada(o): {g("nome")} - {g("n_usp")}',
        f'E-mail: {g("email")}',
        f'Assunto: Solicitação de Auxílio Financeiro - {assunto}',
        f'Programa: {programa}',
        '',
        f'A CCP-{g("programa")} aprovou na data de hoje, a solicitação de auxílio financeiro para a',
        'interessada(o) acima, conforme segue:',
        '',
        'Dados do evento',
        f'Evento: {g("nome_evento")}',
        f'Período: {g("periodo")}',
        f'Local: {g("cidade_evento")} - {g("estado_evento")} - {g("pais_evento")}',
    ]

    if g("link_evento"):
        linhas.append(f'Link do evento: {g("link_evento")}')

    linhas += [
        f'Apresentação de trabalho: {g("apresentacao")}',
        f'Valor solicitado: {formatar_valor(g("valor"))}',
        f'Detalhamento: {g("detalhamento")}',
        '',
        'Endereço da(o) interessada(o)',
        f'{g("logradouro")}, {g("numero")}',
    ]

    if g("complemento"):
        linhas.append(f'Complemento: {g("complemento")}')

    linhas += [
        f'CEP: {g("cep")}',
        f'{g("bairro")}, {g("cidade")} - {g("estado")}',
        '',
        'Dados para pagamento',
        f'Data de nascimento: {g("data_nascimento")}',
        f'CPF: {g("cpf")}',
        f'RG / RNM: {g("rg")}',
        f'Banco: {g("banco")}',
        f'Agência: {g("agencia")}',
        f'Conta: {g("conta")}',
        '',
        'Encaminhe-se ao Serviço Financeiro para providências.',
    ]

    return "\n".join(linhas)


# --------------------------------------------------------------------------
# Rota
# --------------------------------------------------------------------------


@app.post("/solicitar")
async def solicitar(payload: dict):
    aba = payload.get("aba", "alunos")
    if aba not in ("alunos", "docentes"):
        aba = "alunos"
    dados = payload.get("dados") or {}

    erros = validar(aba, dados)
    if erros:
        return JSONResponse({"erros": erros, "oficio": None})

    return {"erros": [], "oficio": gerar_oficio(aba, dados)}


# --------------------------------------------------------------------------
# Arquivos estáticos
# --------------------------------------------------------------------------


@app.get("/")
def index():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/style.css")
def style():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


app.mount(
    "/assets",
    StaticFiles(directory=BASE / "assets", check_dir=False),
    name="assets",
)
