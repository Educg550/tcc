import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str = "alunos"
    nome: str = ""
    nusp: str = ""
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
    nascimento: str = ""
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


CAMPOS_COMUNS = [
    "nome", "nusp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
    "agencia", "conta",
]

RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
RE_DIGITOS = re.compile(r"\d+")


def cpf_valido(cpf: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", cpf)]
    for n in (9, 10):
        soma = sum(d[i] * (n + 1 - i) for i in range(n))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != d[n]:
            return False
    return True


def data_valida(s: str) -> bool:
    dia, mes, ano = (int(p) for p in s.split("/"))
    if mes < 1 or mes > 12:
        return False
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(d: Solicitacao):
    erros = []
    obrigatorios = list(CAMPOS_COMUNS)
    if d.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any((getattr(d, campo) or "").strip() == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if d.nusp and not RE_DIGITOS.fullmatch(d.nusp):
        erros.append("N. USP deve conter apenas números")

    if d.agencia and not RE_DIGITOS.fullmatch(d.agencia):
        erros.append("Número da agência deve conter apenas números")

    if d.valor:
        digitos = re.sub(r"\D", "", d.valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if d.email and not RE_EMAIL.fullmatch(d.email):
        erros.append("E-mail inválido")

    if d.cpf and not RE_CPF.fullmatch(d.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")

    if d.cep and not RE_CEP.fullmatch(d.cep):
        erros.append("CEP deve estar no formato 00000-000")

    if d.nascimento and not RE_DATA.fullmatch(d.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if d.cpf and RE_CPF.fullmatch(d.cpf) and not cpf_valido(d.cpf):
        erros.append("CPF inválido")

    if d.nascimento and RE_DATA.fullmatch(d.nascimento) and not data_valida(d.nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r"\D", "", valor))
    reais = centavos // 100
    cent = centavos % 100
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def gerar_oficio(d: Solicitacao) -> str:
    linhas = []
    linhas.append(f"Interessada(o): {d.nome} - {d.nusp}")
    linhas.append(f"E-mail: {d.email}")
    if d.aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}")
        linhas.append(f"Programa: {d.programa} - {d.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d.programa}")
    linhas.append("")
    linhas.append(
        f"A CCP-{d.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {d.evento}")
    linhas.append(f"Período: {d.periodo}")
    linhas.append(
        f"Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}"
    )
    if d.link_evento.strip():
        linhas.append(f"Link do evento: {d.link_evento}")
    linhas.append(f"Apresentação de trabalho: {d.apresentacao}")
    linhas.append(f"Valor solicitado: {formatar_moeda(d.valor)}")
    linhas.append(f"Detalhamento: {d.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d.logradouro}, {d.numero}")
    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento}")
    linhas.append(f"CEP: {d.cep}")
    linhas.append(f"{d.bairro}, {d.cidade} - {d.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d.nascimento}")
    linhas.append(f"CPF: {d.cpf}")
    linhas.append(f"RG / RNM: {d.rg}")
    linhas.append(f"Banco: {d.banco}")
    linhas.append(f"Agência: {d.agencia}")
    linhas.append(f"Conta: {d.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(dados)}


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html")


app.mount("/", StaticFiles(directory=BASE), name="static")
