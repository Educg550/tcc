"""Backend FastAPI da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
import calendar
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

RAIZ = Path(__file__).resolve().parent

CAMPOS_OPCIONAIS = {"link", "complemento"}

CAMPOS_DOCENTES = [
    "nome", "nusp", "programa", "email", "evento", "periodo",
    "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao",
    "nascimento", "logradouro", "numero", "complemento", "bairro", "cep",
    "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta",
]

CAMPOS_ALUNOS = CAMPOS_DOCENTES[:2] + ["nivel", "auxilio"] + CAMPOS_DOCENTES[2:]

# Serve assets (logo) como estáticos
app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


@app.get("/")
def index():
    return FileResponse(RAIZ / "index.html")


def formatar_cpf(valor):
    digitos = re.sub(r"\D", "", valor or "")
    partes = [digitos[:3], digitos[3:6], digitos[6:9], digitos[9:11]]
    return ".".join(p for p in partes[:3] if p) + ("-" + partes[3] if partes[3] else "")


def formatar_cep(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return digitos[:5] + ("-" + digitos[5:8] if len(digitos) > 5 else "")


def formatar_data(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) <= 2:
        return digitos
    if len(digitos) <= 4:
        return digitos[:2] + "/" + digitos[2:]
    return digitos[:2] + "/" + digitos[2:4] + "/" + digitos[4:8]


def formatar_valor(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return ""
    centavos = int(digitos)
    texto = str(centavos).rjust(3, "0")
    inteiro, dec = texto[:-2], texto[-2:]
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return "R$ " + ".".join(grupos) + "," + dec


@app.post("/api/formata")
def api_formata(dados: dict):
    campo, valor = dados.get("campo", ""), str(dados.get("valor", ""))
    formatadores = {
        "valor": formatar_valor,
        "cpf": formatar_cpf,
        "cep": formatar_cep,
        "nascimento": formatar_data,
    }
    return {"formatado": formatadores.get(campo, lambda v: v)(valor)}


def validar(dados):
    erros = []
    tipo = dados.get("tipo", "alunos")
    campos = CAMPOS_ALUNOS if tipo == "alunos" else CAMPOS_DOCENTES

    if any(str(dados.get(c, "") or "").strip() == "" for c in campos if c not in CAMPOS_OPCIONAIS):
        erros.append("Preencha todos os campos")

    nusp = str(dados.get("nusp", ""))
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", ""))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("valor", ""))
    if valor and not (valor.isdigit() and int(valor) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", ""))
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = formatar_cpf(str(dados.get("cpf", "")))
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = formatar_cep(str(dados.get("cep", "")))
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = formatar_data(str(dados.get("nascimento", "")))
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not _data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum(int(d) * (10 - i) for i, d in enumerate(digitos[:9]))
    d1 = (soma * 10) % 11 % 10
    soma = sum(int(d) * (11 - i) for i, d in enumerate(digitos[:10]))
    d2 = (soma * 10) % 11 % 10
    return d1 == int(digitos[9]) and d2 == int(digitos[10])


def _data_valida(texto):
    dia, mes, ano = int(texto[:2]), int(texto[3:5]), int(texto[6:])
    return 1 <= mes <= 12 and 1 <= dia <= calendar.monthrange(ano, mes)[1]


def gerar_oficio(dados):
    tipo = dados.get("tipo", "alunos")
    linhas = []
    linhas.append(f"Interessada(o): {dados.get('nome')} - {dados.get('nusp')}")
    linhas.append(f"E-mail: {dados.get('email')}")
    if tipo == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados.get('auxilio')}")
        linhas.append(f"Programa: {dados.get('programa')} - {dados.get('nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados.get('programa')}")
    linhas.append("")
    linhas.append(
        "A CCP-" + str(dados.get('programa')) + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {dados.get('evento')}")
    linhas.append(f"Período: {dados.get('periodo')}")
    linhas.append(f"Local: {dados.get('cidade')} - {dados.get('estado')} - {dados.get('pais')}")
    if str(dados.get('link', '')).strip():
        linhas.append(f"Link do evento: {dados.get('link')}")
    linhas.append(f"Apresentação de trabalho: {dados.get('apresentacao')}")
    linhas.append(f"Valor solicitado: {formatar_valor(str(dados.get('valor')))}")
    linhas.append(f"Detalhamento: {dados.get('detalhamento')}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{dados.get('logradouro')}, {dados.get('numero')}")
    if str(dados.get('complemento', '')).strip():
        linhas.append(f"Complemento: {dados.get('complemento')}")
    linhas.append(f"CEP: {formatar_cep(str(dados.get('cep')))}")
    linhas.append(f"{dados.get('bairro')}, {dados.get('cidade_end')} - {dados.get('estado_end')}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {formatar_data(str(dados.get('nascimento')))}")
    linhas.append(f"CPF: {formatar_cpf(str(dados.get('cpf')))}")
    linhas.append(f"RG / RNM: {dados.get('rg')}")
    linhas.append(f"Banco: {dados.get('banco')}")
    linhas.append(f"Agência: {dados.get('agencia')}")
    linhas.append(f"Conta: {dados.get('conta')}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/validar")
def api_validar(dados: dict):
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": gerar_oficio(dados)}
