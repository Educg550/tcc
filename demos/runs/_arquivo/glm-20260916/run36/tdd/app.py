import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

RAIZ = Path(__file__).resolve().parent

app.mount("/assets", StaticFiles(directory=RAIZ / "assets", check_dir=False), name="assets")

OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
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

CPF_PADRAO = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_PADRAO = re.compile(r"^\d{5}-\d{3}$")
DATA_PADRAO = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def valor(dados, chave):
    v = dados.get(chave, "")
    if not isinstance(v, str):
        v = str(v or "")
    return v.strip()


def cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11:
        return False
    resto = sum(d[i] * (10 - i) for i in range(9)) % 11
    dv1 = 0 if resto < 2 else 11 - resto
    resto = sum(d[i] * (11 - i) for i in range(10)) % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return d[9] == dv1 and d[10] == dv2


def valor_solicitado_valido(texto):
    t = texto.replace("R$", "").replace(" ", "")
    if t.count(",") == 1:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t) > 0
    except ValueError:
        return False


def validar(dados):
    erros = []
    docente = valor(dados, "aba") == "DOCENTES"
    obrigatorios = [
        c for c in OBRIGATORIOS if not (docente and c in ("NÍVEL", "TIPO DE AUXÍLIO"))
    ]
    if any(not valor(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = valor(dados, "N. USP")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = valor(dados, "NÚMERO DA AGÊNCIA")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    solicitado = valor(dados, "VALOR SOLICITADO (R$)")
    if solicitado and not valor_solicitado_valido(solicitado):
        erros.append("Valor solicitado deve ser maior que 0")

    email = valor(dados, "E-MAIL")
    if email and ("@" not in email or not email.split("@", 1)[1]):
        erros.append("E-mail inválido")

    cpf = valor(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf:
        if not CPF_PADRAO.match(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = valor(dados, "CEP")
    if cep and not CEP_PADRAO.match(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = valor(dados, "DATA DE NASCIMENTO")
    if data:
        if not DATA_PADRAO.match(data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def oficio(dados):
    docente = valor(dados, "aba") == "DOCENTES"
    if docente:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + valor(dados, "PROGRAMA")
    else:
        assunto = "Solicitação de Auxílio Financeiro - " + valor(dados, "TIPO DE AUXÍLIO")
        programa = "Programa: " + valor(dados, "PROGRAMA") + " - " + valor(dados, "NÍVEL")

    linhas = [
        "Interessada(o): " + valor(dados, "NOME COMPLETO - SEM ABREVIAR") + " - " + valor(dados, "N. USP"),
        "E-mail: " + valor(dados, "E-MAIL"),
        assunto,
        programa,
        "",
        "A CCP-" + valor(dados, "PROGRAMA") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + valor(dados, "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
        "Período: " + valor(dados, "PERÍODO DO EVENTO, EXAME OU DEFESA"),
        "Local: " + valor(dados, "CIDADE DO EVENTO, EXAME OU DEFESA") + " - " + valor(dados, "ESTADO DO EVENTO, EXAME OU DEFESA") + " - " + valor(dados, "PAÍS DO EVENTO, EXAME OU DEFESA"),
    ]
    link = valor(dados, "LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append("Link do evento: " + link)
    linhas += [
        "Apresentação de trabalho: " + valor(dados, "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
        "Valor solicitado: " + valor(dados, "VALOR SOLICITADO (R$)"),
        "Detalhamento: " + valor(dados, "DETALHAMENTO DO PEDIDO"),
        "",
        "Endereço da(o) interessada(o)",
        valor(dados, "LOGRADOURO") + ", " + valor(dados, "NÚMERO"),
    ]
    complemento = valor(dados, "COMPLEMENTO")
    if complemento:
        linhas.append("Complemento: " + complemento)
    linhas += [
        "CEP: " + valor(dados, "CEP"),
        valor(dados, "BAIRRO") + ", " + valor(dados, "CIDADE") + " - " + valor(dados, "ESTADO"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + valor(dados, "DATA DE NASCIMENTO"),
        "CPF: " + valor(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
        "RG / RNM: " + valor(dados, "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
        "Banco: " + valor(dados, "NOME DO BANCO"),
        "Agência: " + valor(dados, "NÚMERO DA AGÊNCIA"),
        "Conta: " + valor(dados, "NÚMERO DA CONTA"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js")


@app.post("/solicitacao")
async def solicitar(dados: dict):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": oficio(dados)}
