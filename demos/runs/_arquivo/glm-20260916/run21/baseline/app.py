import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

CAMPOS = [
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
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
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

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}
SOMENTE_ALUNOS = {"NÍVEL", "TIPO DE AUXÍLIO"}

OBRIGATORIOS = {
    "ALUNOS": [c for c in CAMPOS if c not in OPCIONAIS],
    "DOCENTES": [c for c in CAMPOS if c not in OPCIONAIS and c not in SOMENTE_ALUNOS],
}

app = FastAPI()


def texto(campos, campo):
    valor = campos.get(campo, "")
    return ("" if valor is None else str(valor)).strip()


def cpf_valido(cpf):
    digitos = re.sub(r"[^0-9]", "", cpf)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for posicao, peso_inicial in ((9, 10), (10, 11)):
        soma = sum(int(digitos[i]) * (peso_inicial - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != int(digitos[posicao]):
            return False
    return True


def validar(aba, campos):
    erros = []

    if any(not texto(campos, c) for c in OBRIGATORIOS[aba]):
        erros.append("Preencha todos os campos")

    n_usp = texto(campos, "N. USP")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = texto(campos, "NÚMERO DA AGÊNCIA")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor_bruto = texto(campos, "VALOR SOLICITADO (R$)")
    if valor_bruto:
        limpo = valor_bruto.replace("R$", "").strip()
        if re.fullmatch(r"[0-9]{1,3}(\.[0-9]{3})*,[0-9]{2}|[0-9]+", limpo):
            if int(re.sub(r"[^0-9]", "", limpo)) <= 0:
                erros.append("Valor solicitado deve ser maior que 0")
        else:
            erros.append("Valor solicitado deve ser maior que 0")

    email = texto(campos, "E-MAIL")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = texto(campos, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = texto(campos, "CEP")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(campos, "DATA DE NASCIMENTO")
    data_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento))
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_no_formato:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def moeda(valor):
    limpo = valor.replace("R$", "").strip()
    if re.fullmatch(r"[0-9]{1,3}(\.[0-9]{3})*,[0-9]{2}", limpo):
        return "R$ " + limpo
    if re.fullmatch(r"[0-9]+", limpo):
        partes = f"{int(limpo) / 100:,.2f}"
        return "R$ " + partes.replace(",", "@").replace(".", ",").replace("@", ".")
    return valor


def oficio(aba, campos):
    def v(campo):
        return texto(campos, campo)

    if aba == "DOCENTES":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: " + v("PROGRAMA")
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + v("TIPO DE AUXÍLIO")
        programa = "Programa: " + v("PROGRAMA") + " - " + v("NÍVEL")

    linhas = [
        "Interessada(o): " + v("NOME COMPLETO - SEM ABREVIAR") + " - " + v("N. USP"),
        "E-mail: " + v("E-MAIL"),
        assunto,
        programa,
        "",
        "A CCP-" + v("PROGRAMA") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + v("NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
        "Período: " + v("PERÍODO DO EVENTO, EXAME OU DEFESA"),
        "Local: " + v("CIDADE DO EVENTO, EXAME OU DEFESA") + " - " + v("ESTADO DO EVENTO, EXAME OU DEFESA") + " - " + v("PAÍS DO EVENTO, EXAME OU DEFESA"),
    ]
    if v("LINK DO EVENTO, EXAME OU DEFESA"):
        linhas.append("Link do evento: " + v("LINK DO EVENTO, EXAME OU DEFESA"))
    linhas.extend([
        "Apresentação de trabalho: " + v("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
        "Valor solicitado: " + moeda(v("VALOR SOLICITADO (R$)")),
        "Detalhamento: " + v("DETALHAMENTO DO PEDIDO"),
        "",
        "Endereço da(o) interessada(o)",
        v("LOGRADOURO") + ", " + v("NÚMERO"),
    ])
    if v("COMPLEMENTO"):
        linhas.append("Complemento: " + v("COMPLEMENTO"))
    linhas.extend([
        "CEP: " + v("CEP"),
        v("BAIRRO") + ", " + v("CIDADE") + " - " + v("ESTADO"),
        "",
        "Dados para pagamento",
        "Data de nascimento: " + v("DATA DE NASCIMENTO"),
        "CPF: " + v("CPF (SEPARADOS POR PONTOS E TRAÇO)"),
        "RG / RNM: " + v("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
        "Banco: " + v("NOME DO BANCO"),
        "Agência: " + v("NÚMERO DA AGÊNCIA"),
        "Conta: " + v("NÚMERO DA CONTA"),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def registrar(dados: dict):
    aba = str(dados.get("aba", "")).strip().upper()
    if aba not in OBRIGATORIOS:
        raise HTTPException(status_code=400, detail="Aba inválida")
    campos = dados.get("campos") or {}
    erros = validar(aba, campos)
    return {"erros": erros, "oficio": None if erros else oficio(aba, campos)}


@app.get("/")
@app.get("/index.html")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
