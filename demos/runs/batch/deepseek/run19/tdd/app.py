import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

BASE = Path(__file__).resolve().parent

CAMPOS_COMUNS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao_trabalho",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]


def _texto(valor):
    if valor is None or isinstance(valor, bool):
        return ""
    return str(valor).strip()


def _so_digitos(valor):
    return re.sub(r"\D", "", valor)


def _moeda(digitos):
    reais, centavos = divmod(int(digitos), 100)
    inteiros = "{:,}".format(reais).replace(",", ".")
    return "R$ {},{:02d}".format(inteiros, centavos)


def _cpf_valido(digitos):
    def digito(base):
        peso = len(base) + 1
        soma = sum(int(d) * (peso - i) for i, d in enumerate(base))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    return digitos[9] == digito(digitos[:9]) and digitos[10] == digito(digitos[:10])


def _oficio(aba, d, cpf, cep, nascimento, valor_digitos):
    linhas = [
        "Interessada(o): {} - {}".format(d["nome_completo"], d["n_usp"]),
        "E-mail: {}".format(d["email"]),
    ]
    if aba == "ALUNOS":
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - {}".format(d["tipo_auxilio"])
        )
        linhas.append("Programa: {} - {}".format(d["programa"], d["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(d["programa"]))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            d["programa"]
        ),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(d["nome_evento"]),
        "Período: {}".format(d["periodo_evento"]),
        "Local: {} - {} - {}".format(
            d["cidade_evento"], d["estado_evento"], d["pais_evento"]
        ),
    ]
    if d["link_evento"]:
        linhas.append("Link do evento: {}".format(d["link_evento"]))

    linhas += [
        "Apresentação de trabalho: {}".format(d["apresentacao_trabalho"]),
        "Valor solicitado: {}".format(_moeda(valor_digitos)),
        "Detalhamento: {}".format(d["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(d["logradouro"], d["numero"]),
    ]
    if d["complemento"]:
        linhas.append("Complemento: {}".format(d["complemento"]))

    linhas += [
        "CEP: {}-{}".format(cep[:5], cep[5:]),
        "{}, {} - {}".format(d["bairro"], d["cidade"], d["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}/{}/{}".format(
            nascimento[:2], nascimento[2:4], nascimento[4:]
        ),
        "CPF: {}.{}.{}-{}".format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:]),
        "RG / RNM: {}".format(d["rg"]),
        "Banco: {}".format(d["banco"]),
        "Agência: {}".format(d["agencia"]),
        "Conta: {}".format(d["conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    corpo = await request.json()
    if not isinstance(corpo, dict):
        corpo = {}

    aba = _texto(corpo.get("aba")).upper()
    if aba not in ("ALUNOS", "DOCENTES"):
        aba = "ALUNOS"

    obrigatorios = list(CAMPOS_COMUNS)
    if aba == "ALUNOS":
        obrigatorios += ["nivel", "tipo_auxilio"]

    chaves = set(obrigatorios) | {"link_evento", "complemento"}
    d = {chave: _texto(corpo.get(chave)) for chave in chaves}

    erros = []

    if any(not d[chave] for chave in obrigatorios):
        erros.append("Preencha todos os campos")

    if d["n_usp"] and not re.fullmatch(r"[0-9]+", d["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if d["agencia"] and not re.fullmatch(r"[0-9]+", d["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    valor_digitos = _so_digitos(d["valor_solicitado"])
    if d["valor_solicitado"] and (not valor_digitos or int(valor_digitos) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if d["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", d["email"]):
        erros.append("E-mail inválido")

    cpf = _so_digitos(d["cpf"])
    if d["cpf"] and len(cpf) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = _so_digitos(d["cep"])
    if d["cep"] and len(cep) != 8:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _so_digitos(d["data_nascimento"])
    if d["data_nascimento"] and len(nascimento) != 8:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if d["cpf"] and len(cpf) == 11 and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if d["data_nascimento"] and len(nascimento) == 8:
        try:
            date(int(nascimento[4:]), int(nascimento[2:4]), int(nascimento[:2]))
        except ValueError:
            erros.append("Data de nascimento inválida")

    if erros:
        return {"erros": erros, "oficio": None}

    return {
        "erros": [],
        "oficio": _oficio(aba, d, cpf, cep, nascimento, valor_digitos),
    }


app.mount("/", StaticFiles(directory=BASE, html=True), name="estaticos")
