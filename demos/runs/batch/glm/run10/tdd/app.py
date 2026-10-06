import datetime
import re

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS_BASE = [
    "nome_completo", "n_usp", "programa", "email",
    "nome_evento", "periodo", "cidade_evento", "estado_evento",
    "pais_evento", "valor_solicitado", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_ALUNO = ["nivel", "tipo_auxilio"]


def centavos(valor):
    v = valor.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return round(float(v) * 100)
    except ValueError:
        return None


def formatar_moeda(cent):
    texto = str(cent).rjust(3, "0")
    inteiro, cent = texto[:-2], texto[-2:]
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    return "R$ " + ".".join(grupos) + "," + cent


def cpf_valido(d):
    if len(set(d)) == 1:
        return False
    s = sum(int(d[i]) * (10 - i) for i in range(9))
    d1 = (s * 10) % 11 % 10
    if d1 != int(d[9]):
        return False
    s = sum(int(d[i]) * (11 - i) for i in range(10))
    d2 = (s * 10) % 11 % 10
    return d2 == int(d[10])


def validar(dados):
    erros = []
    aba = dados.get("aba", "alunos")
    campos = list(CAMPOS_BASE) + (CAMPOS_ALUNO if aba == "alunos" else [])
    if any(not str(dados.get(c, "")).strip() for c in campos):
        erros.append("Preencha todos os campos")
    if not re.fullmatch(r"\d+", str(dados.get("n_usp", ""))):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"\d+", str(dados.get("agencia", ""))):
        erros.append("Número da agência deve conter apenas números")
    cent = centavos(str(dados.get("valor_solicitado", "")))
    if cent is None or cent <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(dados.get("email", ""))):
        erros.append("E-mail inválido")
    cpf = str(dados.get("cpf", ""))
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(cpf.replace(".", "").replace("-", "")):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", str(dados.get("cep", ""))):
        erros.append("CEP deve estar no formato 00000-000")
    data = str(dados.get("data_nascimento", ""))
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dia, mes, ano = (int(x) for x in data.split("/"))
        try:
            datetime.date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(dados):
    aba = dados.get("aba", "alunos")
    d = dados
    linhas = [
        "Interessada(o): {} - {}".format(d["nome_completo"], d["n_usp"]),
        "E-mail: " + d["email"],
    ]
    if aba == "alunos":
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - " + d["tipo_auxilio"]
        )
        linhas.append("Programa: {} - {}".format(d["programa"], d["nivel"]))
    else:
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        )
        linhas.append("Programa: " + d["programa"])
    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            d["programa"]
        ),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + d["nome_evento"],
        "Período: " + d["periodo"],
        "Local: {} - {} - {}".format(
            d["cidade_evento"], d["estado_evento"], d["pais_evento"]
        ),
    ]
    if d.get("link_evento", "").strip():
        linhas.append("Link do evento: " + d["link_evento"])
    linhas.append("Apresentação de trabalho: " + d["apresentacao"])
    linhas.append(
        "Valor solicitado: " + formatar_moeda(centavos(d["valor_solicitado"]))
    )
    linhas.append("Detalhamento: " + d["detalhamento"].replace("\n", " "))
    linhas += [
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(d["logradouro"], d["numero"]),
    ]
    if d.get("complemento", "").strip():
        linhas.append("Complemento: " + d["complemento"])
    linhas += [
        "CEP: " + d["cep"],
        "{}, {} - {}".format(d["bairro"], d["cidade"], d["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + d["data_nascimento"],
        "CPF: " + d["cpf"],
        "RG / RNM: " + d["rg"],
        "Banco: " + d["banco"],
        "Agência: " + d["agencia"],
        "Conta: " + d["conta"],
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={"errors": erros})
    return {"oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=".", html=True), name="estaticos")
