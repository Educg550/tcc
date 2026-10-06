import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

CAMPOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email", "evento",
    "periodo", "cidade_evento", "estado_evento", "pais_evento", "link_evento",
    "valor", "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
    "agencia", "conta",
]
OPCIONAIS = {"link_evento", "complemento"}
SO_ALUNOS = {"nivel", "tipo_auxilio"}


class Solicitacao(BaseModel):
    aba: str
    campos: dict[str, str]


def cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(d[j] * (i + 1 - j) for j in range(i))
        if (soma * 10) % 11 % 10 != d[i]:
            return False
    return True


def data_existe(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def centavos(valor):
    digitos = re.sub(r"\D", "", valor)
    return int(digitos) if digitos else 0


def formatar_valor(valor):
    reais, resto = divmod(centavos(valor), 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def validar(aba, c):
    obrigatorios = [
        campo
        for campo in CAMPOS
        if campo not in OPCIONAIS and not (aba == "docentes" and campo in SO_ALUNOS)
    ]
    erros = []
    if any(not c[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if c["n_usp"] and not re.fullmatch(r"[0-9]+", c["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if c["agencia"] and not re.fullmatch(r"[0-9]+", c["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if c["valor"] and centavos(c["valor"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if c["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", c["email"]):
        erros.append("E-mail inválido")
    if c["cpf"]:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", c["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(c["cpf"]):
            erros.append("CPF inválido")
    if c["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", c["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if c["nascimento"]:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", c["nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_existe(c["nascimento"]):
            erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(aba, c):
    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = c["programa"]
    else:
        assunto = "Solicitação de Auxílio Financeiro - " + c["tipo_auxilio"]
        programa = c["programa"] + " - " + c["nivel"]

    linhas = [
        f"Interessada(o): {c['nome']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['evento']}",
        f"Período: {c['periodo']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c["link_evento"]:
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao']}",
        f"Valor solicitado: {formatar_valor(c['valor'])}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c["complemento"]:
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg']}",
        f"Banco: {c['banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitar(solicitacao: Solicitacao):
    campos = {campo: (solicitacao.campos.get(campo) or "").strip() for campo in CAMPOS}
    erros = validar(solicitacao.aba, campos)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(solicitacao.aba, campos)}


app.mount("/", StaticFiles(directory=".", html=True), name="estaticos")
