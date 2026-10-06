import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

BASE = Path(__file__).parent

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str = "alunos"
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""

    @field_validator("*", mode="before")
    @classmethod
    def _para_texto(cls, valor):
        return "" if valor is None else str(valor)


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]

RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_MOEDA = re.compile(r"^R\$\s*([\d.]+),(\d{2})$")


def eh_docente(d):
    return "doce" in d.aba.strip().lower()


def parse_valor(texto):
    texto = texto.strip()
    if not texto:
        return None
    if texto.isdigit():
        return int(texto)
    m = RE_MOEDA.match(texto)
    if not m:
        return None
    inteiro = m.group(1).replace(".", "")
    if not inteiro.isdigit():
        return None
    return int(inteiro) * 100 + int(m.group(2))


def fmt_moeda(centavos):
    reais, cent = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def cpf_valido(cpf):
    n = [int(c) for c in cpf if c.isdigit()]
    if len(n) != 11:
        return False
    for i in (9, 10):
        soma = sum(n[j] * ((i + 1) - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != n[i]:
            return False
    return True


def data_valida(texto):
    try:
        datetime.datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        return False
    return True


def validar(d):
    obrigatorios = list(OBRIGATORIOS)
    if not eh_docente(d):
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []

    if any(not getattr(d, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if d.n_usp.strip() and not d.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    if d.agencia.strip() and not d.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    centavos = parse_valor(d.valor)
    if d.valor.strip() and not (centavos and centavos > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if d.email.strip() and not RE_EMAIL.match(d.email.strip()):
        erros.append("E-mail inválido")

    cpf_formatado = False
    if d.cpf.strip():
        if RE_CPF.match(d.cpf.strip()):
            cpf_formatado = True
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")

    if d.cep.strip() and not RE_CEP.match(d.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    data_formatada = False
    if d.data_nascimento.strip():
        if RE_DATA.match(d.data_nascimento.strip()):
            data_formatada = True
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formatado and not cpf_valido(d.cpf):
        erros.append("CPF inválido")

    if data_formatada and not data_valida(d.data_nascimento):
        erros.append("Data de nascimento inválida")

    return erros, centavos


def gerar_oficio(d, valor_fmt):
    if eh_docente(d):
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {d.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}"
        programa = f"Programa: {d.programa} - {d.nivel}"

    linhas = [
        f"Interessada(o): {d.nome} - {d.n_usp}",
        f"E-mail: {d.email}",
        assunto,
        programa,
        "",
        f"A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.evento}",
        f"Período: {d.periodo}",
        f"Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}",
    ]

    if d.link.strip():
        linhas.append(f"Link do evento: {d.link}")

    linhas += [
        f"Apresentação de trabalho: {d.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {d.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro}, {d.numero}",
    ]

    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento}")

    linhas += [
        f"CEP: {d.cep}",
        f"{d.bairro}, {d.cidade} - {d.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.data_nascimento}",
        f"CPF: {d.cpf}",
        f"RG / RNM: {d.rg}",
        f"Banco: {d.banco}",
        f"Agência: {d.agencia}",
        f"Conta: {d.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitar(dados: Solicitacao):
    erros, centavos = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados, fmt_moeda(centavos))}


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/index.html")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilos():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


app.mount("/assets", StaticFiles(directory=str(BASE / "assets")), name="assets")
