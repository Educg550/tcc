import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    aba: str
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao_trabalho: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg_rnm: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


PREENCHA_TODOS = "Preencha todos os campos"
N_USP_NUMEROS = "N. USP deve conter apenas números"
AGENCIA_NUMEROS = "Número da agência deve conter apenas números"
VALOR_MAIOR_QUE_ZERO = "Valor solicitado deve ser maior que 0"
EMAIL_INVALIDO = "E-mail inválido"
CPF_FORMATO = "CPF deve estar no formato 000.000.000-00"
CPF_INVALIDO = "CPF inválido"
CEP_FORMATO = "CEP deve estar no formato 00000-000"
DATA_FORMATO = "Data de nascimento deve estar no formato dd/mm/aaaa"
DATA_INVALIDA = "Data de nascimento inválida"

OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg_rnm", "banco", "agencia", "conta",
)

CPF_RE = re.compile(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}")
CEP_RE = re.compile(r"[0-9]{5}-[0-9]{3}")
DATA_RE = re.compile(r"[0-9]{2}/[0-9]{2}/[0-9]{4}")
VALOR_RE = re.compile(r"[0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}")


def _so_digitos(valor: str) -> bool:
    return re.fullmatch(r"[0-9]+", valor) is not None


def _email_valido(email: str) -> bool:
    _, arroba, dominio = email.rpartition("@")
    return bool(arroba and dominio)


def _valor_valido(valor: str) -> bool:
    texto = valor.strip()
    if texto.startswith("R$"):
        texto = texto[2:].strip()
    if VALOR_RE.fullmatch(texto):
        return int(texto.replace(".", "").replace(",", "")) > 0
    return re.fullmatch(r"[0-9]+", texto) is not None and int(texto) > 0


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11:
        return False
    for i in (9, 10):
        soma = sum(d * peso for d, peso in zip(digitos[:i], range(i + 1, 1, -1)))
        resto = soma % 11
        if digitos[i] != (0 if resto < 2 else 11 - resto):
            return False
    return True


def _data_existe(data: str) -> bool:
    try:
        datetime.date(int(data[6:10]), int(data[3:5]), int(data[0:2]))
    except ValueError:
        return False
    return True


def _validar(dados: Solicitacao) -> list[str]:
    erros: list[str] = []
    obrigatorios = list(OBRIGATORIOS)
    if dados.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not getattr(dados, campo) for campo in obrigatorios):
        erros.append(PREENCHA_TODOS)
    if dados.n_usp and not _so_digitos(dados.n_usp):
        erros.append(N_USP_NUMEROS)
    if dados.agencia and not _so_digitos(dados.agencia):
        erros.append(AGENCIA_NUMEROS)
    if dados.valor_solicitado and not _valor_valido(dados.valor_solicitado):
        erros.append(VALOR_MAIOR_QUE_ZERO)
    if dados.email and not _email_valido(dados.email):
        erros.append(EMAIL_INVALIDO)
    if dados.cpf:
        if not CPF_RE.fullmatch(dados.cpf):
            erros.append(CPF_FORMATO)
        elif not _cpf_valido(dados.cpf):
            erros.append(CPF_INVALIDO)
    if dados.cep and not CEP_RE.fullmatch(dados.cep):
        erros.append(CEP_FORMATO)
    if dados.data_nascimento:
        if not DATA_RE.fullmatch(dados.data_nascimento):
            erros.append(DATA_FORMATO)
        elif not _data_existe(dados.data_nascimento):
            erros.append(DATA_INVALIDA)
    return erros


def _oficio(dados: Solicitacao) -> str:
    if dados.aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}"
        programa = f"Programa: {dados.programa} - {dados.nivel}"
    linhas = [
        f"Interessada(o): {dados.nome_completo} - {dados.n_usp}",
        f"E-mail: {dados.email}",
        assunto,
        programa,
        "",
        f"A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.nome_evento}",
        f"Período: {dados.periodo_evento}",
        f"Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}",
    ]
    if dados.link_evento:
        linhas.append(f"Link do evento: {dados.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {dados.apresentacao_trabalho}",
        f"Valor solicitado: {dados.valor_solicitado}",
        f"Detalhamento: {dados.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.logradouro}, {dados.numero}",
    ]
    if dados.complemento:
        linhas.append(f"Complemento: {dados.complemento}")
    linhas += [
        f"CEP: {dados.cep}",
        f"{dados.bairro}, {dados.cidade} - {dados.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.data_nascimento}",
        f"CPF: {dados.cpf}",
        f"RG / RNM: {dados.rg_rnm}",
        f"Banco: {dados.banco}",
        f"Agência: {dados.agencia}",
        f"Conta: {dados.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def pagina() -> FileResponse:
    return FileResponse(RAIZ / "index.html", media_type="text/html")


@app.get("/style.css")
def estilo() -> FileResponse:
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def aplicacao() -> FileResponse:
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


@app.get("/assets/usp-logo.png")
def logo() -> FileResponse:
    return FileResponse(RAIZ / "assets" / "usp-logo.png", media_type="image/png")


@app.post("/solicitacao")
def solicitar(dados: Solicitacao) -> dict:
    erros = _validar(dados)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": _oficio(dados)}
