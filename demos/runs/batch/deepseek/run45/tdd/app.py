import html
import os
import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CAMPOS_COMUNS = [
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
    "banco",
    "agencia",
    "conta",
]

CAMPOS_ALUNOS = ["nivel", "tipo_auxilio"]

app = FastAPI()

app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(BASE_DIR, "assets"), check_dir=False),
    name="assets",
)


@app.get("/")
def pagina_inicial():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/style.css")
def estilos():
    return FileResponse(os.path.join(BASE_DIR, "style.css"), media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(os.path.join(BASE_DIR, "app.js"), media_type="application/javascript")


def _apenas_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def _formata_moeda(digitos):
    reais, centavos = divmod(int(digitos), 100)
    return "R$ {},{:02d}".format(f"{reais:,}".replace(",", "."), centavos)


def _formata_cpf(digitos):
    return "{}.{}.{}-{}".format(digitos[:3], digitos[3:6], digitos[6:9], digitos[9:])


def _formata_cep(digitos):
    return "{}-{}".format(digitos[:5], digitos[5:])


def _formata_data(digitos):
    return "{}/{}/{}".format(digitos[:2], digitos[2:4], digitos[4:])


def _cpf_valido(digitos):
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    numeros = [int(c) for c in digitos]
    for i in (9, 10):
        soma = sum(numeros[j] * (i + 1 - j) for j in range(i))
        verificador = (soma * 10) % 11
        if verificador == 10:
            verificador = 0
        if verificador != numeros[i]:
            return False
    return True


def _data_valida(digitos):
    try:
        date(int(digitos[4:8]), int(digitos[2:4]), int(digitos[0:2]))
        return True
    except ValueError:
        return False


def _validar(dados, obrigatorios):
    erros = []

    if any(dados[campo] == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if dados["n_usp"] and not dados["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")

    if dados["agencia"] and not dados["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor_digitos = _apenas_digitos(dados["valor_solicitado"])
    if dados["valor_solicitado"] and (not valor_digitos or int(valor_digitos) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if dados["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", dados["email"]):
        erros.append("E-mail inválido")

    if dados["cpf"]:
        formato_cpf = re.fullmatch(r"\d{11}", dados["cpf"]) or re.fullmatch(
            r"\d{3}\.\d{3}\.\d{3}-\d{2}", dados["cpf"]
        )
        if not formato_cpf:
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(_apenas_digitos(dados["cpf"])):
            erros.append("CPF inválido")

    if dados["cep"] and not (
        re.fullmatch(r"\d{8}", dados["cep"]) or re.fullmatch(r"\d{5}-\d{3}", dados["cep"])
    ):
        erros.append("CEP deve estar no formato 00000-000")

    if dados["data_nascimento"]:
        formato_data = re.fullmatch(r"\d{8}", dados["data_nascimento"]) or re.fullmatch(
            r"\d{2}/\d{2}/\d{4}", dados["data_nascimento"]
        )
        if not formato_data:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(_apenas_digitos(dados["data_nascimento"])):
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados, docente):
    valor = _formata_moeda(_apenas_digitos(dados["valor_solicitado"]))
    cpf = _formata_cpf(_apenas_digitos(dados["cpf"]))
    cep = _formata_cep(_apenas_digitos(dados["cep"]))
    nascimento = _formata_data(_apenas_digitos(dados["data_nascimento"]))

    linhas = [
        "Interessada(o): {} - {}".format(dados["nome_completo"], dados["n_usp"]),
        "E-mail: {}".format(dados["email"]),
    ]
    if docente:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(dados["programa"]))
    else:
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - {}".format(dados["tipo_auxilio"])
        )
        linhas.append("Programa: {} - {}".format(dados["programa"], dados["nivel"]))

    linhas += [
        "",
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            dados["programa"]
        ),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: {}".format(dados["nome_evento"]),
        "Período: {}".format(dados["periodo_evento"]),
        "Local: {} - {} - {}".format(
            dados["cidade_evento"], dados["estado_evento"], dados["pais_evento"]
        ),
    ]
    if dados["link_evento"]:
        linhas.append("Link do evento: {}".format(dados["link_evento"]))
    linhas += [
        "Apresentação de trabalho: {}".format(dados["apresentacao"]),
        "Valor solicitado: {}".format(valor),
        "Detalhamento: {}".format(dados["detalhamento"]),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(dados["logradouro"], dados["numero"]),
    ]
    if dados["complemento"]:
        linhas.append("Complemento: {}".format(dados["complemento"]))
    linhas += [
        "CEP: {}".format(cep),
        "{}, {} - {}".format(dados["bairro"], dados["cidade"], dados["estado"]),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(nascimento),
        "CPF: {}".format(cpf),
        "RG / RNM: {}".format(dados["rg"]),
        "Banco: {}".format(dados["banco"]),
        "Agência: {}".format(dados["agencia"]),
        "Conta: {}".format(dados["conta"]),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    oficio = html.escape("\n".join(linhas))
    return (
        '<section class="confirmacao"><h2>Solicitação registrada</h2>'
        '<pre class="oficio">{}</pre></section>'.format(oficio)
    )


def _processar(form, docente):
    obrigatorios = CAMPOS_COMUNS + ([] if docente else CAMPOS_ALUNOS)
    dados = {campo: (form.get(campo) or "").strip() for campo in obrigatorios}
    dados["link_evento"] = (form.get("link_evento") or "").strip()
    dados["complemento"] = (form.get("complemento") or "").strip()

    erros = _validar(dados, obrigatorios)
    if erros:
        return HTMLResponse("".join("<p>{}</p>".format(html.escape(e)) for e in erros))
    return HTMLResponse(_oficio(dados, docente))


@app.post("/solicitar/alunos")
async def solicitar_alunos(request: Request):
    form = await request.form()
    return _processar(form, docente=False)


@app.post("/solicitar/docentes")
async def solicitar_docentes(request: Request):
    form = await request.form()
    return _processar(form, docente=True)
