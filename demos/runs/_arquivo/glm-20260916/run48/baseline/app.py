import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

OBRIGATORIOS = (
    "nome", "nusps", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
)


def txt(dados, campo):
    return str(dados.get(campo) or "").strip()


def cpf_valido(digitos):
    d = [int(c) for c in digitos]
    dv1 = (sum(d[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(d[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return d[9] == dv1 and d[10] == dv2


def formatar_moeda(campo):
    digitos = re.sub(r"\D", "", campo).zfill(3)
    inteiro = f"{int(digitos[:-2]):,}".replace(",", ".")
    return f"R$ {inteiro},{digitos[-2:]}"


def validar(dados):
    obrigatorios = OBRIGATORIOS
    if txt(dados, "tipo") == "alunos":
        obrigatorios = OBRIGATORIOS + ("nivel", "tipo_auxilio")
    erros = []
    if any(not txt(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    nusps = txt(dados, "nusps")
    if nusps and not nusps.isdigit():
        erros.append("N. USP deve conter apenas números")
    agencia = txt(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = txt(dados, "valor")
    centavos = re.sub(r"\D", "", valor)
    if valor and (not centavos or int(centavos) == 0):
        erros.append("Valor solicitado deve ser maior que 0")
    email = txt(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")
    cpf = txt(dados, "cpf")
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    cep = txt(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    nasc = txt(dados, "data_nascimento")
    nasc_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nasc))
    if nasc and not nasc_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    data_valida = True
    if nasc and nasc_no_formato:
        dia, mes, ano = nasc.split("/")
        try:
            datetime(int(ano), int(mes), int(dia))
        except ValueError:
            data_valida = False
    if cpf and cpf_no_formato and not cpf_valido(re.sub(r"\D", "", cpf)):
        erros.append("CPF inválido")
    if nasc and nasc_no_formato and not data_valida:
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(dados):
    if txt(dados, "tipo") == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {txt(dados, 'tipo_auxilio')}"
        programa = f"Programa: {txt(dados, 'programa')} - {txt(dados, 'nivel')}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {txt(dados, 'programa')}"
    linhas = [
        f"Interessada(o): {txt(dados, 'nome')} - {txt(dados, 'nusps')}",
        f"E-mail: {txt(dados, 'email')}",
        assunto,
        programa,
        "",
        f"A CCP-{txt(dados, 'programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {txt(dados, 'evento')}",
        f"Período: {txt(dados, 'periodo')}",
        f"Local: {txt(dados, 'cidade_evento')} - {txt(dados, 'estado_evento')} - {txt(dados, 'pais_evento')}",
    ]
    if txt(dados, "link"):
        linhas.append(f"Link do evento: {txt(dados, 'link')}")
    linhas += [
        f"Apresentação de trabalho: {txt(dados, 'apresentacao')}",
        f"Valor solicitado: {formatar_moeda(txt(dados, 'valor'))}",
        f"Detalhamento: {txt(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{txt(dados, 'logradouro')}, {txt(dados, 'numero')}",
    ]
    if txt(dados, "complemento"):
        linhas.append(f"Complemento: {txt(dados, 'complemento')}")
    linhas += [
        f"CEP: {txt(dados, 'cep')}",
        f"{txt(dados, 'bairro')}, {txt(dados, 'cidade')} - {txt(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {txt(dados, 'data_nascimento')}",
        f"CPF: {txt(dados, 'cpf')}",
        f"RG / RNM: {txt(dados, 'rg')}",
        f"Banco: {txt(dados, 'banco')}",
        f"Agência: {txt(dados, 'agencia')}",
        f"Conta: {txt(dados, 'conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


app = FastAPI()


@app.post("/api/solicitacao")
def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados)}


app.mount("/assets", StaticFiles(directory=BASE / "assets", check_dir=False), name="assets")


@app.get("/")
def inicio():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")
