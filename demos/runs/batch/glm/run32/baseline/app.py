import re
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

BASE_DIR = Path(__file__).parent

app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


class Solicitacao(BaseModel):
    nome: str
    nusp: str
    programa: str
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str
    evento: str
    periodo: str
    cidade: str
    estado: str
    pais: str
    link: str
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    endereco_cidade: str
    endereco_estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str
    aba: str


def validar_cpf(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False
    if digitos == digitos[0] * 11:
        return False
    soma = sum(int(digitos[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11 % 10
    soma = sum(int(digitos[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11 % 10
    return d1 == int(digitos[9]) and d2 == int(digitos[10])


def validar_data(data: str) -> bool:
    try:
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def formatar_valor(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    centavos = digitos or "0"
    inteiro = int(centavos)
    reais = inteiro // 100
    cents = inteiro % 100
    parte_reais = str(reais)
    grupos = []
    while len(parte_reais) > 3:
        grupos.insert(0, parte_reais[-3:])
        parte_reais = parte_reais[:-3]
    grupos.insert(0, parte_reais)
    return f"R$ {'.'.join(grupos)},{cents:02d}"


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    alunos = s.aba == "alunos"

    obrigatorios = [
        s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo,
        s.cidade, s.estado, s.pais, s.detalhamento, s.apresentacao,
        s.logradouro, s.numero, s.bairro, s.cep, s.endereco_cidade,
        s.endereco_estado, s.cpf, s.rg, s.banco, s.agencia, s.conta,
        s.nascimento, s.valor,
    ]
    if alunos:
        obrigatorios += [s.nivel, s.tipo_auxilio]
    if any(not c.strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if s.nusp and not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    digitos_valor = re.sub(r"\D", "", s.valor) if s.valor else ""
    if s.valor and (not digitos_valor.isdigit() or int(digitos_valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.email):
        erros.append("E-mail inválido")
    if s.cpf and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif s.cpf and not validar_cpf(s.cpf):
        erros.append("CPF inválido")
    if s.cep and not re.match(r"^\d{5}-\d{3}$", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if s.nascimento and not re.match(r"^\d{2}/\d{2}/\d{4}$", s.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif s.nascimento and not validar_data(s.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(s: Solicitacao) -> str:
    alunos = s.aba == "alunos"
    hoje = date.today().strftime("%d/%m/%Y")
    tipo = s.tipo_auxilio if alunos else "Verba do programa"
    programa_linha = f"Programa: {s.programa} - {s.nivel}" if alunos else f"Programa: {s.programa}"

    linhas = [
        f"Interessada(o): {s.nome} - {s.nusp}",
        f"E-mail: {s.email}",
        f"Assunto: Solicitação de Auxílio Financeiro - {tipo}",
        programa_linha,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje ({hoje}), a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade} - {s.estado} - {s.pais}",
    ]
    if s.link.strip():
        linhas.append(f"Link do evento: {s.link}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {formatar_valor(s.valor)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.endereco_cidade} - {s.endereco_estado}",
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


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(s)}


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")
