import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf]
    soma = sum(d * p for d, p in zip(digitos, range(10, 1, -1)))
    if (11 - soma % 11) % 11 != digitos[9]:
        return False
    soma = sum(d * p for d, p in zip(digitos, range(11, 1, -1)))
    return (11 - soma % 11) % 11 == digitos[10]


ERROS_CAMPOS = {
    "n_usp": (lambda d: d["n_usp"].isdigit(), "N. USP deve conter apenas números"),
    "email": (lambda d: "@" in d["email"] and bool(re.match(r"@[^@.]+\.[^@.]+", d["email"])), "E-mail inválido"),
    "valor": (lambda d: d["valor"].isdigit() and int(d["valor"]) > 0, "Valor solicitado deve ser maior que 0"),
    "cpf": (lambda d: bool(re.match(r"\d{3}\.\d{3}\.\d{3}-\d{2}$", d["cpf"])), "CPF deve estar no formato 000.000.000-00"),
    "cep": (lambda d: bool(re.match(r"\d{5}-\d{3}$", d["cep"])), "CEP deve estar no formato 00000-000"),
    "data_nascimento": (lambda d: bool(re.match(r"\d{2}/\d{2}/\d{4}$", d["data_nascimento"])), "Data de nascimento deve estar no formato dd/mm/aaaa"),
    "agencia": (lambda d: d["agencia"].isdigit(), "Número da agência deve conter apenas números"),
}


def _moeda_centavos(centavos: int) -> str:
    inteiro, resto = divmod(centavos, 100)
    inteiro_formatado = "{:,}".format(inteiro).replace(",", ".")
    return "R$ {}.{}".format(inteiro_formatado, str(resto).zfill(2))


def _validar(dados: dict, tipo: str) -> list:
    obrigatorios = [k for k in (
        "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email", "nome_evento",
        "periodo", "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
        "complemento", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
        "agencia", "conta",
    ) if dados.get(k, "").strip() != "" or (tipo == "docentes" and k not in ("nivel", "tipo_auxilio", "complemento"))]
    faltam = (len(obrigatorios) < 27 if tipo == "docentes" else len(obrigatorios) < 28)
    faltam = faltam or (tipo == "docentes" and dados.get("complemento", "").strip() != "")
    erros = []
    if faltam:
        erros.append("Preencha todos os campos")
    for chave, (confere, mensagem) in ERROS_CAMPOS.items():
        if not confere(dados):
            erros.append(mensagem)
    if "cpf" not in erros:
        if not _cpf_valido(re.sub(r"\D", "", dados["cpf"])):
            erros.append("CPF inválido")
    if "data_nascimento" not in erros:
        dia, mes, ano = [int(p) for p in dados["data_nascimento"].split("/")]
        ultimo = [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31,
                  30, 31, 31, 30, 31, 30, 31][mes - 1]
        if not 1 <= dia <= ultimo:
            erros.append("Data de nascimento inválida")
    return erros


def _oficio(dados: dict, tipo: str) -> str:
    valor = _moeda_centavos(int(dados["valor"]))
    linhas = [
        "Interessada(o): {} - {}".format(dados["nome"], dados["n_usp"]),
        "E-mail: {}".format(dados["email"]),
    ]
    if tipo == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(dados["tipo_auxilio"]))
        linhas.append("Programa: {} - {}".format(dados["programa"], dados["nivel"]))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(dados["programa"]))
    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(dados["programa"]),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(dados["nome_evento"]),
        "Período: {}".format(dados["periodo"]),
        "Local: {} - {} - {}".format(dados["cidade_evento"], dados["estado_evento"], dados["pais_evento"]),
    ]
    if dados.get("link", "").strip():
        linhas.append("Link do evento: {}".format(dados["link"]))
    linhas += [
        "Apresentação de trabalho: {}".format(dados["apresentacao"]),
        "Valor solicitado: {}".format(valor),
        "Detalhamento: {}".format(dados["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(dados["logradouro"], dados["numero"]),
    ]
    if dados.get("complemento", "").strip():
        linhas.append("Complemento: {}".format(dados["complemento"]))
    linhas += [
        "CEP: {}".format(dados["cep"]),
        "{}, {} - {}".format(dados["bairro"], dados["cidade"], dados["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(dados["data_nascimento"]),
        "CPF: {}".format(dados["cpf"]),
        "RG / RNM: {}".format(dados["rg"]),
        "Banco: {}".format(dados["banco"]),
        "Agência: {}".format(dados["agencia"]),
        "Conta: {}".format(dados["conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/", response_class=HTMLResponse)
def tela():
    with open("index.html", "rb") as arquivo:
        return arquivo.read().decode("utf-8")


@app.post("/solicitacao")
def solicitar(dados: dict):
    tipo = dados.get("tipo", "alunos")
    erros = _validar(dados, tipo)
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(dados, tipo)}


app.mount("/", StaticFiles(directory=".", html=True), name="estaticos")
