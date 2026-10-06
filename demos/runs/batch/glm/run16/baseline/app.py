import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade: str
    estado: str


class Pagamento(BaseModel):
    data_nascimento: str
    cpf: str
    rg_rnm: str
    banco: str
    agencia: str
    conta: str


class Solicitacao(BaseModel):
    tipo: str
    nome: str
    numero_usp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ""
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
    endereco: Endereco
    pagamento: Pagamento


def valida_cpf(cpf: str) -> bool:
    if not re.fullmatch(r"\d{11}", cpf):
        return False
    digitos = [int(d) for d in cpf]
    for i in (9, 10):
        soma = sum(d * peso for d, peso in zip(digitos[:i], range(i + 1, 1, -1)))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        if digitos[i] != dv:
            return False
    return True


def valida_data(data_str: str) -> bool:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data_str)
    if not m:
        return False
    dia, mes, ano = (int(g) for g in m.groups())
    if not 1 <= mes <= 12:
        return False
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formata_brl(centavos_str: str) -> str:
    centavos = int(centavos_str)
    parte_inteira = centavos // 100
    centavos_resto = centavos % 100
    texto = f"{parte_inteira:,}".replace(",", ".")
    return f"R$ {texto},{centavos_resto:02d}"


@app.post("/solicitacao")
async def criar_solicitacao(s: Solicitacao):
    erros = []

    obrigatorios = [
        s.nome, s.numero_usp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor_solicitado,
        s.detalhamento, s.apresentacao, s.endereco.logradouro, s.endereco.numero,
        s.endereco.bairro, s.endereco.cep, s.endereco.cidade, s.endereco.estado,
        s.pagamento.data_nascimento, s.pagamento.cpf, s.pagamento.rg_rnm,
        s.pagamento.banco, s.pagamento.agencia, s.pagamento.conta,
    ]
    if s.tipo == "alunos":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if not all(campo.strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if not re.fullmatch(r"\d+", s.numero_usp.strip()):
        erros.append("N. USP deve conter apenas números")

    if not re.fullmatch(r"\d+", s.pagamento.agencia.strip()):
        erros.append("Número da agência deve conter apenas números")

    if not re.fullmatch(r"\d+", s.valor_solicitado.strip()) or int(s.valor_solicitado.strip() or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = s.email.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    if not re.fullmatch(r"\d{11}", s.pagamento.cpf.strip()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not valida_cpf(s.pagamento.cpf.strip()):
        erros.append("CPF inválido")

    if not re.fullmatch(r"\d{8}", s.endereco.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    if not valida_data(s.pagamento.data_nascimento.strip()):
        erros.append("Data de nascimento inválida")
    elif not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.pagamento.data_nascimento.strip()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if erros:
        return JSONResponse(status_code=422, content={"ok": False, "erros": erros})

    data_hoje = date.today().strftime("%d/%m/%Y")

    if s.tipo == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = f"Programa: {s.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa_linha = f"Programa: {s.programa} - {s.nivel}"

    linhas = [
        f"Interessada(o): {s.nome} - {s.numero_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa_linha,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje ({data_hoje}), a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {formata_brl(s.valor_solicitado)}",
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
        f"Data de nascimento: {s.pagamento.data_nascimento}",
        f"CPF: {s.pagamento.cpf}",
        f"RG / RNM: {s.pagamento.rg_rnm}",
        f"Banco: {s.pagamento.banco}",
        f"Agência: {s.pagamento.agencia}",
        f"Conta: {s.pagamento.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return {"ok": True, "oficio": "\n".join(linhas)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
