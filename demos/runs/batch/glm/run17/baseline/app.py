from datetime import date
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

# ---------------------------------------------------------------- arquivos estáticos

app.mount("/static", StaticFiles(directory="static"), name="static")


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade: str
    estado: str


class Solicitacao(BaseModel):
    nome: str
    numero_usp: str
    programa: str
    nivel: str
    tipo_de_auxilio: str
    email: str
    nome_do_evento: str
    periodo_do_evento: str
    cidade_do_evento: str
    estado_do_evento: str
    pais_do_evento: str
    link_do_evento: str = ""
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
    data_de_nascimento: str
    endereco: Endereco
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def validar_cpf(cpf: str) -> bool:
    """Valida os dígitos verificadores do CPF."""
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if digito1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    return digito2 == int(cpf[10])


def formatar_data(data: str) -> str:
    """Converte 'aaaa-mm-dd' para 'dd/mm/aaaa'; retorna entrada em caso de erro."""
    try:
        d = date.fromisoformat(data)
        return d.strftime("%d/%m/%Y")
    except ValueError:
        return data


def formatar_moeda(valor: float) -> str:
    """Formata 1500.0 como 'R$ 1.500,00'."""
    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)
    partes = []
    while inteiro >= 1000:
        partes.insert(0, f"{inteiro % 1000:03d}")
        inteiro //= 1000
    partes.insert(0, str(inteiro))
    texto = ".".join(partes)
    return f"R$ {texto},{centavos:02d}"


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/solicitacao")
async def criar_solicitacao(s: Solicitacao) -> JSONResponse:
    erros = []

    # ---------------------------------------------------------------- obrigatoriedade
    obrigatorios = [
        s.nome, s.numero_usp, s.programa, s.email,
        s.nome_do_evento, s.periodo_do_evento,
        s.cidade_do_evento, s.estado_do_evento, s.pais_do_evento,
        s.valor_solicitado, s.detalhamento, s.apresentacao,
        s.data_de_nascimento,
        s.endereco.logradouro, s.endereco.numero, s.endereco.bairro,
        s.endereco.cep, s.endereco.cidade, s.endereco.estado,
        s.cpf, s.rg, s.banco, s.agencia, s.conta,
    ]
    nivel_vazio = not s.nivel.strip()
    auxilio_vazio = not s.tipo_de_auxilio.strip()

    if any(not campo.strip() for campo in obrigatorios) or nivel_vazio or auxilio_vazio:
        erros.append("Preencha todos os campos")

    # ---------------------------------------------------------------- formatos
    if s.numero_usp and not s.numero_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    try:
        valor = float(s.valor_solicitado.replace(",", "."))
        if valor <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    except ValueError:
        if s.valor_solicitado.strip():
            erros.append("Valor solicitado deve ser maior que 0")

    if s.email and "@" not in s.email:
        erros.append("E-mail inválido")
    elif s.email:
        _, sep, dominio = s.email.partition("@")
        if not sep or not dominio.strip() or "." not in dominio:
            erros.append("E-mail inválido")

    if s.cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif s.cpf and not validar_cpf(s.cpf):
        erros.append("CPF inválido")

    if s.endereco.cep and not re.fullmatch(r"\d{5}-\d{3}", s.endereco.cep):
        erros.append("CEP deve estar no formato 00000-000")

    if s.data_de_nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_de_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif s.data_de_nascimento:
        d = formatar_data(s.data_de_nascimento)
        if d == s.data_de_nascimento and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s.data_de_nascimento):
            erros.append("Data de nascimento inválida")

    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})

    # ---------------------------------------------------------------- ofício
    data_oficio = formatar_data(s.data_de_nascimento)
    valor_fmt = formatar_moeda(valor)

    linhas = [
        f"Interessada(o): {s.nome} - {s.numero_usp}",
        f"E-mail: {s.email}",
        f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_de_auxilio}",
        f"Programa: {s.programa} - {s.nivel}",
        "",
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_do_evento}",
        f"Período: {s.periodo_do_evento}",
        f"Local: {s.cidade_do_evento} - {s.estado_do_evento} - {s.pais_do_evento}",
    ]
    if s.link_do_evento.strip():
        linhas.append(f"Link do evento: {s.link_do_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.endereco.logradouro}, {s.endereco.numero}",
    ]
    if s.endereco.complemento.strip():
        linhas.append(f"Complemento: {s.endereco.complemento}")
    linhas += [
        f"CEP: {s.endereco.cep}",
        f"{s.endereco.bairro}, {s.endereco.cidade} - {s.endereco.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data_oficio}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return {"oficio": "\n".join(linhas), "erros": []}
