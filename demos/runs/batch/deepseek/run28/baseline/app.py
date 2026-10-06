import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


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


RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_DIGITOS = re.compile(r"^\d+$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(set(digitos)) == 1:
        return False
    for n in (9, 10):
        soma = sum(digitos[i] * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != digitos[n]:
            return False
    return True


def _data_valida(txt):
    dia, mes, ano = (int(parte) for parte in txt.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _centavos(valor):
    digitos = re.sub(r"\D", "", valor or "")
    return int(digitos) if digitos else 0


def _formatar_valor(centavos):
    reais, resto = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def validar(s):
    erros = []
    obrigatorios = [
        s.nome, s.n_usp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
        s.detalhamento, s.apresentacao, s.data_nascimento, s.logradouro,
        s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg,
        s.banco, s.agencia, s.conta,
    ]
    if s.aba == "alunos":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not campo.strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp and not RE_DIGITOS.match(s.n_usp):
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not RE_DIGITOS.match(s.agencia):
        erros.append("Número da agência deve conter apenas números")
    if s.valor and _centavos(s.valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email and not RE_EMAIL.match(s.email):
        erros.append("E-mail inválido")
    if s.cpf and not RE_CPF.match(s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    if s.cep and not RE_CEP.match(s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if s.data_nascimento and not RE_DATA.match(s.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if s.cpf and RE_CPF.match(s.cpf) and not _cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if s.data_nascimento and RE_DATA.match(s.data_nascimento) and not _data_valida(s.data_nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(s):
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
    if s.link_evento:
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {_formatar_valor(_centavos(s.valor))}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento:
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


@app.post("/api/solicitar")
@app.post("/solicitar")
def solicitar(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {"valido": False, "erros": erros}
    return {"valido": True, "oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="estaticos")
