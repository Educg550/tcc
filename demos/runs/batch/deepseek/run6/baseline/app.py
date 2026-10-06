"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
import unicodedata
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

# --------------------------------------------------------------------- campos

LABELS = {
    "nome": "NOME COMPLETO - SEM ABREVIAR",
    "n_usp": "N. USP",
    "programa": "PROGRAMA",
    "nivel": "NÍVEL",
    "tipo_auxilio": "TIPO DE AUXÍLIO",
    "email": "E-MAIL",
    "evento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "periodo": "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "cidade_evento": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "estado_evento": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "pais": "PAÍS DO EVENTO, EXAME OU DEFESA",
    "link": "LINK DO EVENTO, EXAME OU DEFESA",
    "valor": "VALOR SOLICITADO (R$)",
    "detalhamento": "DETALHAMENTO DO PEDIDO",
    "apresentacao": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "nascimento": "DATA DE NASCIMENTO",
    "logradouro": "LOGRADOURO",
    "numero": "NÚMERO",
    "complemento": "COMPLEMENTO",
    "bairro": "BAIRRO",
    "cep": "CEP",
    "cidade": "CIDADE",
    "estado": "ESTADO",
    "cpf": "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "rg": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "banco": "NOME DO BANCO",
    "agencia": "NÚMERO DA AGÊNCIA",
    "conta": "NÚMERO DA CONTA",
}

OPCIONAIS = {"link", "complemento"}

EXTRAS = {
    "n_usp": ["nusp", "numerousp"],
    "tipo_auxilio": ["tipoauxilio"],
    "cidade_evento": ["cidadeevento"],
    "estado_evento": ["estadoevento"],
    "pais": ["paisevento"],
    "link": ["linkevento"],
    "valor": ["valorsolicitado"],
    "apresentacao": ["apresentacaotrabalho", "iraapresentartrabalho"],
    "nascimento": ["datanascimento"],
    "cidade": ["cidadesolicitante"],
    "estado": ["estadosolicitante"],
    "rg": ["rgrnm"],
    "banco": ["nomebanco"],
    "agencia": ["numerodaagencia"],
    "conta": ["numerodaconta"],
}


def _chave(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto.lower())


MAPA = {}
for _campo, _label in LABELS.items():
    MAPA[_chave(_label)] = _campo
    MAPA[_chave(_campo)] = _campo
for _campo, _apelidos in EXTRAS.items():
    for _apelido in _apelidos:
        MAPA.setdefault(_chave(_apelido), _campo)

RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


# ------------------------------------------------------------------ validação

def so_digitos(texto):
    return re.sub(r"\D", "", texto)


def valor_em_centavos(texto):
    """Devolve o valor em centavos, ou None se não for um número."""
    texto = texto.strip()
    if not texto:
        return None
    if "," in texto or "R$" in texto:
        limpo = re.sub(r"[^0-9,]", "", texto).replace(",", ".")
        try:
            return int(round(float(limpo) * 100))
        except ValueError:
            return None
    return int(texto) if texto.isdigit() else None


def formatar_moeda(centavos):
    reais, resto = divmod(int(centavos), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def email_valido(texto):
    return RE_EMAIL.fullmatch(texto) is not None


def cpf_valido(texto):
    digitos = so_digitos(texto)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[n]) * (i + 1 - n) for n in range(i))
        if (soma * 10) % 11 % 10 != int(digitos[i]):
            return False
    return True


def data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def extrair(corpo):
    dados = {campo: "" for campo in LABELS}
    for chave, valor in corpo.items():
        campo = MAPA.get(_chave(chave))
        if campo is not None:
            dados[campo] = str(valor).strip()
    return dados


def validar(aba, dados):
    campos = [c for c in LABELS if c not in OPCIONAIS]
    if aba == "docentes":
        campos = [c for c in campos if c not in ("nivel", "tipo_auxilio")]

    erros = []
    if any(not dados[c] for c in campos):
        erros.append("Preencha todos os campos")
    if dados["n_usp"] and not dados["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if dados["agencia"] and not dados["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    if dados["valor"]:
        centavos = valor_em_centavos(dados["valor"])
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if dados["email"] and not email_valido(dados["email"]):
        erros.append("E-mail inválido")
    if dados["cpf"] and not RE_CPF.match(dados["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    if dados["cep"] and not RE_CEP.match(dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if dados["nascimento"] and not RE_DATA.match(dados["nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if dados["cpf"] and RE_CPF.match(dados["cpf"]) and not cpf_valido(dados["cpf"]):
        erros.append("CPF inválido")
    if dados["nascimento"] and RE_DATA.match(dados["nascimento"]) and not data_valida(dados["nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(aba, dados, valor_formatado):
    if aba == "docentes":
        assunto = "Verba do programa"
        programa = dados["programa"]
    else:
        assunto = dados["tipo_auxilio"]
        programa = dados["programa"] + " - " + dados["nivel"]

    linhas = [
        "Interessada(o): " + dados["nome"] + " - " + dados["n_usp"],
        "E-mail: " + dados["email"],
        "Assunto: Solicitação de Auxílio Financeiro - " + assunto,
        "Programa: " + programa,
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + dados["evento"],
        "Período: " + dados["periodo"],
        "Local: " + dados["cidade_evento"] + " - " + dados["estado_evento"] + " - " + dados["pais"],
    ]
    if dados["link"]:
        linhas.append("Link do evento: " + dados["link"])
    linhas += [
        "Apresentação de trabalho: " + dados["apresentacao"],
        "Valor solicitado: " + valor_formatado,
        "Detalhamento: " + dados["detalhamento"],
        "",
        "Endereço da(o) interessada(o)",
        dados["logradouro"] + ", " + dados["numero"],
    ]
    if dados["complemento"]:
        linhas.append("Complemento: " + dados["complemento"])
    linhas += [
        "CEP: " + dados["cep"],
        dados["bairro"] + ", " + dados["cidade"] + " - " + dados["estado"],
        "",
        "Dados para pagamento",
        "Data de nascimento: " + dados["nascimento"],
        "CPF: " + dados["cpf"],
        "RG / RNM: " + dados["rg"],
        "Banco: " + dados["banco"],
        "Agência: " + dados["agencia"],
        "Conta: " + dados["conta"],
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


# --------------------------------------------------------------------- rotas

@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


if (BASE / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    if "application/json" in request.headers.get("content-type", ""):
        corpo = await request.json()
    else:
        corpo = dict(await request.form())

    aba = "docentes" if "doc" in _chave(corpo.get("aba", "")) else "alunos"
    dados = extrair(corpo)

    erros = validar(aba, dados)
    if erros:
        return {"ok": False, "erros": erros}

    centavos = valor_em_centavos(dados["valor"])
    return {"ok": True, "oficio": gerar_oficio(aba, dados, formatar_moeda(centavos))}
