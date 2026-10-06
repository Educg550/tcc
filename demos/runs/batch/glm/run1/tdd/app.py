"""Backend da aplicação de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    perfil: str = "alunos"
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


def _cpf_valido(digitos: str) -> bool:
    if len(digitos) != 11 or not digitos.isdigit() or len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(d) * peso for d, peso in zip(digitos[:i], range(i + 1, 1, -1)))
        resto = soma * 10 % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def _erros_de(s: Solicitacao) -> list[str]:
    obrigatorios = [
        s.nome, s.n_usp, s.programa, s.email, s.evento, s.periodo, s.cidade_evento,
        s.estado_evento, s.pais_evento, s.valor, s.detalhamento, s.apresentacao,
        s.logradouro, s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg,
        s.banco, s.agencia, s.conta, s.data_nascimento,
    ]
    if s.perfil == "alunos":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    erros = []
    if any(not c.strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    m = re.fullmatch(r"R\$\s*([\d.]*),(\d{2})", s.valor.strip())
    if not m or int(m.group(1).replace(".", "") or "0") == 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = s.email.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf.strip()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(re.sub(r"\D", "", s.cpf)):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento.strip()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        d, m, a = map(int, s.data_nascimento.split("/"))
        try:
            date(a, m, d)
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def _oficio_de(s: Solicitacao) -> str:
    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        (f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
         if s.perfil == "alunos"
         else "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"),
        (f"Programa: {s.programa} - {s.nivel}"
         if s.perfil == "alunos"
         else f"Programa: {s.programa}"),
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
        f"Valor solicitado: {s.valor.strip()}",
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
    return "\n".join(linhas) + "\n"


@app.post("/solicitacao")
def criar_solicitacao(solicitacao: Solicitacao):
    erros = _erros_de(solicitacao)
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio_de(solicitacao)}


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=RAIZ), name="static")


@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css", include_in_schema=False)
def arquivo_css():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def arquivo_js():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")
