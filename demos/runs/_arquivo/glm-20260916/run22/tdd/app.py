import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}
EXCLUSIVOS_ALUNOS = {"NÍVEL", "TIPO DE AUXÍLIO"}

CAMPOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
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

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


def _obrigatorios(docente):
    return [
        campo
        for campo in CAMPOS
        if campo not in OPCIONAIS and not (docente and campo in EXCLUSIVOS_ALUNOS)
    ]


def _valor_ok(valor):
    texto = valor.strip()
    if not texto.upper().startswith("R$"):
        return False
    numero = texto[2:].strip()
    if not re.fullmatch(r"\d{1,3}(\.\d{3})*,\d{2}", numero):
        return False
    return int(numero.replace(".", "").replace(",", "")) > 0


def _cpf_valido(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    digito1 = sum(digitos[i] * (10 - i) for i in range(9)) % 11
    digito1 = 0 if digito1 < 2 else 11 - digito1
    digito2 = sum(digitos[i] * (11 - i) for i in range(10)) % 11
    digito2 = 0 if digito2 < 2 else 11 - digito2
    return digitos[9] == digito1 and digitos[10] == digito2


def _validar(dados):
    erros = []
    docente = str(dados.get("ABA", "")) == "DOCENTES"
    if not str(dados.get("ABA", "")).strip() or any(
        not str(dados.get(campo, "")).strip() for campo in _obrigatorios(docente)
    ):
        erros.append("Preencha todos os campos")

    n_usp = str(dados.get("N. USP", ""))
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("NÚMERO DA AGÊNCIA", ""))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("VALOR SOLICITADO (R$)", ""))
    if valor and not _valor_ok(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("E-MAIL", ""))
    usuario, _, dominio = email.partition("@")
    if email and (not usuario or not dominio):
        erros.append("E-mail inválido")

    cpf = str(dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", ""))
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = str(dados.get("CEP", ""))
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = str(dados.get("DATA DE NASCIMENTO", ""))
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados):
    if str(dados.get("ABA", "")) == "DOCENTES":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['PROGRAMA']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {dados['TIPO DE AUXÍLIO']}"
        programa = f"Programa: {dados['PROGRAMA']} - {dados['NÍVEL']}"

    linhas = [
        f"Interessada(o): {dados['NOME COMPLETO - SEM ABREVIAR']} - {dados['N. USP']}",
        f"E-mail: {dados['E-MAIL']}",
        f"Assunto: {assunto}",
        programa,
        "",
        f"A CCP-{dados['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {dados['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {dados['CIDADE DO EVENTO, EXAME OU DEFESA']} - {dados['ESTADO DO EVENTO, EXAME OU DEFESA']} - {dados['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]
    if str(dados.get("LINK DO EVENTO, EXAME OU DEFESA", "")).strip():
        linhas.append(f"Link do evento: {dados['LINK DO EVENTO, EXAME OU DEFESA']}")
    linhas += [
        f"Apresentação de trabalho: {dados['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {dados['VALOR SOLICITADO (R$)']}",
        f"Detalhamento: {dados['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['LOGRADOURO']}, {dados['NÚMERO']}",
    ]
    if str(dados.get("COMPLEMENTO", "")).strip():
        linhas.append(f"Complemento: {dados['COMPLEMENTO']}")
    linhas += [
        f"CEP: {dados['CEP']}",
        f"{dados['BAIRRO']}, {dados['CIDADE']} - {dados['ESTADO']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['DATA DE NASCIMENTO']}",
        f"CPF: {dados['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"RG / RNM: {dados['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"Banco: {dados['NOME DO BANCO']}",
        f"Agência: {dados['NÚMERO DA AGÊNCIA']}",
        f"Conta: {dados['NÚMERO DA CONTA']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def registrar_solicitacao(dados: dict):
    erros = _validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(dados)}


@app.get("/")
def pagina_inicial():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script_da_pagina():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
