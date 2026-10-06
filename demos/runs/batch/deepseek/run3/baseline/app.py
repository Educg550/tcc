import os
import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

CAMPOS_COMUNS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_ALUNOS = CAMPOS_COMUNS + ["nivel", "tipo_auxilio"]

FORMATO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
FORMATO_CEP = re.compile(r"\d{5}-\d{3}")
FORMATO_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def texto(dados, campo):
    return str(dados.get(campo, "")).strip()


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def data_existente(valor):
    dia, mes, ano = (int(parte) for parte in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formatar_moeda(valor):
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return ""
    numero = int(digitos)
    reais = re.sub(r"\B(?=(\d{3})+(?!\d))", ".", str(numero // 100))
    return f"R$ {reais},{numero % 100:02d}"


def validar(dados, aba):
    obrigatorios = CAMPOS_ALUNOS if aba == "alunos" else CAMPOS_COMUNS
    erros = []

    if any(not texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "valor")
    if valor and int(re.sub(r"\D", "", valor) or "0") == 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "email")
    if email and not FORMATO_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")

    cpf = texto(dados, "cpf")
    cpf_formatado = bool(FORMATO_CPF.fullmatch(cpf))
    if cpf and not cpf_formatado:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = texto(dados, "cep")
    if cep and not FORMATO_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "data_nascimento")
    data_formatada = bool(FORMATO_DATA.fullmatch(nascimento))
    if nascimento and not data_formatada:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formatado and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_formatada and not data_existente(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados, aba):
    def valor(campo):
        return texto(dados, campo)

    linhas = [
        f"Interessada(o): {valor('nome_completo')} - {valor('n_usp')}",
        f"E-mail: {valor('email')}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {valor('tipo_auxilio')}")
        linhas.append(f"Programa: {valor('programa')} - {valor('nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {valor('programa')}")

    linhas += [
        "",
        f"A CCP-{valor('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {valor('nome_evento')}",
        f"Período: {valor('periodo')}",
        f"Local: {valor('cidade_evento')} - {valor('estado_evento')} - {valor('pais_evento')}",
    ]
    if valor("link_evento"):
        linhas.append(f"Link do evento: {valor('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {valor('apresentacao')}",
        f"Valor solicitado: {formatar_moeda(valor('valor'))}",
        f"Detalhamento: {valor('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{valor('logradouro')}, {valor('numero')}",
    ]
    if valor("complemento"):
        linhas.append(f"Complemento: {valor('complemento')}")
    linhas += [
        f"CEP: {valor('cep')}",
        f"{valor('bairro')}, {valor('cidade')} - {valor('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {valor('data_nascimento')}",
        f"CPF: {valor('cpf')}",
        f"RG / RNM: {valor('rg')}",
        f"Banco: {valor('banco')}",
        f"Agência: {valor('agencia')}",
        f"Conta: {valor('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
@app.post("/solicitar")
async def solicitar(requisicao: Request):
    dados = await requisicao.json()
    aba = "docentes" if dados.get("aba") == "docentes" else "alunos"
    erros = validar(dados, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(dados, aba)}


@app.get("/")
async def raiz():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/style.css")
async def estilo():
    return FileResponse(os.path.join(BASE_DIR, "style.css"))


@app.get("/app.js")
async def script():
    return FileResponse(os.path.join(BASE_DIR, "app.js"))


app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")
