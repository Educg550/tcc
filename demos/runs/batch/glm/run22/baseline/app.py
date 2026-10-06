from datetime import date
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import re

app = FastAPI()


class Contato(BaseModel):
    nome_completo: str
    n_usp: str
    programa: str
    nivel: str | None = None
    tipo_de_auxilio: str | None = None
    email: str
    nome_do_evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ""
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
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


class SolicitacaoAluno(BaseModel):
    solicitante: Contato


class SolicitacaoDocente(BaseModel):
    solicitante: Contato


class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cep: str
    cidade: str
    estado: str


class Banco(BaseModel):
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


class Evento(BaseModel):
    nome_do_evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: str = ""
    valor_solicitado: str
    detalhamento: str
    apresentacao: str


class Solicitante(BaseModel):
    nome_completo: str
    n_usp: str
    programa: str
    nivel: str | None = None
    tipo_de_auxilio: str | None = None
    email: str


class Solicitacao(BaseModel):
    solicitante: Solicitante
    evento: Evento
    endereco: Endereco
    banco: Banco


def validar_cpf(cpf: str) -> bool:
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    if resto < 2:
        dv1 = 0
    else:
        dv1 = 11 - resto
    if int(cpf[9]) != dv1:
        return False
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    if resto < 2:
        dv2 = 0
    else:
        dv2 = 11 - resto
    if int(cpf[10]) != dv2:
        return False
    return True


def validar_data(data: str) -> bool:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return False
    dia, mes, ano = map(int, data.split("/"))
    try:
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def validar_valor(valor: str) -> bool:
    if not valor or not valor.isdigit() or int(valor) <= 0:
        return False
    return True


@app.post("/api/alunos")
def processar_aluno(s: Solicitacao):
    return validar_e_gerar(s, tipo="alunos")


@app.post("/api/docentes")
def processar_docente(s: Solicitacao):
    return validar_e_gerar(s, tipo="docentes")


def validar_e_gerar(s: Solicitacao, tipo: str):
    erros = []
    campos = [
        s.solicitante.nome_completo, s.solicitante.n_usp, s.solicitante.programa,
        s.solicitante.email, s.evento.nome_do_evento, s.evento.periodo,
        s.evento.cidade_evento, s.evento.estado_evento, s.evento.pais_evento,
        s.evento.valor_solicitado, s.evento.detalhamento, s.evento.apresentacao,
        s.endereco.logradouro, s.endereco.numero, s.endereco.bairro, s.endereco.cep,
        s.endereco.cidade, s.endereco.estado, s.banco.cpf, s.banco.rg, s.banco.banco,
        s.banco.agencia, s.banco.conta
    ]
    if tipo == "alunos":
        campos += [s.solicitante.nivel, s.solicitante.tipo_de_auxilio]
    if any(c.strip() == "" for c in campos if c is not None):
        erros.append("Preencha todos os campos")
    if not s.solicitante.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.banco.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if not validar_valor(s.evento.valor_solicitado):
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in s.solicitante.email or not re.search(r"@.+\..+", s.solicitante.email):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.banco.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not validar_cpf(s.banco.cpf.replace(".", "").replace("-", "")):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", s.endereco.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.endereco.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not validar_data(s.endereco.data_nascimento):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    oficio = gerar_oficio(s, tipo)
    return {"ok": True, "oficio": oficio}


def formatar_brl(c: str) -> str:
    c = int(c)
    reais = c // 100
    cent = c % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{cent:02d}"


def gerar_oficio(s: Solicitante, tipo: str) -> str:
    linhas = []
    linhas.append(f"Interessada(o): {s.solicitante.nome_completo} - {s.solicitante.n_usp}")
    linhas.append(f"E-mail: {s.solicitante.email}")
    if tipo == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.solicitante.tipo_de_auxilio}")
        linhas.append(f"Programa: {s.solicitante.programa} - {s.solicitante.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.solicitante.programa}")
    linhas.append("")
    linhas.append("A CCP-" + s.solicitante.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.evento.nome_do_evento}")
    linhas.append(f"Período: {s.evento.periodo}")
    linhas.append(f"Local: {s.evento.cidade_evento} - {s.evento.estado_evento} - {s.evento.pais_evento}")
    if s.evento.link_evento.strip():
        linhas.append(f"Link do evento: {s.evento.link_evento}")
    linhas.append(f"Apresentação de trabalho: {s.evento.apresentacao}")
    linhas.append(f"Valor solicitado: {formatar_brl(s.evento.valor_solicitado)}")
    linhas.append(f"Detalhamento: {s.evento.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.endereco.logradouro}, {s.endereco.numero}")
    if s.endereco.complemento.strip():
        linhas.append(f"Complemento: {s.endereco.complemento}")
    linhas.append(f"CEP: {s.endereco.cep}")
    linhas.append(f"{s.endereco.bairro}, {s.endereco.cidade} - {s.endereco.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.endereco.data_nascimento}")
    linhas.append(f"CPF: {s.banco.cpf}")
    linhas.append(f"RG / RNM: {s.banco.rg}")
    linhas.append(f"Banco: {s.banco.banco}")
    linhas.append(f"Agência: {s.banco.agencia}")
    linhas.append(f"Conta: {s.banco.conta}")
 linhas.append("")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
