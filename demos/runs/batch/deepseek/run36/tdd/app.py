"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import json
import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

ALIASES = {
    "aba": ("aba", "tipo_formulario", "formulario", "publico"),
    "nome": ("nome_completo", "nome_completo_sem_abreviar", "nomeCompleto", "nome"),
    "n_usp": ("n_usp", "nusp", "numero_usp", "numero_do_usp", "num_usp"),
    "programa": ("programa",),
    "nivel": ("nivel", "nível"),
    "tipo_auxilio": ("tipo_de_auxilio", "tipo_auxilio"),
    "email": ("email", "e_mail", "e-mail"),
    "evento": ("nome_do_evento", "nome_evento", "evento"),
    "periodo": ("periodo", "periodo_do_evento", "período", "periodo_evento"),
    "cidade_evento": ("cidade_do_evento", "cidade_evento"),
    "estado_evento": ("estado_do_evento", "estado_evento"),
    "pais_evento": ("pais_do_evento", "pais_evento", "país_do_evento", "pais"),
    "link_evento": ("link_do_evento", "link_evento", "link"),
    "valor": ("valor_solicitado", "valor"),
    "detalhamento": ("detalhamento", "detalhamento_do_pedido"),
    "apresentacao": (
        "ira_apresentar_trabalho",
        "apresentar_trabalho",
        "tipo_apresentacao",
    ),
    "nascimento": ("data_de_nascimento", "data_nascimento", "nascimento"),
    "logradouro": ("logradouro",),
    "numero": ("numero", "número", "num"),
    "complemento": ("complemento",),
    "bairro": ("bairro",),
    "cep": ("cep",),
    "cidade": ("cidade",),
    "estado": ("estado",),
    "cpf": ("cpf",),
    "rg": ("rg", "rnm", "rg_rnm"),
    "banco": ("banco", "nome_do_banco"),
    "agencia": (
        "agencia",
        "agência",
        "numero_da_agencia",
        "numero_agencia",
        "n_agencia",
    ),
    "conta": ("conta", "numero_da_conta", "numero_conta"),
}

REQUERIDOS = [
    "nome",
    "n_usp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
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

SO_DOCENTES = ("nivel", "tipo_auxilio")


def _pega(dados, aliases):
    for alias in aliases:
        valor = dados.get(alias)
        if valor not in (None, ""):
            return str(valor).strip()
    return ""


def _cpf_valido(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    if len(numeros) != 11:
        return False
    for tamanho in (9, 10):
        soma = sum(numeros[i] * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[tamanho]:
            return False
    return True


def _valida(v, docentes):
    erros = []

    requeridos = [
        campo for campo in REQUERIDOS if not (docentes and campo in SO_DOCENTES)
    ]
    if any(not v[campo] for campo in requeridos):
        erros.append("Preencha todos os campos")

    if v["n_usp"] and not re.fullmatch(r"\d+", v["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if v["agencia"] and not re.fullmatch(r"\d+", v["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    if v["valor"]:
        digitos = re.sub(r"\D", "", v["valor"])
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if v["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v["email"]):
        erros.append("E-mail inválido")

    cpf = v["cpf"]
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    if v["cep"] and not re.fullmatch(r"\d{5}-\d{3}", v["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = v["nascimento"]
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = nascimento.split("/")
            try:
                date(int(ano), int(mes), int(dia))
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _oficio(v, docentes):
    linhas = []
    linhas.append("Interessada(o): {} - {}".format(v["nome"], v["n_usp"]))
    linhas.append("E-mail: {}".format(v["email"]))
    if docentes:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(v["programa"]))
    else:
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - {}".format(v["tipo_auxilio"])
        )
        linhas.append("Programa: {} - {}".format(v["programa"], v["nivel"]))

    linhas.append("")
    linhas.append(
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            v["programa"]
        )
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")

    linhas.append("Dados do evento")
    linhas.append("Evento: {}".format(v["evento"]))
    linhas.append("Período: {}".format(v["periodo"]))
    linhas.append(
        "Local: {} - {} - {}".format(
            v["cidade_evento"], v["estado_evento"], v["pais_evento"]
        )
    )
    if v["link_evento"]:
        linhas.append("Link do evento: {}".format(v["link_evento"]))
    linhas.append("Apresentação de trabalho: {}".format(v["apresentacao"]))
    linhas.append("Valor solicitado: {}".format(v["valor"]))
    linhas.append("Detalhamento: {}".format(v["detalhamento"]))
    linhas.append("")

    linhas.append("Endereço da(o) interessada(o)")
    linhas.append("{}, {}".format(v["logradouro"], v["numero"]))
    if v["complemento"]:
        linhas.append("Complemento: {}".format(v["complemento"]))
    linhas.append("CEP: {}".format(v["cep"]))
    linhas.append("{}, {} - {}".format(v["bairro"], v["cidade"], v["estado"]))
    linhas.append("")

    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: {}".format(v["nascimento"]))
    linhas.append("CPF: {}".format(v["cpf"]))
    linhas.append("RG / RNM: {}".format(v["rg"]))
    linhas.append("Banco: {}".format(v["banco"]))
    linhas.append("Agência: {}".format(v["agencia"]))
    linhas.append("Conta: {}".format(v["conta"]))
    linhas.append("")

    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


def _json(payload):
    return Response(
        content=json.dumps(payload, ensure_ascii=False),
        media_type="application/json; charset=utf-8",
    )


@app.post("/solicitacao")
async def solicitar(request: Request):
    dados = await request.json()
    if not isinstance(dados, dict):
        dados = {}

    valores = {campo: _pega(dados, aliases) for campo, aliases in ALIASES.items()}
    docentes = valores["aba"].strip().lower() == "docentes"

    erros = _valida(valores, docentes)
    if erros:
        return _json({"ok": False, "erros": erros})

    return _json({"ok": True, "oficio": _oficio(valores, docentes)})


@app.get("/")
async def raiz():
    return HTMLResponse((BASE / "index.html").read_text(encoding="utf-8"))


@app.get("/style.css")
async def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css; charset=utf-8")


@app.get("/app.js")
async def script():
    return FileResponse(
        BASE / "app.js", media_type="application/javascript; charset=utf-8"
    )


app.mount("/assets", StaticFiles(directory=str(BASE / "assets")), name="assets")
