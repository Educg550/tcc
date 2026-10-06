import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

app.mount("/assets", StaticFiles(directory=BASE / "assets", check_dir=False), name="assets")


@app.get("/")
async def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/index.html")
async def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
async def folha_de_estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
async def script():
    return FileResponse(BASE / "app.js")


CAMPOS_OBRIGATORIOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
)

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _valor_numerico(texto):
    limpo = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _formata_valor(texto):
    digitos = "".join(c for c in texto if c.isdigit())
    total = int(digitos) if digitos else 0
    reais = f"{total // 100:,}".replace(",", ".")
    return f"R$ {reais},{total % 100:02d}"


def _cpf_valido(texto):
    digitos = [int(c) for c in texto if c.isdigit()]
    if len(digitos) != 11:
        return False
    for tamanho in (9, 10):
        soma = sum(digitos[i] * (tamanho + 1 - i) for i in range(tamanho))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[tamanho]:
            return False
    return True


def _data_valida(texto):
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _validar(dados, aluno):
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aluno:
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not dados.get(campo, "").strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados.get("n_usp", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("agencia", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = dados.get("valor", "").strip()
    if valor:
        numero = _valor_numerico(valor)
        if numero is None or numero <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("email", "").strip()
    if email and not RE_EMAIL.match(email):
        erros.append("E-mail inválido")

    cpf = dados.get("cpf", "").strip()
    if cpf:
        if not RE_CPF.match(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = dados.get("cep", "").strip()
    if cep and not RE_CEP.match(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = dados.get("data_nascimento", "").strip()
    if data:
        if not RE_DATA.match(data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, aluno):
    linhas = [
        f"Interessada(o): {dados.get('nome', '')} - {dados.get('n_usp', '')}",
        f"E-mail: {dados.get('email', '')}",
    ]
    if aluno:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados.get('tipo_auxilio', '')}")
        linhas.append(f"Programa: {dados.get('programa', '')} - {dados.get('nivel', '')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados.get('programa', '')}")

    linhas += [
        "",
        f"A CCP-{dados.get('programa', '')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.get('evento', '')}",
        f"Período: {dados.get('periodo', '')}",
        f"Local: {dados.get('cidade_evento', '')} - {dados.get('estado_evento', '')} - {dados.get('pais_evento', '')}",
    ]

    link = dados.get("link_evento", "").strip()
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {dados.get('apresentacao', '')}",
        f"Valor solicitado: {_formata_valor(dados.get('valor', ''))}",
        f"Detalhamento: {dados.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
    ]

    complemento = dados.get("complemento", "").strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {dados.get('cep', '')}",
        f"{dados.get('bairro', '')}, {dados.get('cidade', '')} - {dados.get('estado', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.get('data_nascimento', '')}",
        f"CPF: {dados.get('cpf', '')}",
        f"RG / RNM: {dados.get('rg', '')}",
        f"Banco: {dados.get('banco', '')}",
        f"Agência: {dados.get('agencia', '')}",
        f"Conta: {dados.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    if "application/json" in request.headers.get("content-type", ""):
        corpo = await request.json()
    else:
        corpo = dict(await request.form())
    dados = {chave: valor for chave, valor in corpo.items() if isinstance(valor, str)}
    aluno = dados.get("aba", "").strip().lower().startswith("aluno")
    erros = _validar(dados, aluno)
    if erros:
        return JSONResponse({"ok": False, "erros": erros, "oficio": ""})
    return JSONResponse({"ok": True, "erros": [], "oficio": _oficio(dados, aluno)})
