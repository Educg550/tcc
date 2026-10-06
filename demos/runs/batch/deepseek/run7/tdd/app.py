import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
    nome_completo: str
    n_usp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    nome_evento: str
    periodo_evento: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: Optional[str] = ""
    valor_solicitado: str
    detalhamento: str
    apresentar_trabalho: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = ""
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def _cpf_valido(cpf: str) -> bool:
    d = re.sub(r"\D", "", cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in range(9, 11):
        s = sum(int(d[n]) * ((i + 1) - n) for n in range(i))
        if int(d[i]) != ((s * 10) % 11) % 10:
            return False
    return True


def _data_valida(data: str) -> bool:
    dia, mes, ano = (int(p) for p in data.split("/"))
    try:
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def _valor_numerico(valor: str) -> float:
    d = re.sub(r"\D", "", valor)
    return int(d) / 100 if d else 0.0


def validar(s: Solicitacao):
    erros = []

    obrigatorios = [
        s.nome_completo, s.n_usp, s.programa, s.email, s.nome_evento,
        s.periodo_evento, s.cidade_evento, s.estado_evento, s.pais_evento,
        s.valor_solicitado, s.detalhamento, s.apresentar_trabalho,
        s.data_nascimento, s.logradouro, s.numero, s.bairro, s.cep,
        s.cidade, s.estado, s.cpf, s.rg, s.banco, s.agencia, s.conta,
    ]
    if s.aba == "ALUNOS":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not c or not str(c).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp and not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if _valor_numerico(s.valor_solicitado) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.email or ""):
        erros.append("E-mail inválido")
    if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", s.cpf or ""):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if not re.match(r"^\d{5}-\d{3}$", s.cep or ""):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", s.data_nascimento or ""):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not _data_valida(s.data_nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(s: Solicitacao) -> str:
    linhas = []
    linhas.append(f"Interessada(o): {s.nome_completo} - {s.n_usp}")
    linhas.append(f"E-mail: {s.email}")
    if s.aba == "DOCENTES":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    linhas.append("")
    linhas.append(f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.nome_evento}")
    linhas.append(f"Período: {s.periodo_evento}")
    linhas.append(f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}")
    if s.link_evento:
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.append(f"Apresentação de trabalho: {s.apresentar_trabalho}")
    linhas.append(f"Valor solicitado: {s.valor_solicitado}")
    linhas.append(f"Detalhamento: {s.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.logradouro}, {s.numero}")
    if s.complemento:
        linhas.append(f"Complemento: {s.complemento}")
    linhas.append(f"CEP: {s.cep}")
    linhas.append(f"{s.bairro}, {s.cidade} - {s.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.data_nascimento}")
    linhas.append(f"CPF: {s.cpf}")
    linhas.append(f"RG / RNM: {s.rg}")
    linhas.append(f"Banco: {s.banco}")
    linhas.append(f"Agência: {s.agencia}")
    linhas.append(f"Conta: {s.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas) + "\n"


@app.post("/submit")
def submit(s: Solicitacao):
    erros = validar(s)
    if erros:
        return JSONResponse(status_code=400, content={"errors": erros})
    return {"oficio": gerar_oficio(s)}


@app.get("/")
def index():
    return FileResponse("index.html")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/", StaticFiles(directory=".", html=True), name="static")
