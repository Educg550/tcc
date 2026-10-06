import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
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

CAMPOS_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]


def _campo(dados, nome):
    return (dados.get(nome) or "").strip()


def apenas_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def parse_valor(texto):
    digitos = apenas_digitos(texto)
    if not digitos:
        return None
    return int(digitos)


def formatar_moeda(centavos):
    reais = centavos // 100
    cent = centavos % 100
    milhares = f"{reais:,}".replace(",", ".")
    return f"R$ {milhares},{cent:02d}"


def cpf_valido(cpf):
    nums = [int(d) for d in apenas_digitos(cpf)]
    for i in range(2):
        soma = sum(nums[j] * ((10 + i) - j) for j in range(9 + i))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != nums[9 + i]:
            return False
    return True


def validar(dados, aba):
    erros = []
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "ALUNOS":
        obrigatorios += CAMPOS_ALUNOS
    if any(not _campo(dados, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _campo(dados, "N. USP")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _campo(dados, "NÚMERO DA AGÊNCIA")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _campo(dados, "VALOR SOLICITADO (R$)")
    if valor:
        centavos = parse_valor(valor)
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _campo(dados, "E-MAIL")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = _campo(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _campo(dados, "CEP")
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _campo(dados, "DATA DE NASCIMENTO")
    if nascimento:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(p) for p in nascimento.split("/"))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados, aba):
    c = {campo: _campo(dados, campo) for campo in CAMPOS_OBRIGATORIOS + CAMPOS_ALUNOS}

    if aba == "DOCENTES":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {c['PROGRAMA']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {c['TIPO DE AUXÍLIO']}"
        programa = f"Programa: {c['PROGRAMA']} - {c['NÍVEL']}"

    linhas = [
        f"Interessada(o): {c['NOME COMPLETO - SEM ABREVIAR']} - {c['N. USP']}",
        f"E-mail: {c['E-MAIL']}",
        f"Assunto: {assunto}",
        programa,
        "",
        f"A CCP-{c['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {c['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {c['CIDADE DO EVENTO, EXAME OU DEFESA']} - {c['ESTADO DO EVENTO, EXAME OU DEFESA']} - {c['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]

    link = _campo(dados, "LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas.append(f"Apresentação de trabalho: {c['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}")
    linhas.append(f"Valor solicitado: {formatar_moeda(parse_valor(c['VALOR SOLICITADO (R$)']) or 0)}")
    linhas.append(f"Detalhamento: {c['DETALHAMENTO DO PEDIDO']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{c['LOGRADOURO']}, {c['NÚMERO']}")

    complemento = _campo(dados, "COMPLEMENTO")
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas.append(f"CEP: {c['CEP']}")
    linhas.append(f"{c['BAIRRO']}, {c['CIDADE']} - {c['ESTADO']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {c['DATA DE NASCIMENTO']}")
    linhas.append(f"CPF: {c['CPF (SEPARADOS POR PONTOS E TRAÇO)']}")
    linhas.append(f"RG / RNM: {c['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}")
    linhas.append(f"Banco: {c['NOME DO BANCO']}")
    linhas.append(f"Agência: {c['NÚMERO DA AGÊNCIA']}")
    linhas.append(f"Conta: {c['NÚMERO DA CONTA']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return "\n".join(linhas)


@app.post("/solicitar")
def solicitar(dados: dict):
    aba = dados.get("aba") or "ALUNOS"
    erros = validar(dados, aba)
    resposta = {"erros": erros, "oficio": None}
    if not erros:
        resposta["oficio"] = gerar_oficio(dados, aba)
    return resposta


@app.get("/", include_in_schema=False)
def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/style.css", include_in_schema=False)
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(BASE / "app.js")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
