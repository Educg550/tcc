import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE = Path(__file__).resolve().parent


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]

CPF_FORMATO = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_FORMATO = re.compile(r"^\d{5}-\d{3}$")
DATA_FORMATO = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _cpf_valido(cpf):
    nums = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(set(nums)) == 1:
        return False
    for i in (9, 10):
        soma = sum(nums[j] * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != nums[i]:
            return False
    return True


def _data_valida(texto):
    try:
        datetime.datetime.strptime(texto, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validar(dados):
    erros = []

    obrigatorios = list(OBRIGATORIOS)
    if dados.get("aba") == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not str(dados.get(c, "")).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = str(dados.get("n_usp", "")).strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", "")).strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("valor", "")).strip()
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", "")).strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = str(dados.get("cpf", "")).strip()
    cpf_formato_ok = bool(cpf) and bool(CPF_FORMATO.match(cpf))
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = str(dados.get("cep", "")).strip()
    if cep and not CEP_FORMATO.match(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = str(dados.get("data_nascimento", "")).strip()
    data_formato_ok = bool(data) and bool(DATA_FORMATO.match(data))
    if data and not data_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato_ok and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_formato_ok and not _data_valida(data):
        erros.append("Data de nascimento inválida")

    return erros


def _formatar_valor(valor):
    digitos = re.sub(r"\D", "", str(valor))
    reais, centavos = divmod(int(digitos), 100)
    milhares = f"{reais:,}".replace(",", ".")
    return f"R$ {milhares},{centavos:02d}"


def gerar_oficio(dados):
    aba = dados.get("aba")
    programa = str(dados.get("programa", "")).strip()

    if aba == "alunos":
        assunto = "Solicitação de Auxílio Financeiro - " + str(dados.get("tipo_auxilio", "")).strip()
        programa_linha = programa + " - " + str(dados.get("nivel", "")).strip()
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = programa

    linhas = [
        "Interessada(o): {} - {}".format(dados.get("nome", ""), dados.get("n_usp", "")),
        "E-mail: {}".format(dados.get("email", "")),
        "Assunto: {}".format(assunto),
        "Programa: {}".format(programa_linha),
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(programa),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(dados.get("evento", "")),
        "Período: {}".format(dados.get("periodo", "")),
        "Local: {} - {} - {}".format(
            dados.get("cidade_evento", ""),
            dados.get("estado_evento", ""),
            dados.get("pais_evento", ""),
        ),
    ]

    link = str(dados.get("link_evento", "")).strip()
    if link:
        linhas.append("Link do evento: " + link)

    linhas += [
        "Apresentação de trabalho: {}".format(dados.get("apresentacao", "")),
        "Valor solicitado: {}".format(_formatar_valor(dados.get("valor", ""))),
        "Detalhamento: {}".format(dados.get("detalhamento", "")),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(dados.get("logradouro", ""), dados.get("numero", "")),
    ]

    complemento = str(dados.get("complemento", "")).strip()
    if complemento:
        linhas.append("Complemento: " + complemento)

    linhas += [
        "CEP: {}".format(dados.get("cep", "")),
        "{}, {} - {}".format(
            dados.get("bairro", ""), dados.get("cidade", ""), dados.get("estado", "")
        ),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(dados.get("data_nascimento", "")),
        "CPF: {}".format(dados.get("cpf", "")),
        "RG / RNM: {}".format(dados.get("rg", "")),
        "Banco: {}".format(dados.get("banco", "")),
        "Agência: {}".format(dados.get("agencia", "")),
        "Conta: {}".format(dados.get("conta", "")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="static")
