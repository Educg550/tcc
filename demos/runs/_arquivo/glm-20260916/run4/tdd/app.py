import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

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

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


def _texto(dados, campo):
    return str(dados.get(campo) or "").strip()


def _cpf_conferem(cpf):
    # módulo 11: os dois dígitos finais devem bater com o quociente da soma
    # dos nove primeiros dígitos dividida por 11
    digitos = re.sub(r"\D", "", cpf)
    if len(set(digitos)) == 1:
        return False
    return int(digitos[9:]) == sum(int(digito) for digito in digitos[:9]) // 11


def _data_existe(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _erros(dados, obrigatorios):
    erros = []
    if any(not _texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "N. USP")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "NÚMERO DA AGÊNCIA")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "VALOR SOLICITADO (R$)")
    if valor and not (valor.isdigit() and int(valor) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "E-MAIL")
    if email and ("@" not in email or not email.split("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_conferem(cpf):
        erros.append("CPF inválido")

    cep = _texto(dados, "CEP")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = _texto(dados, "DATA DE NASCIMENTO")
    if data and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data and not _data_existe(data):
        erros.append("Data de nascimento inválida")

    return erros


def _moeda(digitos_do_valor):
    centavos = int(digitos_do_valor)
    return f"R$ {centavos // 100:,}".replace(",", ".") + f",{centavos % 100:02d}"


def _oficio(dados, aba):
    if aba == "ALUNOS":
        assunto = f"Solicitação de Auxílio Financeiro - {dados['TIPO DE AUXÍLIO']}"
        programa = f"{dados['PROGRAMA']} - {dados['NÍVEL']}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = dados["PROGRAMA"]

    linhas = [
        f"Interessada(o): {dados['NOME COMPLETO - SEM ABREVIAR']} - {dados['N. USP']}",
        f"E-mail: {dados['E-MAIL']}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{dados['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {dados['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        (
            f"Local: {dados['CIDADE DO EVENTO, EXAME OU DEFESA']}"
            f" - {dados['ESTADO DO EVENTO, EXAME OU DEFESA']}"
            f" - {dados['PAÍS DO EVENTO, EXAME OU DEFESA']}"
        ),
    ]

    link = _texto(dados, "LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {dados['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {_moeda(dados['VALOR SOLICITADO (R$)'])}",
        f"Detalhamento: {dados['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['LOGRADOURO']}, {dados['NÚMERO']}",
    ]

    complemento = _texto(dados, "COMPLEMENTO")
    if complemento:
        linhas.append(f"Complemento: {complemento}")

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
    aba = dados.get("ABA") or "ALUNOS"
    obrigatorios = list(OBRIGATORIOS)
    if aba == "ALUNOS":
        obrigatorios += ["NÍVEL", "TIPO DE AUXÍLIO"]
    erros = _erros(dados, obrigatorios)
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(dados, aba)}


@app.get("/")
def pagina_inicial():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script_da_pagina():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets", check_dir=False), name="assets")
