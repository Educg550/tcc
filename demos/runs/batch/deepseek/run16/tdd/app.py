import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def comportamento():
    return FileResponse("app.js")


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


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]

FORMATO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
FORMATO_CEP = re.compile(r"\d{5}-\d{3}")
FORMATO_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def apenas_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def valor_valido(texto):
    digitos = apenas_digitos(texto)
    return bool(digitos) and int(digitos) > 0


def formatar_valor(texto):
    digitos = apenas_digitos(texto)
    if not digitos:
        return texto
    reais = int(digitos) / 100
    return "R$ " + f"{reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cpf_valido(texto):
    digitos = apenas_digitos(texto)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        verificador = (soma * 10) % 11
        if verificador == 10:
            verificador = 0
        if verificador != int(digitos[tamanho]):
            return False
    return True


def data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(s):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if s.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not getattr(s, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")

    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")

    if s.valor.strip() and not valor_valido(s.valor):
        erros.append("Valor solicitado deve ser maior que 0")

    if s.email.strip() and not FORMATO_EMAIL.fullmatch(s.email.strip()):
        erros.append("E-mail inválido")

    if s.cpf.strip() and not FORMATO_CPF.fullmatch(s.cpf.strip()):
        erros.append("CPF deve estar no formato 000.000.000-00")

    if s.cep.strip() and not FORMATO_CEP.fullmatch(s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    if s.data_nascimento.strip() and not FORMATO_DATA.fullmatch(s.data_nascimento.strip()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if FORMATO_CPF.fullmatch(s.cpf.strip()) and not cpf_valido(s.cpf):
        erros.append("CPF inválido")

    if FORMATO_DATA.fullmatch(s.data_nascimento.strip()) and not data_valida(s.data_nascimento.strip()):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(s):
    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
    ]
    if s.aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    linhas += [
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link.strip():
        linhas.append(f"Link do evento: {s.link}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {formatar_valor(s.valor)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
def solicitar(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": montar_oficio(dados)}
