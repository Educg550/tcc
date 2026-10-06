import re
import unicodedata
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

CAMPOS = [
    ("nome_completo", "NOME COMPLETO - SEM ABREVIAR"),
    ("n_usp", "N. USP"),
    ("programa", "PROGRAMA"),
    ("nivel", "NÍVEL"),
    ("tipo_auxilio", "TIPO DE AUXÍLIO"),
    ("email", "E-MAIL"),
    ("nome_evento", "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"),
    ("periodo", "PERÍODO DO EVENTO, EXAME OU DEFESA"),
    ("cidade_evento", "CIDADE DO EVENTO, EXAME OU DEFESA"),
    ("estado_evento", "ESTADO DO EVENTO, EXAME OU DEFESA"),
    ("pais_evento", "PAÍS DO EVENTO, EXAME OU DEFESA"),
    ("link_evento", "LINK DO EVENTO, EXAME OU DEFESA"),
    ("valor", "VALOR SOLICITADO (R$)"),
    ("detalhamento", "DETALHAMENTO DO PEDIDO"),
    ("apresentacao", "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"),
    ("data_nascimento", "DATA DE NASCIMENTO"),
    ("logradouro", "LOGRADOURO"),
    ("numero", "NÚMERO"),
    ("complemento", "COMPLEMENTO"),
    ("bairro", "BAIRRO"),
    ("cep", "CEP"),
    ("cidade", "CIDADE"),
    ("estado", "ESTADO"),
    ("cpf", "CPF (SEPARADOS POR PONTOS E TRAÇO)"),
    ("rg", "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"),
    ("banco", "NOME DO BANCO"),
    ("agencia", "NÚMERO DA AGÊNCIA"),
    ("conta", "NÚMERO DA CONTA"),
]

OPCIONAIS = {"link_evento", "complemento"}


def normalizar(texto):
    """Chave de comparação tolerante a acentos, maiúsculas e pontuação."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]", "", texto).upper()


APELIDOS = {}
for _chave, _rotulo in CAMPOS:
    APELIDOS[normalizar(_chave)] = _chave
    APELIDOS[normalizar(_rotulo)] = _chave


def cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"[^0-9]", "", cpf)]
    for peso in (10, 11):
        soma = sum(d * (peso - i) for i, d in enumerate(digitos[: peso - 1]))
        if (soma * 10) % 11 % 10 != digitos[peso - 1]:
            return False
    return True


def data_existe(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formata_valor(centavos):
    reais, resto = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def validar(corpo, aba):
    dados = {chave: "" for chave, _ in CAMPOS}
    for chave, valor in corpo.items():
        campo = APELIDOS.get(normalizar(chave))
        if campo:
            dados[campo] = str(valor).strip()

    if aba == "alunos":
        obrigatorios = [c for c, _ in CAMPOS if c not in OPCIONAIS]
    else:
        obrigatorios = [c for c, _ in CAMPOS
                        if c not in OPCIONAIS and c not in ("nivel", "tipo_auxilio")]

    erros = []
    if any(not dados[c] for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if dados["n_usp"] and not re.fullmatch(r"[0-9]+", dados["n_usp"]):
        erros.append("N. USP deve conter apenas números")

    if dados["agencia"] and not re.fullmatch(r"[0-9]+", dados["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    centavos = int(re.sub(r"[^0-9]", "", dados["valor"]) or 0)
    if dados["valor"] and centavos <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    if dados["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", dados["email"]):
        erros.append("E-mail inválido")

    cpf_formatado = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", dados["cpf"]))
    if dados["cpf"] and not cpf_formatado:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if dados["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    data_formatada = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", dados["data_nascimento"]))
    if dados["data_nascimento"] and not data_formatada:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formatado and not cpf_valido(dados["cpf"]):
        erros.append("CPF inválido")

    if data_formatada and not data_existe(dados["data_nascimento"]):
        erros.append("Data de nascimento inválida")

    return dados, erros, centavos


def gerar_oficio(dados, aba, centavos):
    if aba == "alunos":
        assunto = "Solicitação de Auxílio Financeiro - " + dados["tipo_auxilio"]
        programa = dados["programa"] + " - " + dados["nivel"]
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = dados["programa"]

    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link_evento"]:
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {formata_valor(centavos)}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    if "json" in request.headers.get("content-type", ""):
        corpo = await request.json()
    else:
        corpo = dict(await request.form())
    if not isinstance(corpo, dict):
        corpo = {}

    aba = "alunos"
    for chave, valor in corpo.items():
        if normalizar(chave) in ("ABA", "FORMULARIO"):
            aba = "docentes" if normalizar(valor).startswith("DOCENTE") else "alunos"

    dados, erros, centavos = validar(corpo, aba)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": gerar_oficio(dados, aba, centavos)})


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets", check_dir=False))
