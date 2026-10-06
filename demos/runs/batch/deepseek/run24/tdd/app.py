import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


class Solicitacao(BaseModel):
    aba: str = "alunos"
    campos: dict[str, str] = {}


OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

OBRIGATORIOS_ALUNOS = OBRIGATORIOS + ["NÍVEL", "TIPO DE AUXÍLIO"]


def _somente_digitos(valor):
    return re.fullmatch(r"\d+", valor) is not None


def _valor_valido(valor):
    limpo = valor.replace("R$", "").strip()
    if not re.fullmatch(r"\d{1,3}(\.\d{3})*(,\d{2})?|\d+", limpo):
        return False
    return int(re.sub(r"\D", "", limpo) or 0) > 0


def _cpf_valido(cpf):
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    for tamanho in (9, 10):
        soma = sum(digitos[i] * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10) % 11 % 10 != digitos[tamanho]:
            return False
    return True


def _data_valida(valor):
    dia, mes, ano = (int(parte) for parte in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _validar(aba, campos):
    erros = []
    obrigatorios = OBRIGATORIOS_ALUNOS if aba == "alunos" else OBRIGATORIOS
    if any(not campos.get(campo, "").strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = campos.get("N. USP", "").strip()
    if nusp and not _somente_digitos(nusp):
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("NÚMERO DA AGÊNCIA", "").strip()
    if agencia and not _somente_digitos(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("VALOR SOLICITADO (R$)", "").strip()
    if valor and not _valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("E-MAIL", "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = campos.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "").strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = campos.get("CEP", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campos.get("DATA DE NASCIMENTO", "").strip()
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def _formata_moeda(valor):
    centavos = int(re.sub(r"\D", "", valor) or 0)
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def _gera_oficio(aba, campos):
    def campo(nome):
        return campos.get(nome, "").strip()

    if aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {campo('PROGRAMA')}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {campo('TIPO DE AUXÍLIO')}"
        programa = f"Programa: {campo('PROGRAMA')} - {campo('NÍVEL')}"

    linhas = [
        f"Interessada(o): {campo('NOME COMPLETO - SEM ABREVIAR')} - {campo('N. USP')}",
        f"E-mail: {campo('E-MAIL')}",
        assunto,
        programa,
        "",
        f"A CCP-{campo('PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campo('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {campo('PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {campo('CIDADE DO EVENTO, EXAME OU DEFESA')} - {campo('ESTADO DO EVENTO, EXAME OU DEFESA')} - {campo('PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ]
    if campo("LINK DO EVENTO, EXAME OU DEFESA"):
        linhas.append(f"Link do evento: {campo('LINK DO EVENTO, EXAME OU DEFESA')}")
    linhas += [
        f"Apresentação de trabalho: {campo('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {_formata_moeda(campo('VALOR SOLICITADO (R$)'))}",
        f"Detalhamento: {campo('DETALHAMENTO DO PEDIDO')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('LOGRADOURO')}, {campo('NÚMERO')}",
    ]
    if campo("COMPLEMENTO"):
        linhas.append(f"Complemento: {campo('COMPLEMENTO')}")
    linhas += [
        f"CEP: {campo('CEP')}",
        f"{campo('BAIRRO')}, {campo('CIDADE')} - {campo('ESTADO')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {campo('DATA DE NASCIMENTO')}",
        f"CPF: {campo('CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"RG / RNM: {campo('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"Banco: {campo('NOME DO BANCO')}",
        f"Agência: {campo('NÚMERO DA AGÊNCIA')}",
        f"Conta: {campo('NÚMERO DA CONTA')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def pagina_inicial():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script_da_pagina():
    return FileResponse(RAIZ / "app.js", media_type="application/javascript")


@app.post("/solicitar")
def solicitar(solicitacao: Solicitacao):
    aba = "docentes" if solicitacao.aba == "docentes" else "alunos"
    erros = _validar(aba, solicitacao.campos)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": _gera_oficio(aba, solicitacao.campos)}
