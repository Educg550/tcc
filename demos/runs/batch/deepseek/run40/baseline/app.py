import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

OBRIGATORIOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade_endereco", "estado_endereco", "cpf", "rg", "banco", "agencia", "conta",
)


def centavos(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return int(digitos) if digitos else 0


def formatar_valor(valor):
    digitos = re.sub(r"\D", "", valor or "").lstrip("0") or "0"
    digitos = digitos.zfill(3)
    inteiro = f"{int(digitos[:-2]):,}".replace(",", ".")
    return f"R$ {inteiro},{digitos[-2:]}"


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r"\D", "", cpf)]
    if len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != digitos[posicao]:
            return False
    return True


def data_valida(data):
    dia, mes, ano = (int(parte) for parte in data.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(d):
    campos = OBRIGATORIOS if d.get("tipo") == "docente" else OBRIGATORIOS + ("nivel", "tipo_auxilio")
    erros = []

    if any(not d.get(campo, "").strip() for campo in campos):
        erros.append("Preencha todos os campos")

    n_usp = d.get("n_usp", "").strip()
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = d.get("agencia", "").strip()
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    if d.get("valor", "").strip() and centavos(d["valor"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = d.get("email", "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = d.get("cpf", "").strip()
    cpf_formatado = re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf)
    if cpf and not cpf_formatado:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = d.get("cep", "").strip()
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = d.get("nascimento", "").strip()
    nascimento_formatado = re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento)
    if nascimento and not nascimento_formatado:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formatado and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if nascimento_formatado and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(d):
    def campo(nome):
        return d.get(nome, "").strip()

    linhas = [
        f"Interessada(o): {campo('nome')} - {campo('n_usp')}",
        f"E-mail: {campo('email')}",
    ]
    if campo("tipo") == "docente":
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f"Programa: {campo('programa')}",
        ]
    else:
        linhas += [
            f"Assunto: Solicitação de Auxílio Financeiro - {campo('tipo_auxilio')}",
            f"Programa: {campo('programa')} - {campo('nivel')}",
        ]
    linhas += [
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
        f"Valor solicitado: {formatar_valor(campo('valor'))}",
        f"Detalhamento: {campo('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('logradouro')}, {campo('numero')}",
    ]
    if campo("complemento"):
        linhas.append(f"Complemento: {campo('complemento')}")
    linhas += [
        f"CEP: {campo('cep')}",
        f"{campo('bairro')}, {campo('cidade_endereco')} - {campo('estado_endereco')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {campo('nascimento')}",
        f"CPF: {campo('cpf')}",
        f"RG / RNM: {campo('rg')}",
        f"Banco: {campo('banco')}",
        f"Agência: {campo('agencia')}",
        f"Conta: {campo('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitar(dados: dict):
    d = {chave: "" if valor is None else str(valor) for chave, valor in dados.items()}
    erros = validar(d)
    if erros:
        return {"valido": False, "erros": erros, "oficio": ""}
    return {"valido": True, "erros": [], "oficio": montar_oficio(d)}


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory=str(BASE / "assets")), name="assets")
