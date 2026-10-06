"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
from datetime import date
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
    nome: str
    nusp: str
    programa: str
    nivel: str = ""
    tipo: str = ""
    email: str
    evento: str
    periodo: str
    cidade: str
    estado_evento: str
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
    cidade_end: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


OBRIGATORIOS = [
    "nome", "nusp", "programa", "email", "evento", "periodo", "cidade",
    "estado_evento", "pais", "valor", "detalhamento", "apresentacao",
    "nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf[:9]]
    for _ in range(2):
        soma = sum((len(digitos) + 1 - i) * d for i, d in enumerate(digitos))
        resto = soma % 11
        dv = 0 if resto < 2 else 11 - resto
        digitos.append(dv)
    return "".join(str(d) for d in digitos[9:]) == cpf[12:]


def _data_existe(data: str) -> bool:
    dia, mes, ano = int(data[:2]), int(data[3:5]), int(data[6:10])
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(d: Solicitacao) -> list[str]:
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if d.aba == "alunos":
        obrigatorios += ["nivel", "tipo"]
    if any(not getattr(d, c).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if d.nusp and not d.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if d.agencia and not d.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor_centavos = int(d.valor.replace(".", "").replace(",", "") or 0) \
        if re.fullmatch(r"R\$ [\d.,]+", d.valor) else 0
    if not valor_centavos > 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if d.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", d.email):
        erros.append("E-mail inválido")
    if d.cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif d.cpf and not _cpf_valido(d.cpf):
        erros.append("CPF inválido")
    if d.cep and not re.fullmatch(r"\d{5}-\d{3}", d.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if d.nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif d.nascimento and not _data_existe(d.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def oficio(d: Solicitacao) -> str:
    if d.aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {d.tipo}"
        programa = f"Programa: {d.programa} - {d.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {d.programa}"
    linhas = [
        f"Interessada(o): {d.nome} - {d.nusp}",
        f"E-mail: {d.email}",
        assunto,
        programa,
        "",
        "A CCP-" + d.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.evento}",
        f"Período: {d.periodo}",
        f"Local: {d.cidade} - {d.estado_evento} - {d.pais}",
    ]
    if d.link.strip():
        linhas.append(f"Link do evento: {d.link}")
    linhas += [
        f"Apresentação de trabalho: {d.apresentacao}",
        f"Valor solicitado: {d.valor}",
        f"Detalhamento: {d.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro}, {d.numero}",
    ]
    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento}")
    linhas += [
        f"CEP: {d.cep}",
        f"{d.bairro}, {d.cidade_end} - {d.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.nascimento}",
        f"CPF: {d.cpf}",
        f"RG / RNM: {d.rg}",
        f"Banco: {d.banco}",
        f"Agência: {d.agencia}",
        f"Conta: {d.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitar(d: Solicitacao):
    erros = validar(d)
    return {"erros": erros, "oficio": "" if erros else oficio(d)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
