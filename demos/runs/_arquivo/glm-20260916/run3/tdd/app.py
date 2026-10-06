import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


@app.get("/")
def pagina_inicial():
    return FileResponse(RAIZ / "index.html", media_type="text/html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def roteiro():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


CAMPOS = (
    "nome_completo", "n_usp", "programa", "nivel", "tipo_de_auxilio", "email",
    "nome_do_evento", "periodo_do_evento", "cidade_do_evento", "estado_do_evento",
    "pais_do_evento", "link_do_evento", "valor_solicitado", "detalhamento",
    "apresentacao", "data_de_nascimento", "logradouro", "numero", "complemento",
    "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_do_banco",
    "numero_da_agencia", "numero_da_conta",
)
OPCIONAIS = {"link_do_evento", "complemento"}
CAMPOS_DE_DOCENTE = ("nivel", "tipo_de_auxilio")


def _valor_valido(texto):
    numero = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(numero) > 0
    except ValueError:
        return False


def _email_valido(texto):
    _, arroba, dominio = texto.partition("@")
    return arroba == "@" and dominio != ""


def _cpf_valido(texto):
    digitos = [int(caractere) for caractere in texto if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    resto = sum(digitos[i] * (10 - i) for i in range(9)) % 11
    digito1 = 0 if resto < 2 else 11 - resto
    resto = sum(digitos[i] * (11 - i) for i in range(10)) % 11
    digito2 = 0 if resto < 2 else 11 - resto
    return digitos[9] == digito1 and digitos[10] == digito2


def _data_valida(texto):
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _mensagens_de_erro(dados):
    docente = dados.get("aba") == "docentes"
    valor = {campo: str(dados.get(campo, "")).strip() for campo in CAMPOS}
    obrigatorios = [
        campo
        for campo in CAMPOS
        if campo not in OPCIONAIS and not (docente and campo in CAMPOS_DE_DOCENTE)
    ]
    mensagens = []
    if any(not valor[campo] for campo in obrigatorios):
        mensagens.append("Preencha todos os campos")
    if valor["n_usp"] and not re.fullmatch(r"[0-9]+", valor["n_usp"]):
        mensagens.append("N. USP deve conter apenas números")
    if valor["numero_da_agencia"] and not re.fullmatch(r"[0-9]+", valor["numero_da_agencia"]):
        mensagens.append("Número da agência deve conter apenas números")
    if valor["valor_solicitado"] and not _valor_valido(valor["valor_solicitado"]):
        mensagens.append("Valor solicitado deve ser maior que 0")
    if valor["email"] and not _email_valido(valor["email"]):
        mensagens.append("E-mail inválido")
    if valor["cpf"] and not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", valor["cpf"]):
        mensagens.append("CPF deve estar no formato 000.000.000-00")
    elif valor["cpf"] and not _cpf_valido(valor["cpf"]):
        mensagens.append("CPF inválido")
    if valor["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", valor["cep"]):
        mensagens.append("CEP deve estar no formato 00000-000")
    if valor["data_de_nascimento"]:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", valor["data_de_nascimento"]):
            mensagens.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(valor["data_de_nascimento"]):
            mensagens.append("Data de nascimento inválida")
    return mensagens


def _oficio(dados):
    def campo(nome):
        return str(dados.get(nome, "")).strip()

    docente = dados.get("aba") == "docentes"
    if docente:
        assunto = "Verba do programa"
        programa = campo("programa")
    else:
        assunto = campo("tipo_de_auxilio")
        programa = f"{campo('programa')} - {campo('nivel')}"
    linhas = [
        f"Interessada(o): {campo('nome_completo')} - {campo('n_usp')}",
        f"E-mail: {campo('email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{campo('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campo('nome_do_evento')}",
        f"Período: {campo('periodo_do_evento')}",
        f"Local: {campo('cidade_do_evento')} - {campo('estado_do_evento')} - {campo('pais_do_evento')}",
    ]
    if campo("link_do_evento"):
        linhas.append(f"Link do evento: {campo('link_do_evento')}")
    linhas += [
        f"Apresentação de trabalho: {campo('apresentacao')}",
        f"Valor solicitado: {campo('valor_solicitado')}",
        f"Detalhamento: {campo('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('logradouro')}, {campo('numero')}",
    ]
    if campo("complemento"):
        linhas.append(f"Complemento: {campo('complemento')}")
    linhas += [
        f"CEP: {campo('cep')}",
        f"{campo('bairro')}, {campo('cidade')} - {campo('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {campo('data_de_nascimento')}",
        f"CPF: {campo('cpf')}",
        f"RG / RNM: {campo('rg_rnm')}",
        f"Banco: {campo('nome_do_banco')}",
        f"Agência: {campo('numero_da_agencia')}",
        f"Conta: {campo('numero_da_conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
@app.post("/solicitacoes")
@app.post("/api/solicitacao")
@app.post("/api/solicitacoes")
@app.post("/solicitar")
async def registrar_solicitacao(request: Request):
    try:
        dados = await request.()
    except Exception:
        try:
            dados = dict(await request.form())
        except Exception:
            dados = {}
    if not isinstance(dados, dict):
        dados = {}
    mensagens = _mensagens_de_erro(dados)
    if mensagens:
        return JSONResponse({"erros": mensagens})
    return JSONResponse({"oficio": _oficio(dados)})
