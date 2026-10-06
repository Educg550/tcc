from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import re

app = FastAPI()

# Modelos de dados

class Endereco(BaseModel):
    data_nascimento: str
    logradouro: str
    numero: str
    complemento: Optional[str] = ""
    bairro: str
    cep: str
    cidade: str
    estado: str


class Pagamento(BaseModel):
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


class Solicitacao(BaseModel):
    tipo: str  # "aluno" ou "docente"
    nome_completo: str
    n_usp: str
    programa: str
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
    email: str
    nome_evento: str
    periodo: str
    cidade_evento: str
    estado_evento: str
    pais_evento: str
    link_evento: Optional[str] = ""
    valor_solicitado: str
    detalhamento: str
    apresentacao: str
    endereco: Endereco
    pagamento: Pagamento

# Formata o valor em centavos para "R$ 1.234,56"
def formatar_valor(centavos: int) -> str:
    texto = f"{centavos:,}".replace(",", ".")
    reais, _, cent = texto.partition(".")
    if centavos < 100:
        cent = f"{centavos:02d}"
    elif len(cent) == 1:
        cent += "0"
    # recontruir: f-string com grouping manual
    return f"R$ {reais},{cent}"

# Valida e formata CPF
def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11 % 10
    if d1 != int(cpf[9]):
        return False
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma2 * 10) % 11 % 10
    return d2 == int(cpf[10])


def validar_data(data: str) -> bool:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return False
    d, mes, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mes < 1 or mes > 12:
        return False
    if a < 1 or a > 9999:
        return False
    if d < 1 or d > dias_no_mes(mes, a):
        return False
    return True


def dias_no_mes(mes: int, ano: int) -> int:
    if mes == 2:
        return 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28
    return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]


def formatar_data(data: str) -> str:
    d = data.replace("/", "")
    if len(d) != 8:
        return data
    return f"{d[:2]}/{d[2:4]}/{d[4:]}"


@app.post("/api/solicitacao")
def receber_solicitacao(s: Solicitacao):
    erros = []

    # Campos obrigatórios
    obrigatorios = [s.nome_completo, s.n_usp, s.programa, s.email, s.nome_evento, s.periodo,
                    s.cidade_evento, s.estado_evento, s.pais_evento, s.valor_solicitado,
                    s.detalhamento, s.apresentacao,
                    s.endereco.data_nascimento, s.endereco.logradouro, s.endereco.numero,
                    s.endereco.bairro, s.endereco.cep, s.endereco.cidade, s.endereco.estado,
                    s.pagamento.cpf, s.pagamento.rg, s.pagamento.banco, s.pagamento.agencia,
                    s.pagamento.conta]
    if s.tipo == "aluno":
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not (v or "").strip() for v in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp and not re.fullmatch(r"\d+", s.n_usp or ""):
        erros.append("N. USP deve conter apenas números")
    if s.pagamento.agencia and not re.fullmatch(r"\d+", s.pagamento.agencia or ""):
        erros.append("Número da agência deve conter apenas números")

    m = re.search(r"\d+", s.valor_solicitado or "")
    centavos = int(m.group()) if m else 0
    if centavos <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = s.email or ""
    if email and ("@" not in email or not email.split("@")[-1].strip() or "." not in email.split("@")[-1]):
        erros.append("E-mail inválido")

    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.pagamento.cpf or ""):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not validar_cpf(s.pagamento.cpf):
        erros.append("CPF inválido")

    if not re.fullmatch(r"\d{5}-\d{3}", s.endereco.cep or ""):
        erros.append("CEP deve estar no formato 00000-000")

    if not validar_data(s.endereco.data_nascimento or ""):
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.endereco.data_nascimento or ""):
            erros.append("Data de nascimento inválida")
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if erros:
        return JSONResponse(status_code=400, content={"ok": False, "erros": erros})

    # Gera o ofício
    linhas = []
    linhas.append(f"Interessada(o): {s.nome_completo} - {s.n_usp}")
    linhas.append(f"E-mail: {s.email}")
    if s.tipo == "aluno":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    linhas.append("")
    linhas.append(f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.nome_evento}")
    linhas.append(f"Período: {s.periodo}")
    linhas.append(f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}")
    if s.link_evento and s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.append(f"Apresentação de trabalho: {s.apresentacao}")
    linhas.append(f"Valor solicitado: {formatar_valor(centavos)}")
    linhas.append(f"Detalhamento: {s.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.endereco.logradouro}, {s.endereco.numero}")
    if s.endereco.complemento and s.endereco.complemento.strip():
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

    return {"ok": True, "oficio": "\n".join(linhas)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
