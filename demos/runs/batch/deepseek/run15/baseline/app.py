import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


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
    link_evento: str = ""
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


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def cpf_valido(cpf):
    d = [int(c) for c in re.sub(r"\D", "", cpf)]
    for i in (9, 10):
        soma = sum(d[j] * (i + 1 - j) for j in range(i))
        if (soma * 10) % 11 % 10 != d[i]:
            return False
    return True


def parse_valor(v):
    digitos = re.sub(r"\D", "", v or "")
    return int(digitos) if digitos else 0


def format_moeda(cents):
    reais = cents // 100
    resto = cents % 100
    return "R$ " + format(reais, ",").replace(",", ".") + "," + f"{resto:02d}"


def validar(s):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if s.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not getattr(s, c).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")

    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")

    if s.valor.strip() and parse_valor(s.valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    if s.email.strip() and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.email.strip()):
        erros.append("E-mail inválido")

    cpf = s.cpf.strip()
    cpf_formato_ok = bool(re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf))
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if s.cep.strip() and not re.match(r"^\d{5}-\d{3}$", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    data = s.data_nascimento.strip()
    data_formato_ok = bool(re.match(r"^\d{2}/\d{2}/\d{4}$", data))
    if data and not data_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_formato_ok and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data and data_formato_ok:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(s):
    if s.aba == "alunos":
        assunto = "Solicitação de Auxílio Financeiro - " + s.tipo_auxilio
        programa_linha = s.programa + " - " + s.nivel
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = s.programa

    valor = format_moeda(parse_valor(s.valor))
    link_linha = f"Link do evento: {s.link_evento}\n" if s.link_evento.strip() else ""
    complemento_linha = f"Complemento: {s.complemento}\n" if s.complemento.strip() else ""

    return f"""Interessada(o): {s.nome} - {s.n_usp}
E-mail: {s.email}
Assunto: {assunto}
Programa: {programa_linha}

A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
Evento: {s.evento}
Período: {s.periodo}
Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}
{link_linha}Apresentação de trabalho: {s.apresentacao}
Valor solicitado: {valor}
Detalhamento: {s.detalhamento}

Endereço da(o) interessada(o)
{s.logradouro}, {s.numero}
{complemento_linha}CEP: {s.cep}
{s.bairro}, {s.cidade} - {s.estado}

Dados para pagamento
Data de nascimento: {s.data_nascimento}
CPF: {s.cpf}
RG / RNM: {s.rg}
Banco: {s.banco}
Agência: {s.agencia}
Conta: {s.conta}

Encaminhe-se ao Serviço Financeiro para providências."""


@app.post("/solicitar")
@app.post("/api/solicitar")
def solicitar(sol: Solicitacao):
    erros = validar(sol)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(sol)}


@app.get("/")
def pagina():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")
