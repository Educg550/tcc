import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "nome_banco",
    "agencia",
    "conta",
]
OBRIGATORIOS_ALUNOS = OBRIGATORIOS + ["nivel", "tipo_auxilio"]


def _texto(dados, campo):
    valor = dados.get(campo)
    return "" if valor is None else str(valor).strip()


def _valor_centavos(valor):
    digitos = re.sub(r"\D", "", valor)
    return int(digitos) if digitos else 0


def _moeda(centavos):
    reais, cent = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(set(digitos)) == 1:
        return False
    for pos in (9, 10):
        soma = sum(int(digitos[n]) * (pos + 1 - n) for n in range(pos))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if esperado != int(digitos[pos]):
            return False
    return True


def _data_valida(texto):
    dia, mes, ano = (int(p) for p in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _validar(dados, docente):
    erros = []
    obrigatorios = OBRIGATORIOS if docente else OBRIGATORIOS_ALUNOS
    if any(not _texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor_solicitado")
    if valor and _valor_centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _texto(dados, "data_nascimento")
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, docente):
    programa = _texto(dados, "programa")
    linhas = [
        f"Interessada(o): {_texto(dados, 'nome_completo')} - {_texto(dados, 'n_usp')}",
        f"E-mail: {_texto(dados, 'email')}",
    ]
    if docente:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    else:
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - "
            + _texto(dados, "tipo_auxilio")
        )
        linhas.append(f"Programa: {programa} - {_texto(dados, 'nivel')}")

    linhas += [
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados, 'nome_evento')}",
        f"Período: {_texto(dados, 'periodo_evento')}",
        "Local: "
        f"{_texto(dados, 'cidade_evento')} - {_texto(dados, 'estado_evento')} - "
        f"{_texto(dados, 'pais_evento')}",
    ]

    link = _texto(dados, "link_evento")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {_texto(dados, 'apresentacao')}",
        "Valor solicitado: "
        + _moeda(_valor_centavos(_texto(dados, "valor_solicitado"))),
        f"Detalhamento: {_texto(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_texto(dados, 'logradouro')}, {_texto(dados, 'numero')}",
    ]

    complemento = _texto(dados, "complemento")
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {_texto(dados, 'cep')}",
        f"{_texto(dados, 'bairro')}, {_texto(dados, 'cidade')} - {_texto(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_texto(dados, 'data_nascimento')}",
        f"CPF: {_texto(dados, 'cpf')}",
        f"RG / RNM: {_texto(dados, 'rg')}",
        f"Banco: {_texto(dados, 'nome_banco')}",
        f"Agência: {_texto(dados, 'agencia')}",
        f"Conta: {_texto(dados, 'conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


async def _solicitar(request, docente):
    dados = await request.json()
    erros = _validar(dados, docente)
    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})
    return JSONResponse(content={"oficio": _oficio(dados, docente)})


@app.post("/solicitar/alunos")
async def solicitar_alunos(request: Request):
    return await _solicitar(request, False)


@app.post("/solicitar/docentes")
async def solicitar_docentes(request: Request):
    return await _solicitar(request, True)


@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse("app.js", media_type="application/javascript")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
