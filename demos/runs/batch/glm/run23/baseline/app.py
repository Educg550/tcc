"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date, datetime

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


def validacpf(cpf: str) -> bool:
    if not re.fullmatch(r"\d{11}", cpf):
        return False
    if cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        s = sum(int(c) * k for c, k in zip(cpf[:i], range(i - 7, 1, -1)))
        r = (s * 10) % 11
        if r != int(cpf[i]):
            return False
    return True


def valida_data(valor: str) -> bool:
    try:
        datetime.strptime(valor, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def moeda(centavos: int) -> str:
    valor = f"{centavos // 100},{centavos % 100:02d}"
    for i in range(len(valor) - 3, 0, -3):
        valor = valor[:i] + "." + valor[i:]
    return "R$ " + valor


class Solicitacao(BaseModel):
    aba: str
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo: str = ""
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
    nascimento: str = ""
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


class Erro(BaseModel):
    erros: list[str]
    oficio: str | None = None


@app.post("/api/solicitacao", response_model=None)
def cria(s: Solicitacao):
    erros = []

    if not validacpf(re.sub(r"\D", "", s.cpf)):
        erros.append("CPF inválido" if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf) else "CPF deve estar no formato 000.000.000-00")

    if not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")

    if not valida_data(s.nascimento):
        erros.append("Data de nascimento inválida" if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.nascimento) else "Data de nascimento deve estar no formato dd/mm/aaaa")

    obr = [s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo, s.cidade_evento, s.estado_evento, s.pais_evento, s.valor, s.detalhamento, s.apresentacao, s.logradouro, s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg, s.banco, s.agencia, s.conta]

    if s.aba == "ALUNOS":
        obr.extend([s.nivel, s.tipo])

    if not all(v.strip() for v in obr):
        erros.insert(0, "Preencha todos os campos")

    if not re.fullmatch(r"\d+", s.nusp):
        erros.append("N. USP deve conter apenas números")

    if not re.fullmatch(r"\d+", s.agencia):
        erros.append("Número da agência deve conter apenas números")

    if not re.fullmatch(r"\d+", s.valor) or int(s.valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s.email):
        erros.append("E-mail inválido")

    if erros:
        return {"erros": erros}

    hoje = date.today().strftime("%d/%m/%Y")
    tipo = s.tipo if s.aba == "ALUNOS" else "Verba do programa"
    programa = f"{s.programa} - {s.nivel}" if s.aba == "ALUNOS" else s.programa

    linhas = [
        f"Interessada(o): {s.nome} - {s.nusp}",
        f"E-mail: {s.email}",
        f"Assunto: Solicitação de Auxílio Financeiro - {tipo}",
        f"Programa: {programa}",
        "",
        f"A CCP-{s.programa} aprovou na data de hoje ({hoje}), a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]

    if s.link.strip():
        linhas.append(f"Link do evento: {s.link.strip()}")

    linhas.extend([
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {moeda(int(s.valor))}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ])

    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento.strip()}")

    linhas.extend([
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])

    return {"erros": [], "oficio": "\n".join(linhas)}


app.mount("/", StaticFiles(directory="frontend", html=True), name="estaticos")
