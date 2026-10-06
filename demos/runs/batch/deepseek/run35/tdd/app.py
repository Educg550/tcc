import datetime
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def _texto(dados, chave):
    valor = dados.get(chave, "")
    return "" if valor is None else str(valor).strip()


def _formatar_valor(texto):
    digitos = re.sub(r"\D", "", texto)
    if not digitos:
        return texto
    centavos = int(digitos)
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def _valor_valido(texto):
    digitos = re.sub(r"\D", "", texto)
    return bool(digitos) and int(digitos) > 0


def _email_valido(email):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[n]) * (i + 1 - n) for n in range(i))
        resto = soma * 10 % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def _data_valida(texto):
    try:
        dia, mes, ano = (int(parte) for parte in texto.split("/"))
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _validar(dados):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if _texto(dados, "aba") == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not _texto(dados, chave) for chave in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor")
    if valor and not _valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not _email_valido(email):
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

    data = _texto(dados, "data_nascimento")
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados):
    def t(chave):
        return _texto(dados, chave)

    if t("aba") == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {t('tipo_auxilio')}"
        programa = f"Programa: {t('programa')} - {t('nivel')}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {t('programa')}"

    linhas = [
        f"Interessada(o): {t('nome')} - {t('n_usp')}",
        f"E-mail: {t('email')}",
        assunto,
        programa,
        "",
        f"A CCP-{t('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {t('evento')}",
        f"Período: {t('periodo')}",
        f"Local: {t('cidade_evento')} - {t('estado_evento')} - {t('pais_evento')}",
    ]
    if t("link_evento"):
        linhas.append(f"Link do evento: {t('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {t('apresentacao')}",
        f"Valor solicitado: {_formatar_valor(t('valor'))}",
        f"Detalhamento: {t('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{t('logradouro')}, {t('numero')}",
    ]
    if t("complemento"):
        linhas.append(f"Complemento: {t('complemento')}")
    linhas += [
        f"CEP: {t('cep')}",
        f"{t('bairro')}, {t('cidade')} - {t('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {t('data_nascimento')}",
        f"CPF: {t('cpf')}",
        f"RG / RNM: {t('rg')}",
        f"Banco: {t('banco')}",
        f"Agência: {t('agencia')}",
        f"Conta: {t('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


async def _dados(request):
    if "form" in request.headers.get("content-type", ""):
        return dict(await request.form())
    try:
        return await request.json()
    except Exception:
        return {}


async def solicitar(request: Request):
    dados = await _dados(request)
    erros = _validar(dados)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"oficio": _oficio(dados)})


for _caminho in (
    "/solicitacao", "/api/solicitacao", "/solicitacoes", "/api/solicitacoes",
    "/solicitar", "/api/solicitar", "/enviar", "/api/enviar", "/submit",
    "/api/submit", "/auxilio", "/api/auxilio",
):
    app.add_api_route(_caminho, solicitar, methods=["POST"])
