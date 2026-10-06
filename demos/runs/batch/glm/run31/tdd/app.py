"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

OBRIGATORIOS = {
    "aluno": (
        "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
        "evento", "periodo", "cidade", "estado_evento", "pais", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade_endereco", "estado_endereco",
        "cpf", "rg", "banco", "agencia", "conta",
    ),
    "docente": (
        "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade",
        "estado_evento", "pais", "valor", "detalhamento", "apresentacao",
        "data_nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade_endereco", "estado_endereco", "cpf", "rg", "banco",
        "agencia", "conta",
    ),
}

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


def texto(dados, campo):
    valor = dados.get(campo)
    return "" if valor is None else str(valor).strip()


def cpf_valido(cpf):
    digitos = [int(digito) for digito in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    dv1 = sum(d * (10 - i) for i, d in enumerate(digitos[:9])) * 10 % 11 % 10
    dv2 = sum(d * (11 - i) for i, d in enumerate(digitos[:10])) * 10 % 11 % 10
    return digitos[9] == dv1 and digitos[10] == dv2


def data_valida(data):
    dia, mes, ano = (int(parte) for parte in data.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def para_decimal(valor):
    limpo = valor.removeprefix("R$").strip().replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def em_moeda(valor):
    inteiro, centavos = divmod(round(valor * 100), 100)
    return f"R$ {inteiro:,}".replace(",", ".") + f",{centavos:02d}"


def validar(dados, tipo):
    erros = []
    if any(not texto(dados, campo) for campo in OBRIGATORIOS[tipo]):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "valor")
    if valor:
        numero = para_decimal(valor)
        if numero is None or numero <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = texto(dados, "cpf")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "data_nascimento")
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(dados, tipo):
    t = {campo: texto(dados, campo) for campo in (
        "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
        "evento", "periodo", "cidade", "estado_evento", "pais", "link",
        "valor", "detalhamento", "apresentacao", "data_nascimento",
        "logradouro", "numero", "complemento", "bairro", "cep",
        "cidade_endereco", "estado_endereco", "cpf", "rg", "banco",
        "agencia", "conta",
    )}

    if tipo == "docente":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {t['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {t['tipo_auxilio']}"
        programa = f"Programa: {t['programa']} - {t['nivel']}"

    linhas = [
        f"Interessada(o): {t['nome']} - {t['n_usp']}",
        f"E-mail: {t['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{t['programa']} aprovou na data de hoje, a solicitação de "
        "auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {t['evento']}",
        f"Período: {t['periodo']}",
        f"Local: {t['cidade']} - {t['estado_evento']} - {t['pais']}",
    ]
    if t["link"]:
        linhas.append(f"Link do evento: {t['link']}")
    linhas += [
        f"Apresentação de trabalho: {t['apresentacao']}",
        f"Valor solicitado: {em_moeda(para_decimal(t['valor']))}",
        f"Detalhamento: {t['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{t['logradouro']}, {t['numero']}",
    ]
    if t["complemento"]:
        linhas.append(f"Complemento: {t['complemento']}")
    linhas += [
        f"CEP: {t['cep']}",
        f"{t['bairro']}, {t['cidade_endereco']} - {t['estado_endereco']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {t['data_nascimento']}",
        f"CPF: {t['cpf']}",
        f"RG / RNM: {t['rg']}",
        f"Banco: {t['banco']}",
        f"Agência: {t['agencia']}",
        f"Conta: {t['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def criar_solicitacao(dados: dict = Body(...)):
    tipo = "docente" if texto(dados, "tipo") == "docente" else "aluno"
    erros = validar(dados, tipo)
    if erros:
        return JSONResponse(status_code=400, content={"ok": False, "erros": erros})
    return {"ok": True, "oficio": montar_oficio(dados, tipo)}


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="estaticos")
