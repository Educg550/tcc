import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")

OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "evento_nome", "evento_periodo",
    "evento_cidade", "evento_estado", "evento_pais", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
)


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


def _texto(dados, campo):
    return str(dados.get(campo, "")).strip()


def _parse_valor(valor):
    limpo = re.sub(r"[^0-9,.]", "", valor).replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(digitos[j] * (i + 1 - j) for j in range(i))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if digitos[i] != esperado:
            return False
    return True


def _data_existente(valor):
    dia, mes, ano = valor.split("/")
    try:
        date(int(ano), int(mes), int(dia))
    except ValueError:
        return False
    return True


def validar(dados):
    aba = dados.get("aba", "alunos")
    campos = list(OBRIGATORIOS)
    if aba != "docentes":
        campos += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not _texto(dados, campo) for campo in campos):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor")
    if valor and (_parse_valor(valor) or 0) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = _texto(dados, "data_nascimento")
    if nascimento:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_existente(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados):
    programa = _texto(dados, "programa")
    if dados.get("aba") == "docentes":
        assunto = "Verba do programa"
        linha_programa = f"Programa: {programa}"
    else:
        assunto = _texto(dados, "tipo_auxilio")
        linha_programa = f"Programa: {programa} - {_texto(dados, 'nivel')}"

    linhas = [
        f"Interessada(o): {_texto(dados, 'nome_completo')} - {_texto(dados, 'n_usp')}",
        f"E-mail: {_texto(dados, 'email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados, 'evento_nome')}",
        f"Período: {_texto(dados, 'evento_periodo')}",
        f"Local: {_texto(dados, 'evento_cidade')} - {_texto(dados, 'evento_estado')} - {_texto(dados, 'evento_pais')}",
    ]

    link = _texto(dados, "evento_link")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {_texto(dados, 'apresentacao')}",
        f"Valor solicitado: {_texto(dados, 'valor')}",
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
        f"Banco: {_texto(dados, 'banco')}",
        f"Agência: {_texto(dados, 'agencia')}",
        f"Conta: {_texto(dados, 'conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitar(request: Request):
    dados = await request.json()
    erros = validar(dados)
    if erros:
        return PlainTextResponse("\n".join(erros), status_code=400)
    return PlainTextResponse(_oficio(dados))
