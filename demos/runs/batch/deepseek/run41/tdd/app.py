import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
async def pagina_inicial():
    return FileResponse("index.html")


@app.get("/style.css")
async def folha_de_estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
async def script():
    return FileResponse("app.js", media_type="application/javascript")


def _digitos(valor):
    return re.sub("[^0-9]", "", "" if valor is None else str(valor))


def _formatar_cpf(digitos):
    return "{}.{}.{}-{}".format(digitos[:3], digitos[3:6], digitos[6:9], digitos[9:])


def _cpf_valido(digitos):
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    numeros = [int(c) for c in digitos]
    for posicao in (9, 10):
        soma = sum(numeros[i] * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[posicao]:
            return False
    return True


def _data_valida(digitos):
    try:
        date(int(digitos[4:]), int(digitos[2:4]), int(digitos[:2]))
        return True
    except ValueError:
        return False


def _formatar_moeda(digitos):
    centavos = int(digitos)
    reais = "{:,}".format(centavos // 100).replace(",", ".")
    return "R$ {},{:02d}".format(reais, centavos % 100)


CAMPOS_OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao", "data_nascimento",
    "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf",
    "rg", "nome_banco", "numero_agencia", "numero_conta",
]


def _validar(data):
    fatais = []
    formatos = []

    if str(data.get("aba") or "ALUNOS").upper() != "DOCENTES":
        obrigatorios = CAMPOS_OBRIGATORIOS + ["nivel", "tipo_auxilio"]
    else:
        obrigatorios = CAMPOS_OBRIGATORIOS
    if any(not str(data.get(campo) or "").strip() for campo in obrigatorios):
        fatais.append("Preencha todos os campos")

    n_usp = str(data.get("n_usp") or "").strip()
    if n_usp and not n_usp.isdigit():
        fatais.append("N. USP deve conter apenas números")

    agencia = str(data.get("numero_agencia") or "").strip()
    if agencia and not agencia.isdigit():
        fatais.append("Número da agência deve conter apenas números")

    email = str(data.get("email") or "").strip()
    if email and not re.fullmatch("[^@ ]+@[^@ ]+[.][^@ ]+", email):
        fatais.append("E-mail inválido")

    valor = _digitos(data.get("valor_solicitado"))
    if not valor or int(valor) <= 0:
        fatais.append("Valor solicitado deve ser maior que 0")

    cpf = str(data.get("cpf") or "").strip()
    if cpf:
        digitos = _digitos(cpf)
        if len(digitos) == 11:
            if cpf != _formatar_cpf(digitos):
                formatos.append("CPF deve estar no formato 000.000.000-00")
            if not _cpf_valido(digitos):
                fatais.append("CPF inválido")
        else:
            fatais.append("CPF deve estar no formato 000.000.000-00")

    cep = str(data.get("cep") or "").strip()
    if cep:
        digitos = _digitos(cep)
        if len(digitos) == 8:
            if cep != "{}-{}".format(digitos[:5], digitos[5:]):
                formatos.append("CEP deve estar no formato 00000-000")
        else:
            fatais.append("CEP deve estar no formato 00000-000")

    nascimento = str(data.get("data_nascimento") or "").strip()
    if nascimento:
        digitos = _digitos(nascimento)
        if len(digitos) == 8:
            if nascimento != "{}/{}/{}".format(digitos[:2], digitos[2:4], digitos[4:]):
                formatos.append("Data de nascimento deve estar no formato dd/mm/aaaa")
            if not _data_valida(digitos):
                fatais.append("Data de nascimento inválida")
        else:
            fatais.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    return fatais, formatos


def _gerar_oficio(data):
    def campo(nome):
        return str(data.get(nome) or "").strip()

    if str(data.get("aba") or "ALUNOS").upper() == "DOCENTES":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = "Programa: {}".format(campo("programa"))
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - {}".format(campo("tipo_auxilio"))
        programa = "Programa: {} - {}".format(campo("programa"), campo("nivel"))

    cep = _digitos(campo("cep"))
    cep = "{}-{}".format(cep[:5], cep[5:])
    nascimento = _digitos(campo("data_nascimento"))
    nascimento = "{}/{}/{}".format(nascimento[:2], nascimento[2:4], nascimento[4:])
    valor = _formatar_moeda(_digitos(campo("valor_solicitado")))

    linhas = [
        "Interessada(o): {} - {}".format(campo("nome_completo"), campo("n_usp")),
        "E-mail: {}".format(campo("email")),
        assunto,
        programa,
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(campo("programa")),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(campo("nome_evento")),
        "Período: {}".format(campo("periodo_evento")),
        "Local: {} - {} - {}".format(campo("cidade_evento"), campo("estado_evento"), campo("pais_evento")),
    ]
    if campo("link_evento"):
        linhas.append("Link do evento: {}".format(campo("link_evento")))
    linhas += [
        "Apresentação de trabalho: {}".format(campo("apresentacao")),
        "Valor solicitado: {}".format(valor),
        "Detalhamento: {}".format(campo("detalhamento")),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(campo("logradouro"), campo("numero")),
    ]
    if campo("complemento"):
        linhas.append("Complemento: {}".format(campo("complemento")))
    linhas += [
        "CEP: {}".format(cep),
        "{}, {} - {}".format(campo("bairro"), campo("cidade"), campo("estado")),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(nascimento),
        "CPF: {}".format(_formatar_cpf(_digitos(campo("cpf")))),
        "RG / RNM: {}".format(campo("rg")),
        "Banco: {}".format(campo("nome_banco")),
        "Agência: {}".format(campo("numero_agencia")),
        "Conta: {}".format(campo("numero_conta")),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitar(request: Request):
    data = await request.json()
    fatais, formatos = _validar(data)
    if fatais:
        return {"ok": False, "erros": fatais + formatos}
    return {"ok": True, "oficio": _gerar_oficio(data), "erros": formatos}
