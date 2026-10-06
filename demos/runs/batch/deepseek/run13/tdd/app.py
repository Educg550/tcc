"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

OBRIGATORIOS = [
    "nome",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor",
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


# --------------------------------------------------------------------------- validação


def _valor_em_reais(texto):
    t = texto.strip().replace("R$", "").strip()
    if not t:
        return 0.0
    if "," in t:
        try:
            return float(t.replace(".", "").replace(",", "."))
        except ValueError:
            return None
    if re.fullmatch(r"[0-9]+", t):
        return int(t) / 100
    return None


def _cpf_confere(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * ((i + 1) - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != digitos[i]:
            return False
    return True


def validar(d):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if d["aba"] != "DOCENTES":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not d[c].strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = d["n_usp"].strip()
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = d["agencia"].strip()
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = d["valor"].strip()
    if valor:
        reais = _valor_em_reais(valor)
        if reais is None or reais <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = d["email"].strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = d["cpf"].strip()
    if cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_confere(cpf):
            erros.append("CPF inválido")

    cep = d["cep"].strip()
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = d["data_nascimento"].strip()
    if nascimento:
        partes = re.fullmatch(r"([0-9]{2})/([0-9]{2})/([0-9]{4})", nascimento)
        if not partes:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                date(int(partes.group(3)), int(partes.group(2)), int(partes.group(1)))
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


# ------------------------------------------------------------------------------ ofício


def montar_oficio(d):
    linhas = []
    linhas.append("Interessada(o): {} - {}".format(d["nome"], d["n_usp"]))
    linhas.append("E-mail: {}".format(d["email"]))
    if d["aba"] == "DOCENTES":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append("Programa: {}".format(d["programa"]))
    else:
        linhas.append(
            "Assunto: Solicitação de Auxílio Financeiro - {}".format(d["tipo_auxilio"])
        )
        linhas.append("Programa: {} - {}".format(d["programa"], d["nivel"]))
    linhas.append("")
    linhas.append(
        "A CCP-{} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(
            d["programa"]
        )
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append("Evento: {}".format(d["evento"]))
    linhas.append("Período: {}".format(d["periodo"]))
    linhas.append(
        "Local: {} - {} - {}".format(
            d["cidade_evento"], d["estado_evento"], d["pais_evento"]
        )
    )
    if d["link_evento"].strip():
        linhas.append("Link do evento: {}".format(d["link_evento"]))
    linhas.append("Apresentação de trabalho: {}".format(d["apresentacao"]))
    linhas.append("Valor solicitado: {}".format(d["valor"]))
    linhas.append("Detalhamento: {}".format(d["detalhamento"]))
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append("{}, {}".format(d["logradouro"], d["numero"]))
    if d["complemento"].strip():
        linhas.append("Complemento: {}".format(d["complemento"]))
    linhas.append("CEP: {}".format(d["cep"]))
    linhas.append("{}, {} - {}".format(d["bairro"], d["cidade"], d["estado"]))
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append("Data de nascimento: {}".format(d["data_nascimento"]))
    linhas.append("CPF: {}".format(d["cpf"]))
    linhas.append("RG / RNM: {}".format(d["rg"]))
    linhas.append("Banco: {}".format(d["banco"]))
    linhas.append("Agência: {}".format(d["agencia"]))
    linhas.append("Conta: {}".format(d["conta"]))
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


# ------------------------------------------------------------------------------ rotas


def _estatico(caminho, raiz):
    caminho = caminho.resolve()
    raiz = raiz.resolve()
    if raiz not in caminho.parents or not caminho.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(caminho)


@app.get("/", include_in_schema=False)
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css", include_in_schema=False)
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(BASE / "app.js")


@app.get("/assets/{nome}", include_in_schema=False)
def asset(nome: str):
    return _estatico(BASE / "assets" / nome, BASE / "assets")


@app.post("/solicitacao")
def solicitar(
    aba: str = Form(""),
    nome: str = Form(""),
    n_usp: str = Form(""),
    programa: str = Form(""),
    nivel: str = Form(""),
    tipo_auxilio: str = Form(""),
    email: str = Form(""),
    evento: str = Form(""),
    periodo: str = Form(""),
    cidade_evento: str = Form(""),
    estado_evento: str = Form(""),
    pais_evento: str = Form(""),
    link_evento: str = Form(""),
    valor: str = Form(""),
    detalhamento: str = Form(""),
    apresentacao: str = Form(""),
    data_nascimento: str = Form(""),
    logradouro: str = Form(""),
    numero: str = Form(""),
    complemento: str = Form(""),
    bairro: str = Form(""),
    cep: str = Form(""),
    cidade: str = Form(""),
    estado: str = Form(""),
    cpf: str = Form(""),
    rg: str = Form(""),
    banco: str = Form(""),
    agencia: str = Form(""),
    conta: str = Form(""),
):
    dados = {
        "aba": aba,
        "nome": nome,
        "n_usp": n_usp,
        "programa": programa,
        "nivel": nivel,
        "tipo_auxilio": tipo_auxilio,
        "email": email,
        "evento": evento,
        "periodo": periodo,
        "cidade_evento": cidade_evento,
        "estado_evento": estado_evento,
        "pais_evento": pais_evento,
        "link_evento": link_evento,
        "valor": valor,
        "detalhamento": detalhamento,
        "apresentacao": apresentacao,
        "data_nascimento": data_nascimento,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cep": cep,
        "cidade": cidade,
        "estado": estado,
        "cpf": cpf,
        "rg": rg,
        "banco": banco,
        "agencia": agencia,
        "conta": conta,
    }
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": montar_oficio(dados)}
