import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    nome_banco: str = ""
    numero_agencia: str = ""
    numero_conta: str = ""


OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "nome_evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "nome_banco",
    "numero_agencia",
    "numero_conta",
]

SO_DOCENTES_NAO_TEM = ("nivel", "tipo_auxilio")


def _centavos(texto):
    """Converte o valor digitado (centavos crus ou moeda formatada) em centavos."""
    limpo = texto.replace("R$", "").strip()
    if "," in limpo:
        try:
            return round(float(limpo.replace(".", "").replace(",", ".")) * 100)
        except ValueError:
            return None
    if limpo.isdigit():
        return int(limpo)
    return None


def _formata_moeda(centavos):
    reais = "{:,}".format(centavos // 100).replace(",", ".")
    return "R$ {}, {:02d}".format(reais, centavos % 100).replace(", ", ",")


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    for i in (9, 10):
        soma = sum(digitos[j] * (i + 1 - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[i]:
            return False
    return True


def _valida(dados, aba):
    erros = []
    obrigatorios = [
        campo for campo in OBRIGATORIOS if not (aba == "docentes" and campo in SO_DOCENTES_NAO_TEM)
    ]
    if any(not dados[campo].strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados["n_usp"].strip()
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = dados["numero_agencia"].strip()
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = dados["valor_solicitado"].strip()
    if valor:
        centavos = _centavos(valor)
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = dados["email"].strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = dados["cpf"].strip()
    if cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = dados["cep"].strip()
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados["data_nascimento"].strip()
    if nascimento:
        partes = re.fullmatch(r"([0-9]{2})/([0-9]{2})/([0-9]{4})", nascimento)
        if not partes:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                date(int(partes.group(3)), int(partes.group(2)), int(partes.group(1)))
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, aba):
    linhas = [
        "Interessada(o): {} - {}".format(dados["nome_completo"], dados["n_usp"]),
        "E-mail: {}".format(dados["email"]),
    ]
    if aba == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(dados["tipo_auxilio"]))
        linhas.append("Programa: {} - {}".format(dados["programa"], dados["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(dados["programa"]))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            dados["programa"]
        ),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(dados["nome_evento"]),
        "Período: {}".format(dados["periodo"]),
        "Local: {} - {} - {}".format(dados["cidade_evento"], dados["estado_evento"], dados["pais_evento"]),
    ]

    if dados["link_evento"].strip():
        linhas.append("Link do evento: {}".format(dados["link_evento"]))

    linhas += [
        "Apresentação de trabalho: {}".format(dados["apresentacao"]),
        "Valor solicitado: {}".format(_formata_moeda(_centavos(dados["valor_solicitado"]))),
        "Detalhamento: {}".format(dados["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(dados["logradouro"], dados["numero"]),
    ]

    if dados["complemento"].strip():
        linhas.append("Complemento: {}".format(dados["complemento"]))

    linhas += [
        "CEP: {}".format(dados["cep"]),
        "{}, {} - {}".format(dados["bairro"], dados["cidade"], dados["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(dados["data_nascimento"]),
        "CPF: {}".format(dados["cpf"]),
        "RG / RNM: {}".format(dados["rg"]),
        "Banco: {}".format(dados["nome_banco"]),
        "Agência: {}".format(dados["numero_agencia"]),
        "Conta: {}".format(dados["numero_conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


def _responde(dados, aba):
    valores = dados.model_dump()
    erros = _valida(valores, aba)
    if erros:
        return {"erros": erros}
    return {"erros": [], "oficio": _oficio(valores, aba)}


@app.post("/api/alunos")
def solicitar_alunos(dados: Solicitacao):
    return _responde(dados, "alunos")


@app.post("/api/docentes")
def solicitar_docentes(dados: Solicitacao):
    return _responde(dados, "docentes")


app.mount("/", StaticFiles(directory=BASE, html=True), name="estatico")
