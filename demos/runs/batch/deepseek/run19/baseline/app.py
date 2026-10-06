import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento_nome", "evento_periodo",
    "evento_cidade", "evento_estado", "evento_pais", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(d[j] * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != d[i]:
            return False
    return True


def data_valida(data):
    dia, mes, ano = (int(p) for p in data.split("/"))
    if not 1 <= mes <= 12:
        return False
    try:
        datetime.date(ano, mes, dia)
        return True
    except ValueError:
        return False


def formata_moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def gera_oficio(campos, aba):
    c = {k: str(v).strip() for k, v in campos.items()}
    centavos = int(re.sub(r"\D", "", c["valor"]))
    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {c['tipo_auxilio']}"
        linha_programa = f"Programa: {c['programa']} - {c['nivel']}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {c['programa']}"

    linhas = [
        f"Interessada(o): {c['nome']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['evento_nome']}",
        f"Período: {c['evento_periodo']}",
        f"Local: {c['evento_cidade']} - {c['evento_estado']} - {c['evento_pais']}",
    ]
    if c.get("evento_link"):
        linhas.append(f"Link do evento: {c['evento_link']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao']}",
        f"Valor solicitado: {formata_moeda(centavos)}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c.get("complemento"):
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['data_nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def valida(campos, aba):
    c = {k: str(v).strip() for k, v in campos.items()}
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not c.get(nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")

    if c.get("n_usp") and not c["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")

    if c.get("agencia") and not c["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")

    if c.get("valor"):
        digitos = re.sub(r"\D", "", c["valor"])
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if c.get("email") and not RE_EMAIL.match(c["email"]):
        erros.append("E-mail inválido")

    if c.get("cpf") and not RE_CPF.match(c["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")

    if c.get("cep") and not RE_CEP.match(c["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    if c.get("data_nascimento") and not RE_DATA.match(c["data_nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if c.get("cpf") and RE_CPF.match(c["cpf"]) and not cpf_valido(c["cpf"]):
        erros.append("CPF inválido")

    if c.get("data_nascimento") and RE_DATA.match(c["data_nascimento"]) and not data_valida(c["data_nascimento"]):
        erros.append("Data de nascimento inválida")

    return erros


@app.post("/api/solicitacao")
async def solicitar(pedido: dict):
    campos = pedido.get("campos", {})
    aba = pedido.get("aba", "alunos")
    erros = valida(campos, aba)
    if erros:
        return {"erros": erros}
    return {"oficio": gera_oficio(campos, aba)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="static")
