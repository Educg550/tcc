import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
app = FastAPI()

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]
OBRIGATORIOS_ALUNOS = OBRIGATORIOS + ["nivel", "tipo_auxilio"]


def _txt(dados, campo):
    valor = dados.get(campo, "")
    return valor.strip() if isinstance(valor, str) else ""


def _valor_em_centavos(valor):
    texto = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", texto):
        return None
    reais, _, centavos = texto.partition(".")
    return int(reais) * 100 + int((centavos + "00")[:2])


def _cpf_valido(cpf):
    numeros = [int(digito) for digito in re.sub(r"\D", "", cpf)]
    dv1 = (sum(numeros[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(numeros[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return numeros[9] == dv1 and numeros[10] == dv2


def validar(dados, aba):
    erros = []
    obrigatorios = OBRIGATORIOS if aba == "docentes" else OBRIGATORIOS_ALUNOS
    if any(not _txt(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _txt(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _txt(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _txt(dados, "valor")
    if valor and not _valor_em_centavos(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _txt(dados, "email")
    if email:
        local, _, dominio = email.partition("@")
        if not local or not dominio:
            erros.append("E-mail inválido")

    cpf = _txt(dados, "cpf")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = _txt(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _txt(dados, "data_nascimento")
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, aba):
    def campo(nome):
        return _txt(dados, nome)

    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {campo('programa')}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {campo('tipo_auxilio')}"
        linha_programa = f"Programa: {campo('programa')} - {campo('nivel')}"

    linhas = [
        f"Interessada(o): {campo('nome_completo')} - {campo('n_usp')}",
        f"E-mail: {campo('email')}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{campo('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campo('evento')}",
        f"Período: {campo('periodo')}",
        f"Local: {campo('cidade_evento')} - {campo('estado_evento')} - {campo('pais_evento')}",
    ]
    if campo("link"):
        linhas.append(f"Link do evento: {campo('link')}")
    linhas += [
        f"Apresentação de trabalho: {campo('apresentacao')}",
        f"Valor solicitado: {campo('valor')}",
        f"Detalhamento: {campo('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('logradouro')}, {campo('numero')}",
    ]
    if campo("complemento"):
        linhas.append(f"Complemento: {campo('complemento')}")
    linhas += [
        f"CEP: {campo('cep')}",
        f"{campo('bairro')}, {campo('cidade')} - {campo('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {campo('data_nascimento')}",
        f"CPF: {campo('cpf')}",
        f"RG / RNM: {campo('rg')}",
        f"Banco: {campo('banco')}",
        f"Agência: {campo('agencia')}",
        f"Conta: {campo('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitar(request: Request):
    try:
        dados = await request.()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}
    aba = dados.get("aba", "alunos")
    erros = validar(dados, aba)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"oficio": _oficio(dados, aba)})


@app.get("/", response_class=HTMLResponse)
async def pagina():
    return (BASE / "index.html").read_text(encoding="utf-8")


@app.get("/style.css")
async def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
async def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets", check_dir=False), name="assets")
