import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    aba: str = ""
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
    def como_texto(cls, valor):
        return "" if valor is None else str(valor)


app = FastAPI()


@app.post("/api/solicitacao")
def registrar(solicitacao: Solicitacao):
    erros = validar(solicitacao)
    if erros:
        return {"erros": erros}
    return {"oficio": redigir(solicitacao)}


def validar(s):
    erros = []
    obrigatorios = [
        s.nome, s.n_usp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
        s.detalhamento, s.apresentacao, s.data_nascimento, s.logradouro,
        s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg,
        s.banco, s.agencia, s.conta,
    ]
    if s.aba != "docentes":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not campo.strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    centavos = re.sub(r"\D", "", s.valor)
    if s.valor.strip() and (not centavos or int(centavos) == 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email.strip() and not re.fullmatch(r"[^@\s]+@[^@\s]+", s.email.strip()):
        erros.append("E-mail inválido")
    cpf = s.cpf.strip()
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")
    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    data = s.data_nascimento.strip()
    if data and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def cpf_valido(cpf):
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11:
        return False
    resto1 = sum(d * p for d, p in zip(digitos[:9], range(10, 1, -1))) % 11
    dv1 = 0 if resto1 < 2 else 11 - resto1
    resto2 = sum(d * p for d, p in zip(digitos[:10], range(11, 1, -1))) % 11
    dv2 = 0 if resto2 < 2 else 11 - resto2
    return digitos[9] == dv1 and digitos[10] == dv2


def moeda(texto):
    centavos = int(re.sub(r"\D", "", texto) or "0")
    return f"R$ {centavos // 100:,}".replace(",", ".") + f",{centavos % 100:02d}"


def redigir(s):
    if s.aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {s.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        linha_programa = f"Programa: {s.programa} - {s.nivel}"
    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        assunto,
        linha_programa,
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
        f"Valor solicitado: {moeda(s.valor)}",
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


app.mount("/", StaticFiles(directory=RAIZ, html=True), name="raiz")
