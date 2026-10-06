import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
    "pais_evento", "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg_rnm", "nome_banco", "agencia", "conta",
]

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str
    campos: dict[str, str]


def digitos_verificadores_cpf(cpf: str) -> bool:
    d = [int(caractere) for caractere in cpf]
    soma1 = sum(d[i] * (10 - i) for i in range(9))
    if (soma1 * 10) % 11 % 10 != d[9]:
        return False
    soma2 = sum(d[i] * (11 - i) for i in range(10))
    return (soma2 * 10) % 11 % 10 == d[10]


def data_existe(texto: str) -> bool:
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(tipo: str, campos: dict[str, str]) -> list[str]:
    erros: list[str] = []
    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if tipo == "alunos" else [])
    if any(not campos.get(chave, "").strip() for chave in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campos.get("n_usp", "")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("agencia", "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("valor_solicitado", "")
    if valor:
        centavos = re.sub(r"\D", "", valor)
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("email", "")
    if email and ("@" not in email or not email.rsplit("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf = campos.get("cpf", "")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not digitos_verificadores_cpf(cpf):
            erros.append("CPF inválido")

    cep = campos.get("cep", "")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campos.get("data_nascimento", "")
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_existe(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def formatar_valor(centavos: str) -> str:
    inteiro = f"{int(centavos[:-2] or 0):,}".replace(",", ".")
    return f"R$ {inteiro},{centavos[-2:]}"


def gerar_oficio(tipo: str, c: dict[str, str]) -> str:
    valor = formatar_valor(re.sub(r"\D", "", c["valor_solicitado"]))
    if tipo == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {c['tipo_auxilio']}"
        programa = f"Programa: {c['programa']} - {c['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {c['programa']}"
    linhas = [
        f"Interessada(o): {c['nome_completo']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['nome_evento']}",
        f"Período: {c['periodo_evento']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c.get("link_evento", "").strip():
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao_trabalho']}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c.get("complemento", "").strip():
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['data_nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg_rnm']}",
        f"Banco: {c['nome_banco']}",
        f"Agência: {c['agencia']}",
        f"Conta: {c['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao.tipo, solicitacao.campos)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(solicitacao.tipo, solicitacao.campos)}


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
