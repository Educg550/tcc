import datetime
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/style.css")
def css():
    return FileResponse("style.css")


@app.get("/app.js")
def js():
    return FileResponse("app.js")


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


def _cpf_valido(cpf):
    numeros = [int(c) for c in re.sub(r"\D", "", cpf)]
    for posicao in (9, 10):
        soma = sum(n * p for n, p in zip(numeros[:posicao], range(posicao + 1, 1, -1)))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[posicao]:
            return False
    return True


def _formatar_moeda(valor):
    centavos = int(re.sub(r"\D", "", valor))
    reais = centavos // 100
    resto = centavos % 100
    inteiro = "{:,}".format(reais).replace(",", ".")
    return "R$ {0},{1:02d}".format(inteiro, resto)


def validar(dados, aba):
    erros = []
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "ALUNOS":
        obrigatorios += ["NÍVEL", "TIPO DE AUXÍLIO"]
    if any(not str(dados.get(c) or "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    usp = str(dados.get("N. USP") or "")
    if usp and not usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("NÚMERO DA AGÊNCIA") or "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("VALOR SOLICITADO (R$)") or "")
    digitos_valor = re.sub(r"\D", "", valor)
    if valor and (not digitos_valor or int(digitos_valor) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("E-MAIL") or "").strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = str(dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)") or "").strip()
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = str(dados.get("CEP") or "").strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = str(dados.get("DATA DE NASCIMENTO") or "").strip()
    if nascimento:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(p) for p in nascimento.split("/"))
            try:
                datetime.date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados, aba):
    if aba == "ALUNOS":
        assunto = dados.get("TIPO DE AUXÍLIO", "")
        programa = "{0} - {1}".format(dados.get("PROGRAMA", ""), dados.get("NÍVEL", ""))
    else:
        assunto = "Verba do programa"
        programa = dados.get("PROGRAMA", "")

    valor = _formatar_moeda(dados.get("VALOR SOLICITADO (R$)", ""))

    linhas = [
        "Interessada(o): {0} - {1}".format(
            dados.get("NOME COMPLETO - SEM ABREVIAR", ""), dados.get("N. USP", "")
        ),
        "E-mail: {0}".format(dados.get("E-MAIL", "")),
        "Assunto: Solicitação de Auxílio Financeiro - {0}".format(assunto),
        "Programa: {0}".format(programa),
        "",
        "A CCP-{0} aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:".format(
            dados.get("PROGRAMA", "")
        ),
        "",
        "Dados do evento",
        "Evento: {0}".format(dados.get("NOME DO EVENTO / BANCA DE EXAME OU DEFESA", "")),
        "Período: {0}".format(dados.get("PERÍODO DO EVENTO, EXAME OU DEFESA", "")),
        "Local: {0} - {1} - {2}".format(
            dados.get("CIDADE DO EVENTO, EXAME OU DEFESA", ""),
            dados.get("ESTADO DO EVENTO, EXAME OU DEFESA", ""),
            dados.get("PAÍS DO EVENTO, EXAME OU DEFESA", ""),
        ),
    ]
    if dados.get("LINK DO EVENTO, EXAME OU DEFESA"):
        linhas.append("Link do evento: {0}".format(dados["LINK DO EVENTO, EXAME OU DEFESA"]))
    linhas += [
        "Apresentação de trabalho: {0}".format(
            dados.get("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?", "")
        ),
        "Valor solicitado: {0}".format(valor),
        "Detalhamento: {0}".format(dados.get("DETALHAMENTO DO PEDIDO", "")),
        "",
        "Endereço da(o) interessada(o)",
        "{0}, {1}".format(dados.get("LOGRADOURO", ""), dados.get("NÚMERO", "")),
    ]
    if dados.get("COMPLEMENTO"):
        linhas.append("Complemento: {0}".format(dados["COMPLEMENTO"]))
    linhas += [
        "CEP: {0}".format(dados.get("CEP", "")),
        "{0}, {1} - {2}".format(
            dados.get("BAIRRO", ""), dados.get("CIDADE", ""), dados.get("ESTADO", "")
        ),
        "",
        "Dados para pagamento",
        "Data de nascimento: {0}".format(dados.get("DATA DE NASCIMENTO", "")),
        "CPF: {0}".format(dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "")),
        "RG / RNM: {0}".format(dados.get("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)", "")),
        "Banco: {0}".format(dados.get("NOME DO BANCO", "")),
        "Agência: {0}".format(dados.get("NÚMERO DA AGÊNCIA", "")),
        "Conta: {0}".format(dados.get("NÚMERO DA CONTA", "")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
def solicitar(payload: dict):
    aba = payload.get("aba", "DOCENTES")
    erros = validar(payload, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(payload, aba)}
