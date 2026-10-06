import os
import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}
EXTRAS_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]

CAMPOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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


def valor(campos: dict, campo: str) -> str:
    return str(campos.get(campo, "") or "").strip()


def digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def valor_em_centavos(texto: str) -> int | None:
    if not re.fullmatch(r"R?\$?[0-9.,\s]*", texto):
        return None
    numero = digitos(texto)
    return int(numero) if numero else None


def cpf_valido(cpf: str) -> bool:
    numero = [int(d) for d in digitos(cpf)]
    if len(numero) != 11:
        return False
    dv1 = sum(numero[i] * (10 - i) for i in range(9)) % 11
    dv1 = 0 if dv1 < 2 else 11 - dv1
    dv2 = sum(numero[i] * (11 - i) for i in range(10)) % 11
    dv2 = 0 if dv2 < 2 else 11 - dv2
    return numero[9] == dv1 and numero[10] == dv2


def data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def valor_formatado(texto: str) -> str:
    centavos = valor_em_centavos(texto)
    if centavos is None:
        return texto
    inteiro = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {inteiro},{centavos % 100:02d}"


def validar(tipo: str, campos: dict) -> list[str]:
    obrigatorios = [c for c in CAMPOS if c not in OPCIONAIS]
    if tipo == "alunos":
        obrigatorios += EXTRAS_ALUNOS

    erros: list[str] = []
    if any(valor(campos, c) == "" for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = valor(campos, "N. USP")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = valor(campos, "NÚMERO DA AGÊNCIA")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    solicitado = valor(campos, "VALOR SOLICITADO (R$)")
    if solicitado:
        centavos = valor_em_centavos(solicitado)
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = valor(campos, "E-MAIL")
    if email and not re.fullmatch(r"\S+@\S+", email):
        erros.append("E-mail inválido")

    cpf = valor(campos, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = valor(campos, "CEP")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = valor(campos, "DATA DE NASCIMENTO")
    nascimento_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento))
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if nascimento_no_formato and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(tipo: str, campos: dict) -> str:
    if tipo == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {valor(campos, 'PROGRAMA')}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {valor(campos, 'TIPO DE AUXÍLIO')}"
        linha_programa = f"Programa: {valor(campos, 'PROGRAMA')} - {valor(campos, 'NÍVEL')}"

    linhas = [
        f"Interessada(o): {valor(campos, 'NOME COMPLETO - SEM ABREVIAR')} - {valor(campos, 'N. USP')}",
        f"E-mail: {valor(campos, 'E-MAIL')}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{valor(campos, 'PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {valor(campos, 'NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {valor(campos, 'PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        (
            f"Local: {valor(campos, 'CIDADE DO EVENTO, EXAME OU DEFESA')}"
            f" - {valor(campos, 'ESTADO DO EVENTO, EXAME OU DEFESA')}"
            f" - {valor(campos, 'PAÍS DO EVENTO, EXAME OU DEFESA')}"
        ),
    ]
    if valor(campos, "LINK DO EVENTO, EXAME OU DEFESA"):
        linhas.append(f"Link do evento: {valor(campos, 'LINK DO EVENTO, EXAME OU DEFESA')}")
    linhas += [
        f"Apresentação de trabalho: {valor(campos, 'IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {valor_formatado(valor(campos, 'VALOR SOLICITADO (R$)'))}",
        f"Detalhamento: {valor(campos, 'DETALHAMENTO DO PEDIDO')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{valor(campos, 'LOGRADOURO')}, {valor(campos, 'NÚMERO')}",
    ]
    if valor(campos, "COMPLEMENTO"):
        linhas.append(f"Complemento: {valor(campos, 'COMPLEMENTO')}")
    linhas += [
        f"CEP: {valor(campos, 'CEP')}",
        f"{valor(campos, 'BAIRRO')}, {valor(campos, 'CIDADE')} - {valor(campos, 'ESTADO')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {valor(campos, 'DATA DE NASCIMENTO')}",
        f"CPF: {valor(campos, 'CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"RG / RNM: {valor(campos, 'RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"Banco: {valor(campos, 'NOME DO BANCO')}",
        f"Agência: {valor(campos, 'NÚMERO DA AGÊNCIA')}",
        f"Conta: {valor(campos, 'NÚMERO DA CONTA')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
async def index():
    return FileResponse("index.html")


@app.get("/style.css")
async def folha_de_estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
async def script_da_pagina():
    return FileResponse("app.js", media_type="text/javascript")


if os.path.isdir("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.post("/solicitacao")
async def solicitar(dados: dict) -> dict:
    corpo = dict(dados or {})
    tipo = str(corpo.pop("tipo", "alunos"))
    campos = corpo.pop("campos", None)
    if not isinstance(campos, dict):
        campos = corpo
    if tipo not in ("alunos", "docentes"):
        return {"ok": False, "erros": ["Tipo de solicitação inválido"]}
    erros = validar(tipo, campos)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(tipo, campos)}
