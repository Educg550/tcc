import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

NOME = "NOME COMPLETO - SEM ABREVIAR"
NUSP = "N. USP"
PROGRAMA = "PROGRAMA"
NIVEL = "NÍVEL"
TIPO_AUXILIO = "TIPO DE AUXÍLIO"
EMAIL = "E-MAIL"
EVENTO = "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"
PERIODO = "PERÍODO DO EVENTO, EXAME OU DEFESA"
CIDADE_EVENTO = "CIDADE DO EVENTO, EXAME OU DEFESA"
ESTADO_EVENTO = "ESTADO DO EVENTO, EXAME OU DEFESA"
PAIS = "PAÍS DO EVENTO, EXAME OU DEFESA"
LINK = "LINK DO EVENTO, EXAME OU DEFESA"
VALOR = "VALOR SOLICITADO (R$)"
DETALHAMENTO = "DETALHAMENTO DO PEDIDO"
APRESENTACAO = "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"
NASCIMENTO = "DATA DE NASCIMENTO"
LOGRADOURO = "LOGRADOURO"
NUMERO = "NÚMERO"
COMPLEMENTO = "COMPLEMENTO"
BAIRRO = "BAIRRO"
CEP = "CEP"
CIDADE = "CIDADE"
ESTADO = "ESTADO"
CPF = "CPF (SEPARADOS POR PONTOS E TRAÇO)"
RG = "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"
BANCO = "NOME DO BANCO"
AGENCIA = "NÚMERO DA AGÊNCIA"
CONTA = "NÚMERO DA CONTA"

OBRIGATORIOS = [
    NOME, NUSP, PROGRAMA, EMAIL, EVENTO, PERIODO, CIDADE_EVENTO, ESTADO_EVENTO, PAIS,
    VALOR, DETALHAMENTO, APRESENTACAO, NASCIMENTO, LOGRADOURO, NUMERO, BAIRRO, CEP,
    CIDADE, ESTADO, CPF, RG, BANCO, AGENCIA, CONTA,
]
SO_ALUNOS = [NIVEL, TIPO_AUXILIO]


def _digitos(valor):
    return re.sub(r"\D", "", valor)


def _moeda(valor):
    centavos = int(_digitos(valor) or 0)
    inteiros = f"{centavos // 100:,}".replace(",", ".")
    return "R$ {},{:02d}".format(inteiros, centavos % 100)


def _cpf_formatado(valor):
    d = _digitos(valor)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else valor


def _cep_formatado(valor):
    d = _digitos(valor)
    return f"{d[:5]}-{d[5:]}" if len(d) == 8 else valor


def _data_formatada(valor):
    d = _digitos(valor)
    return f"{d[:2]}/{d[2:4]}/{d[4:]}" if len(d) == 8 else valor


def _cpf_valido(digitos):
    if digitos == digitos[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(digitos[i]) * (posicao + 1 - i) for i in range(posicao))
        if int(digitos[posicao]) != (soma * 10) % 11 % 10:
            return False
    return True


def _data_existente(digitos):
    try:
        date(int(digitos[4:]), int(digitos[2:4]), int(digitos[:2]))
    except ValueError:
        return False
    return True


def validar(aba, c):
    erros = []
    obrigatorios = OBRIGATORIOS + (SO_ALUNOS if aba == "alunos" else [])
    if any(not c.get(campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = c.get(NUSP, "")
    if nusp and not re.fullmatch(r"[0-9]+", nusp):
        erros.append("N. USP deve conter apenas números")

    agencia = c.get(AGENCIA, "")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = c.get(VALOR, "")
    if valor and not (_digitos(valor) and int(_digitos(valor)) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = c.get(EMAIL, "")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = c.get(CPF, "")
    cpf_digitos = _digitos(cpf)
    if cpf and len(cpf_digitos) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = c.get(CEP, "")
    if cep and len(_digitos(cep)) != 8:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = c.get(NASCIMENTO, "")
    nascimento_digitos = _digitos(nascimento)
    if nascimento and len(nascimento_digitos) != 8:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and len(cpf_digitos) == 11 and not _cpf_valido(cpf_digitos):
        erros.append("CPF inválido")

    if nascimento and len(nascimento_digitos) == 8 and not _data_existente(nascimento_digitos):
        erros.append("Data de nascimento inválida")

    return erros


def oficio(aba, c):
    linhas = [
        f"Interessada(o): {c[NOME]} - {c[NUSP]}",
        f"E-mail: {c[EMAIL]}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {c[TIPO_AUXILIO]}")
        linhas.append(f"Programa: {c[PROGRAMA]} - {c[NIVEL]}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {c[PROGRAMA]}")

    linhas += [
        "",
        f"A CCP-{c[PROGRAMA]} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c[EVENTO]}",
        f"Período: {c[PERIODO]}",
        f"Local: {c[CIDADE_EVENTO]} - {c[ESTADO_EVENTO]} - {c[PAIS]}",
    ]
    if c[LINK]:
        linhas.append(f"Link do evento: {c[LINK]}")
    linhas += [
        f"Apresentação de trabalho: {c[APRESENTACAO]}",
        f"Valor solicitado: {_moeda(c[VALOR])}",
        f"Detalhamento: {c[DETALHAMENTO]}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c[LOGRADOURO]}, {c[NUMERO]}",
    ]
    if c[COMPLEMENTO]:
        linhas.append(f"Complemento: {c[COMPLEMENTO]}")
    linhas += [
        f"CEP: {_cep_formatado(c[CEP])}",
        f"{c[BAIRRO]}, {c[CIDADE]} - {c[ESTADO]}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_data_formatada(c[NASCIMENTO])}",
        f"CPF: {_cpf_formatado(c[CPF])}",
        f"RG / RNM: {c[RG]}",
        f"Banco: {c[BANCO]}",
        f"Agência: {c[AGENCIA]}",
        f"Conta: {c[CONTA]}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    corpo = await request.json()
    aba = str(corpo.get("aba", "alunos")).strip().lower()
    campos = corpo.get("campos") or corpo
    c = {chave: str(valor or "").strip() for chave, valor in campos.items() if chave != "aba"}
    erros = validar(aba, c)
    if erros:
        return {"aba": aba, "erros": erros, "oficio": None}
    return {"aba": aba, "erros": [], "oficio": oficio(aba, c)}


@app.get("/")
@app.get("/index.html")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
