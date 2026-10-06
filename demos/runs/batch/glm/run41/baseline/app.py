"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str
    nome: str
    nusp: str
    programa: str
    nivel: str
    tipo_auxilio: str
    email: str
    evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def cpf_valido(cpf: str) -> bool:
    digitos = [int(d) for d in cpf if d.isdigit()]
    if len(digitos) != 11:
        return False
    soma = sum(d * w for d, w in zip(digitos[:9], range(10, 1, -1)))
    d1 = (soma * 10 % 11) % 11
    soma = sum(d * w for d, w in zip(digitos[:10], range(11, 1, -1)))
    d2 = (soma * 10 % 11) % 11
    return d1 == digitos[9] and d2 == digitos[10]


def valida(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    campos = [s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo,
              s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
              s.detalhamento, s.apresentacao, s.nascimento, s.logradouro,
              s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg,
              s.banco, s.agencia, s.conta]
    if s.tipo == "aluno":
        campos += [s.nivel, s.tipo_auxilio]
    if any(not c.strip() for c in campos):
        erros.append("Preencha todos os campos")
    if not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if not (s.valor.replace(".", "").replace(",", "").isdigit()
            and int(s.valor.replace(".", "").replace(",", "")) > 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in s.email or "@" not in s.email.split("@")[1] or not s.email.split("@")[1]:
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            date(int(s.nascimento[6:]), int(s.nascimento[3:5]), int(s.nascimento[:2]))
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def moeda(digitos: str) -> str:
    n = int(digitos)
    reais = n // 100
    centavos = n % 100
    return f"R$ {reais:,}.{centavos:02d}".replace(",", ".")


def oficio(s: Solicitacao) -> str:
    valor_fmt = moeda(s.valor.replace(".", "").replace(",", ""))
    hoje = date.today().strftime("%d/%m/%Y")
    if s.tipo == "aluno":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
    linhas = [
        f"Interessada(o): {s.nome} - {s.nusp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje ({hoje}), a solicitação de auxílio financeiro para a",
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
        f"Valor solicitado: {valor_fmt}",
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
        f"Data de nascimento: {s.nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def processa(s: Solicitacao):
    erros = valida(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": oficio(s)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
