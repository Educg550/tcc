import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


CAMPOS_OBRIGATORIOS = [
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


def _campos_obrigatorios(aba):
    if aba == "alunos":
        return CAMPOS_OBRIGATORIOS
    return [c for c in CAMPOS_OBRIGATORIOS if c not in ("NÍVEL", "TIPO DE AUXÍLIO")]


def _apenas_digitos(valor):
    return bool(re.fullmatch(r"\d+", valor))


def _cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    for n in (9, 10):
        soma = sum(d[i] * (n + 1 - i) for i in range(n))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != d[n]:
            return False
    return True


def _data_existente(data):
    dia, mes, ano = (int(p) for p in data.split("/"))
    try:
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _valor_em_centavos(valor):
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return 0
    return int(digitos)


def _formatar_valor(valor):
    centavos = _valor_em_centavos(valor)
    reais = "{:,}".format(centavos // 100).replace(",", ".")
    return "R$ {},{:02d}".format(reais, centavos % 100)


def validar(dados, aba):
    erros = []
    obrigatorios = _campos_obrigatorios(aba)

    if any(not str(dados.get(campo, "")).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = str(dados.get("N. USP", "")).strip()
    if nusp and not _apenas_digitos(nusp):
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("NÚMERO DA AGÊNCIA", "")).strip()
    if agencia and not _apenas_digitos(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("VALOR SOLICITADO (R$)", "")).strip()
    if valor and _valor_em_centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("E-MAIL", "")).strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = str(dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "")).strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = str(dados.get("CEP", "")).strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = str(dados.get("DATA DE NASCIMENTO", "")).strip()
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_existente(data):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados, aba):
    def v(campo):
        return str(dados.get(campo, "")).strip()

    linhas = [
        "Interessada(o): {} - {}".format(v("NOME COMPLETO - SEM ABREVIAR"), v("N. USP")),
        "E-mail: {}".format(v("E-MAIL")),
    ]
    if aba == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - {}".format(v("TIPO DE AUXÍLIO")))
        linhas.append("Programa: {} - {}".format(v("PROGRAMA"), v("NÍVEL")))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(v("PROGRAMA")))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(v("PROGRAMA")),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(v("NOME DO EVENTO / BANCA DE EXAME OU DEFESA")),
        "Período: {}".format(v("PERÍODO DO EVENTO, EXAME OU DEFESA")),
        "Local: {} - {} - {}".format(
            v("CIDADE DO EVENTO, EXAME OU DEFESA"),
            v("ESTADO DO EVENTO, EXAME OU DEFESA"),
            v("PAÍS DO EVENTO, EXAME OU DEFESA"),
        ),
    ]

    link = v("LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append("Link do evento: {}".format(link))

    linhas += [
        "Apresentação de trabalho: {}".format(v("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?")),
        "Valor solicitado: {}".format(_formatar_valor(v("VALOR SOLICITADO (R$)"))),
        "Detalhamento: {}".format(v("DETALHAMENTO DO PEDIDO")),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(v("LOGRADOURO"), v("NÚMERO")),
    ]

    complemento = v("COMPLEMENTO")
    if complemento:
        linhas.append("Complemento: {}".format(complemento))

    linhas += [
        "CEP: {}".format(v("CEP")),
        "{}, {} - {}".format(v("BAIRRO"), v("CIDADE"), v("ESTADO")),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(v("DATA DE NASCIMENTO")),
        "CPF: {}".format(v("CPF (SEPARADOS POR PONTOS E TRAÇO)")),
        "RG / RNM: {}".format(v("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)")),
        "Banco: {}".format(v("NOME DO BANCO")),
        "Agência: {}".format(v("NÚMERO DA AGÊNCIA")),
        "Conta: {}".format(v("NÚMERO DA CONTA")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/style.css")
def estilos():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")


@app.post("/api/solicitacao/{aba}")
def solicitar(aba: str, dados: dict):
    erros = validar(dados, aba)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados, aba)}
