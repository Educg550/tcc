import re
from datetime import date

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]

FORMATO_CPF = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
FORMATO_CEP = r"\d{5}-\d{3}"
FORMATO_DATA = r"\d{2}/\d{2}/\d{4}"
EMAIL = r"[^@\s]+@[^@\s]+\.[^@\s]+"


def cpf_valido(cpf):
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(set(numeros)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(numeros[j] * ((posicao + 1) - j) for j in range(posicao))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[posicao]:
            return False
    return True


def valor_formatado(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return valor or ""
    centavos = int(digitos)
    reais = re.sub(r"\B(?=(\d{3})+(?!\d))", ".", str(centavos // 100))
    return "R$ %s,%02d" % (reais, centavos % 100)


def validar(aba, campos):
    def texto(nome):
        return (campos.get(nome) or "").strip()

    erros = []

    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not texto(nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")

    if texto("n_usp") and not re.fullmatch(r"\d+", texto("n_usp")):
        erros.append("N. USP deve conter apenas números")

    if texto("agencia") and not re.fullmatch(r"\d+", texto("agencia")):
        erros.append("Número da agência deve conter apenas números")

    valor = texto("valor")
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if texto("email") and not re.fullmatch(EMAIL, texto("email")):
        erros.append("E-mail inválido")

    cpf = texto("cpf")
    cpf_formato_ok = bool(re.fullmatch(FORMATO_CPF, cpf)) if cpf else False
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if texto("cep") and not re.fullmatch(FORMATO_CEP, texto("cep")):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto("data_nascimento")
    data_formato_ok = bool(re.fullmatch(FORMATO_DATA, nascimento)) if nascimento else False
    if nascimento and not data_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato_ok and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_formato_ok:
        dia, mes, ano = nascimento.split("/")
        try:
            date(int(ano), int(mes), int(dia))
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(aba, campos):
    def texto(nome):
        return (campos.get(nome) or "").strip()

    linhas = [
        "Interessada(o): %s - %s" % (texto("nome"), texto("n_usp")),
        "E-mail: %s" % texto("email"),
    ]
    if aba == "alunos":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - %s" % texto("tipo_auxilio"))
        linhas.append("Programa: %s - %s" % (texto("programa"), texto("nivel")))
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: %s" % texto("programa"))

    linhas.append("")
    linhas.append("A CCP-%s aprovou na data de hoje, a solicitação de auxílio financeiro para a" % texto("programa"))
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: %s" % texto("evento"))
    linhas.append("Período: %s" % texto("periodo"))
    linhas.append("Local: %s - %s - %s" % (texto("cidade_evento"), texto("estado_evento"), texto("pais_evento")))
    if texto("link_evento"):
        linhas.append("Link do evento: %s" % texto("link_evento"))
    linhas.append("Apresentação de trabalho: %s" % texto("apresentacao"))
    linhas.append("Valor solicitado: %s" % valor_formatado(texto("valor")))
    linhas.append("Detalhamento: %s" % texto("detalhamento"))
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append("%s, %s" % (texto("logradouro"), texto("numero")))
    if texto("complemento"):
        linhas.append("Complemento: %s" % texto("complemento"))
    linhas.append("CEP: %s" % texto("cep"))
    linhas.append("%s, %s - %s" % (texto("bairro"), texto("cidade"), texto("estado")))
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: %s" % texto("data_nascimento"))
    linhas.append("CPF: %s" % texto("cpf"))
    linhas.append("RG / RNM: %s" % texto("rg"))
    linhas.append("Banco: %s" % texto("banco"))
    linhas.append("Agência: %s" % texto("agencia"))
    linhas.append("Conta: %s" % texto("conta"))
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(pedido: Request):
    corpo = await pedido.json()
    aba = corpo.get("aba")
    if aba not in ("alunos", "docentes"):
        aba = "alunos"
    campos = corpo.get("campos") or {}
    erros = validar(aba, campos)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(aba, campos)}


@app.get("/")
def pagina():
    return Response(open("index.html", encoding="utf-8").read(), media_type="text/html")


@app.get("/style.css")
def estilos():
    return Response(open("style.css", encoding="utf-8").read(), media_type="text/css")


@app.get("/app.js")
def script():
    return Response(open("app.js", encoding="utf-8").read(), media_type="application/javascript")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
