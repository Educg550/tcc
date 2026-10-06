"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

Serve a página (index.html, style.css, app.js e assets/) e recebe a
solicitação em POST /api/solicitacao. Nada é gravado: a resposta traz o
ofício redigido ou as mensagens de erro.
"""

import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()


@app.get("/")
def pagina():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE_DIR / "app.js", media_type="text/javascript")


@app.get("/assets/{arquivo}")
def asset(arquivo: str):
    caminho = BASE_DIR / "assets" / arquivo
    if not caminho.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(caminho)


CAMPOS_COMUNS = (
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_do_evento",
    "periodo_do_evento",
    "cidade_do_evento",
    "estado_do_evento",
    "pais_do_evento",
    "valor_solicitado",
    "detalhamento_do_pedido",
    "ira_apresentar_trabalho",
    "data_de_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg_rnm",
    "nome_do_banco",
    "numero_da_agencia",
    "numero_da_conta",
)
CAMPOS_ALUNOS = CAMPOS_COMUNS + ("nivel", "tipo_de_auxilio")


def texto(dados, chave):
    return str(dados.get(chave) or "").strip()


def valor_maior_que_zero(valor):
    numero = valor.removeprefix("R$").strip().replace(".", "").replace(",", ".")
    try:
        return float(numero) > 0
    except ValueError:
        return False


def email_valido(email):
    partes = email.split("@")
    return len(partes) == 2 and partes[0] != "" and partes[1] != ""


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    for quantidade in (9, 10):
        soma = sum(
            digito * (quantidade + 1 - posicao)
            for posicao, digito in enumerate(digitos[:quantidade])
        )
        verificador = (soma * 10) % 11 % 10
        if verificador != digitos[quantidade]:
            return False
    return True


def validar(dados):
    obrigatorios = CAMPOS_COMUNS if dados.get("aba") == "docentes" else CAMPOS_ALUNOS
    erros = []
    if any(texto(dados, campo) == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "n_usp")
    if n_usp and not re.fullmatch(r"\d+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "numero_da_agencia")
    if agencia and not re.fullmatch(r"\d+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "valor_solicitado")
    if valor and not valor_maior_que_zero(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "email")
    if email and not email_valido(email):
        erros.append("E-mail inválido")

    cpf = texto(dados, "cpf")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "data_de_nascimento")
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def redigir_oficio(dados):
    docentes = dados.get("aba") == "docentes"
    assunto = "Verba do programa" if docentes else texto(dados, "tipo_de_auxilio")
    if docentes:
        linha_programa = f"Programa: {texto(dados, 'programa')}"
    else:
        linha_programa = (
            f"Programa: {texto(dados, 'programa')} - {texto(dados, 'nivel')}"
        )
    linhas = [
        f"Interessada(o): {texto(dados, 'nome_completo')} - {texto(dados, 'n_usp')}",
        f"E-mail: {texto(dados, 'email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{texto(dados, 'programa')} aprovou na data de hoje, "
        "a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {texto(dados, 'nome_do_evento')}",
        f"Período: {texto(dados, 'periodo_do_evento')}",
        "Local: "
        f"{texto(dados, 'cidade_do_evento')} - {texto(dados, 'estado_do_evento')}"
        f" - {texto(dados, 'pais_do_evento')}",
    ]
    link = texto(dados, "link_do_evento")
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {texto(dados, 'ira_apresentar_trabalho')}",
        f"Valor solicitado: {texto(dados, 'valor_solicitado')}",
        f"Detalhamento: {texto(dados, 'detalhamento_do_pedido')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{texto(dados, 'logradouro')}, {texto(dados, 'numero')}",
    ]
    complemento = texto(dados, "complemento")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {texto(dados, 'cep')}",
        f"{texto(dados, 'bairro')}, {texto(dados, 'cidade')} - {texto(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {texto(dados, 'data_de_nascimento')}",
        f"CPF: {texto(dados, 'cpf')}",
        f"RG / RNM: {texto(dados, 'rg_rnm')}",
        f"Banco: {texto(dados, 'nome_do_banco')}",
        f"Agência: {texto(dados, 'numero_da_agencia')}",
        f"Conta: {texto(dados, 'numero_da_conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(dados: dict):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": redigir_oficio(dados)}
