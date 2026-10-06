"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

app.mount("/static", StaticFiles(directory="static"), name="static")


class Solicitacao(BaseModel):
    """Dados enviados por uma das abas do formulário."""

    tipo: str  # "alunos" ou "docentes"
    nome_completo: str
    n_usp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    nome_evento: str
    periodo_evento: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ""
    valor_solicitado: float
    detalhamento: str
    apresentacao: str
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def _validar_cpf(cpf: str) -> bool:
    """Verifica os dígitos do CPF."""
    digitos = [int(d) for d in cpf if d.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    soma = sum(d * w for d, w in zip(digitos[:9], range(10, 1, -1)))
    if (soma * 10) % 11 % 10 != digitos[9]:
        return False
    soma = sum(d * w for d, w in zip(digitos[:10], range(11, 1, -1)))
    return (soma * 10) % 11 % 10 == digitos[10]


def _validar_data(data_str: str) -> bool:
    """Verifica se a data existe no calendário."""
    try:
        dia, mes, ano = (int(p) for p in data_str.split("/"))
        date(ano, mes, dia)
        return 1900 <= ano <= date.today().year
    except (ValueError, TypeError):
        return False


@app.get("/", response_class=FileResponse)
def index():
    """Serve a página do formulário."""
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    """Endpoint de verificação."""
    return {"status": "ok"}


@app.post("/solicitacao")
def processar(s: Solicitacao):
    """Valida a solicitação e devolve o ofício pronto ou os erros."""
    erros = []

    if s.tipo == "alunos" and (not s.nivel or not s.tipo_auxilio):
        erros.append("Alunos devem informar nível e tipo de auxílio.")

    if not _validar_cpf(s.cpf):
        erros.append("CPF inválido.")
    if not _validar_data(s.data_nascimento):
        erros.append("Data de nascimento inválida.")
    if s.valor_solicitado <= 0:
        erros.append("Valor solicitado deve ser maior que zero.")
    if "@" not in s.email or len(s.email.split("@")[-1]) == 0:
        erros.append("E-mail inválido.")

    if erros:
        return {"ok": False, "erros": erros}

    linhas = []
    a = linhas.append
    a(f"Interessado(a): {s.nome_completo} - {s.n_usp}")
    a(f"E-mail: {s.email}")
    if s.tipo == "alunos":
        a(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        a(f"Programa: {s.programa} - {s.nivel}")
    else:
        a("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        a(f"Programa: {s.programa}")
    a("")
    a("A CCP aprovou, na data de hoje, a solicitação de auxílio financeiro do interessado acima, conforme segue:")
    a("")
    a("Dados do evento")
    a(f"Evento: {s.nome_evento}")
    a(f"Período: {s.periodo_evento}")
    a(f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}")
    if s.link_evento:
        a(f"Link do evento: {s.link_evento}")
    a(f"Apresentação de trabalho: {s.apresentacao}")
    a(f"Valor solicitado: R$ {s.valor_solicitado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    a(f"Detalhamento: {s.detalhamento}")
    a("")
    a("Endereço do interessado(a)")
    a(f"{s.logradouro}, {s.numero}")
    if s.complemento:
        a(f"Complemento: {s.complemento}")
    a(f"CEP: {s.cep}")
    a(f"{s.bairro}, {s.cidade} - {s.estado}")
    a("")
    a("Dados para pagamento")
    a(f"Data de nascimento: {s.data_nascimento}")
    a(f"CPF: {s.cpf}")
    a(f"RG / RNM: {s.rg}")
    a(f"Banco: {s.banco}")
    a(f"Agência: {s.agencia}")
    a(f"Conta: {s.conta}")
    a("")
    a("Encaminhe-se ao Serviço Financeiro para providências.")

    return {"ok": True, "oficio": "\n".join(linhas)}
