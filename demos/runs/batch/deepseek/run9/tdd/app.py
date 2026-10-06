import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()


OBRIGATORIOS_BASE = [
    "nome",
    "nusp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais",
    "valor",
    "detalhamento",
    "apresentacao",
    "nascimento",
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

OBRIGATORIOS_ALUNOS = OBRIGATORIOS_BASE + ["nivel", "tipo_auxilio"]
OBRIGATORIOS_DOCENTES = list(OBRIGATORIOS_BASE)

RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def _texto(dados, chave):
    return str(dados.get(chave, "") or "").strip()


def _para_centavos(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    if "," in texto:
        limpo = texto.replace("R$", "").strip().replace(".", "")
        inteiro, _, decimal = limpo.partition(",")
        if not inteiro.isdigit():
            return None
        decimal = (decimal + "00")[:2]
        if not decimal.isdigit():
            return None
        return int(inteiro) * 100 + int(decimal)
    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        return None
    return int(digitos)


def _formata_valor(centavos):
    if centavos is None:
        centavos = 0
    inteiros, resto = divmod(int(centavos), 100)
    milhares = f"{inteiros:,}".replace(",", ".")
    return f"R$ {milhares},{resto:02d}"


def _email_valido(valor):
    if valor.count("@") != 1 or " " in valor:
        return False
    local, _, dominio = valor.partition("@")
    return bool(local) and "." in dominio and not dominio.startswith(".") and not dominio.endswith(".")


def _cpf_valido(digitos):
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[n]) * ((i + 1) - n) for n in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def validar(dados, aba):
    obrigatorios = OBRIGATORIOS_DOCENTES if aba == "docentes" else OBRIGATORIOS_ALUNOS

    faltando = any(not _texto(dados, campo) for campo in obrigatorios)

    nusp = _texto(dados, "nusp")
    agencia = _texto(dados, "agencia")
    valor = _texto(dados, "valor")
    email = _texto(dados, "email")
    cpf = _texto(dados, "cpf")
    cep = _texto(dados, "cep")
    nascimento = _texto(dados, "nascimento")

    erros = []

    if faltando:
        erros.append("Preencha todos os campos")

    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    if valor and (_para_centavos(valor) or 0) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    if email and not _email_valido(email):
        erros.append("E-mail inválido")

    cpf_formato_ok = False
    if cpf:
        cpf_formato_ok = bool(RE_CPF.fullmatch(cpf))
        if not cpf_formato_ok:
            erros.append("CPF deve estar no formato 000.000.000-00")

    if cep and not RE_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_formato_ok = False
    data_valida = False
    if nascimento:
        m = RE_DATA.fullmatch(nascimento)
        data_formato_ok = bool(m)
        if not data_formato_ok:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                datetime(ano, mes, dia)
                data_valida = True
            except ValueError:
                data_valida = False

    if cpf and cpf_formato_ok and not _cpf_valido(re.sub(r"\D", "", cpf)):
        erros.append("CPF inválido")

    if nascimento and data_formato_ok and not data_valida:
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados, aba):
    nome = _texto(dados, "nome")
    nusp = _texto(dados, "nusp")
    email = _texto(dados, "email")
    programa = _texto(dados, "programa")
    nivel = _texto(dados, "nivel")
    tipo = _texto(dados, "tipo_auxilio")
    evento = _texto(dados, "evento")
    periodo = _texto(dados, "periodo")
    cidade_evento = _texto(dados, "cidade_evento")
    estado_evento = _texto(dados, "estado_evento")
    pais = _texto(dados, "pais")
    link = _texto(dados, "link")
    detalhamento = _texto(dados, "detalhamento")
    apresentacao = _texto(dados, "apresentacao")
    nascimento = _texto(dados, "nascimento")
    logradouro = _texto(dados, "logradouro")
    numero = _texto(dados, "numero")
    complemento = _texto(dados, "complemento")
    bairro = _texto(dados, "bairro")
    cep = _texto(dados, "cep")
    cidade = _texto(dados, "cidade")
    estado = _texto(dados, "estado")
    cpf = _texto(dados, "cpf")
    rg = _texto(dados, "rg")
    banco = _texto(dados, "banco")
    agencia = _texto(dados, "agencia")
    conta = _texto(dados, "conta")
    valor = _formata_valor(_para_centavos(_texto(dados, "valor")))

    if aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = "Programa: " + programa
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - " + tipo
        programa_linha = "Programa: " + programa + " - " + nivel

    linhas = [
        "Interessada(o): " + nome + " - " + nusp,
        "E-mail: " + email,
        assunto,
        programa_linha,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + evento,
        "Período: " + periodo,
        "Local: " + cidade_evento + " - " + estado_evento + " - " + pais,
    ]

    if link:
        linhas.append("Link do evento: " + link)

    linhas += [
        "Apresentação de trabalho: " + apresentacao,
        "Valor solicitado: " + valor,
        "Detalhamento: " + detalhamento,
        "",
        "Endereço da(o) interessada(o)",
        logradouro + ", " + numero,
    ]

    if complemento:
        linhas.append("Complemento: " + complemento)

    linhas += [
        "CEP: " + cep,
        bairro + ", " + cidade + " - " + estado,
        "",
        "Dados para pagamento",
        "Data de nascimento: " + nascimento,
        "CPF: " + cpf,
        "RG / RNM: " + rg,
        "Banco: " + banco,
        "Agência: " + agencia,
        "Conta: " + conta,
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(request: Request):
    try:
        dados = await request.json()
    except Exception:
        dados = {}
    if not isinstance(dados, dict):
        dados = {}

    aba = "docentes" if str(dados.get("aba", "")).lower() == "docentes" else "alunos"

    erros = validar(dados, aba)
    if erros:
        return JSONResponse({"erros": erros, "oficio": None})

    return JSONResponse({"erros": [], "oficio": gerar_oficio(dados, aba)})


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
