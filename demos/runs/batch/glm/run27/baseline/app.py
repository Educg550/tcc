import calendar
import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")


ERRO_CAMPOS = "Preencha todos os campos"
ERRO_NUSP = "N. USP deve conter apenas números"
ERRO_AGENCIA = "Número da agência deve conter apenas números"
ERRO_VALOR = "Valor solicitado deve ser maior que 0"
ERRO_EMAIL = "E-mail inválido"
ERRO_CPF_FORMATO = "CPF deve estar no formato 000.000.000-00"
ERRO_CEP = "CEP deve estar no formato 00000-000"
ERRO_DATA_FORMATO = "Data de nascimento deve estar no formato dd/mm/aaaa"
ERRO_CPF = "CPF inválido"
ERRO_DATA = "Data de nascimento inválida"


class Endereco(BaseModel):
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""


class Pagamento(BaseModel):
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""

    def formatar_moeda(self, valor: int) -> str:
        return formatar_moeda(valor)


class Evento(BaseModel):
    nome: str = ""
    periodo: str = ""
    cidade: str = ""
    estado: str = ""
    pais: str = ""
    link: str = ""
    apresentacao: str = ""
    detalhamento: str = ""


class Solicitante(BaseModel):
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo: str = ""
    email: str = ""


class Solicitacao(BaseModel):
    aba: str = "alunos"
    solicitante: Solicitante = Solicitante()
    evento: Evento = Evento()
    endereco: Endereco = Endereco()
    pagamento: Pagamento = Pagamento()
    valor_solicitado: int = 0


class Erros(BaseModel):
    mensagens: list[str] = []
    oficio: str | None = None


def formatar_moeda(valor: int) -> str:
    centavos = valor % 100
    reais = valor // 100
    grupos = []
    while reais >= 1000:
        grupos.insert(0, str(reais % 1000).zfill(3))
        reais //= 1000
    grupos.insert(0, str(reais))
    return f"R$ {'.'.join(grupos)},{str(centavos).zfill(2)}"


def validar_cpf_digitos(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    soma = sum(d * f for d, f in zip(digitos[:9], range(10, 1, -1)))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != digitos[9]:
        return False
    soma2 = sum(d * f for d, f in zip(digitos[:10], range(11, 1, -1)))
    resto2 = (soma2 * 10) % 11
    if resto2 == 10:
        resto2 = 0
    return resto2 == digitos[10]


def validar_data(data: str) -> bool:
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", data)
    if not m:
        return False
    d, mes, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mes < 1 or mes > 12 or a < 1 or d < 1:
        return False
    return d <= calendar.monthrange(a, mes)[1]


def validar_email(email: str) -> bool:
    m = re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)
    return bool(m)


def gerar_oficio(s: Solicitacao) -> str:
    data_hoje = date.today().strftime("%d/%m/%Y")
    valor = formatar_moeda(s.valor_solicitado)
    linhas = []
    linhas.append(f"Interessada(o): {s.solicitante.nome} - {s.solicitante.nusp}")
    linhas.append(f"E-mail: {s.solicitante.email}")
    if s.aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.solicitante.programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.solicitante.tipo}")
        linhas.append(f"Programa: {s.solicitante.programa} - {s.solicitante.nivel}")
    linhas.append("")
    linhas.append(
        f"A CCP-{s.solicitante.programa} aprovou na data de hoje ({data_hoje}), "
        "a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.evento.nome}")
    linhas.append(f"Período: {s.evento.periodo}")
    linhas.append(f"Local: {s.evento.cidade} - {s.evento.estado} - {s.evento.pais}")
    if s.evento.link:
        linhas.append(f"Link do evento: {s.evento.link}")
    linhas.append(f"Apresentação de trabalho: {s.evento.apresentacao}")
    linhas.append(f"Valor solicitado: {valor}")
    linhas.append(f"Detalhamento: {s.evento.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.endereco.logradouro}, {s.endereco.numero}")
    if s.endereco.complemento:
        linhas.append(f"Complemento: {s.endereco.complemento}")
    linhas.append(f"CEP: {s.endereco.cep}")
    linhas.append(f"{s.endereco.bairro}, {s.endereco.cidade} - {s.endereco.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.endereco.data_nascimento}")
    linhas.append(f"CPF: {s.pagamento.cpf}")
    linhas.append(f"RG / RNM: {s.pagamento.rg}")
    linhas.append(f"Banco: {s.pagamento.banco}")
    linhas.append(f"Agência: {s.pagamento.agencia}")
    linhas.append(f"Conta: {s.pagamento.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(solicitacao: Solicitacao) -> Erros:
    s = solicitacao
    erros = []
    obrig = [
        s.solicitante.nome, s.solicitante.nusp, s.solicitante.programa,
        s.solicitante.email,
        s.evento.nome, s.evento.periodo, s.evento.cidade, s.evento.estado,
        s.evento.pais, s.evento.apresentacao, s.evento.detalhamento,
        s.endereco.logradouro, s.endereco.numero, s.endereco.bairro,
        s.endereco.cep, s.endereco.cidade, s.endereco.estado,
        s.endereco.data_nascimento,
        s.pagamento.cpf, s.pagamento.rg, s.pagamento.banco,
        s.pagamento.agencia, s.pagamento.conta,
    ]
    if s.aba == "alunos":
        obrig += [s.solicitante.nivel, s.solicitante.tipo]
    if any(not c.strip() for c in obrig):
        erros.append(ERRO_CAMPOS)
    if not erros or ERRO_CAMPOS not in erros:
        pass
    if s.solicitante.nusp and not s.solicitante.nusp.isdigit():
        erros.append(ERRO_NUSP)
    if s.pagamento.agencia and not s.pagamento.agencia.isdigit():
        erros.append(ERRO_AGENCIA)
    if s.valor_solicitado is None or s.valor_solicitado <= 0:
        erros.append(ERRO_VALOR)
    if s.solicitante.email and not validar_email(s.solicitante.email):
        erros.append(ERRO_EMAIL)
    if s.pagamento.cpf and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", s.pagamento.cpf):
        erros.append(ERRO_CPF_FORMATO)
    elif s.pagamento.cpf and not validar_cpf_digitos(s.pagamento.cpf):
        erros.append(ERRO_CPF)
    if s.endereco.cep and not re.match(r"^\d{5}-\d{3}$", s.endereco.cep):
        erros.append(ERRO_CEP)
    if s.endereco.data_nascimento and not re.match(r"^\d{2}/\d{2}/\d{4}$", s.endereco.data_nascimento):
        erros.append(ERRO_DATA_FORMATO)
    elif s.endereco.data_nascimento and not validar_data(s.endereco.data_nascimento):
        erros.append(ERRO_DATA)
    if erros:
        return Erros(mensagens=erros, oficio=None)
    return Erros(mensagens=[], oficio=gerar_oficio(s))
