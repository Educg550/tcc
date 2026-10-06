from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import re
from datetime import date

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str  # "alunos" | "docentes"
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: Optional[str] = None
    tipo_auxilio: Optional[str] = None
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


def digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def formatar_valor(valor: str) -> str:
    centavos = int(valor)
    texto = str(centavos)
    partes = []
    while len(texto) > 3:
        partes.append(texto[-3:])
        texto = texto[:-3]
    partes.append(texto)
    return "R$ " + ".".join(reversed(partes)) + ",00"


def validar(data: Solicitacao) -> list[str]:
    erros = []
    obrigatorios = [
        data.nome, data.nusp, data.programa, data.email, data.evento,
        data.periodo, data.cidade_evento, data.estado_evento, data.pais_evento,
        data.valor, data.detalhamento, data.apresentacao, data.nascimento,
        data.logradouro, data.numero, data.bairro, data.cep, data.cidade,
        data.estado, data.cpf, data.rg, data.banco, data.agencia, data.conta,
    ]
    if data.tipo == "alunos":
        obrigatorios += [data.nivel, data.tipo_auxilio]
    if any(campo == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if data.nusp and not data.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if data.agencia and not data.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = digitos(data.valor)
    if data.valor and (not valor.isdigit() or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if data.email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data.email):
        erros.append("E-mail inválido")
    if data.cpf and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", data.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif data.cpf and not cpf_valido(data.cpf):
        erros.append("CPF inválido")
    if data.cep and not re.match(r"^\d{5}-\d{3}$", data.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if data.nascimento and not re.match(r"^\d{2}/\d{2}/\d{4}$", data.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data.nascimento and not data_valida(data.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def cpf_valido(cpf: str) -> bool:
    d = [int(c) for c in cpf if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in [9, 10]:
        s = sum((11 - i + k) % 10 * d[k] for k in range(i))
        # fórmula abaixo, correta:
        s = sum(d[k] * ((i + 1) - k) for k in range(i))
        r = (s * 10) % 11
        if r == 10:
            r = 0
        if d[i] != r:
            return False
    return True


def data_valida(texto: str) -> bool:
    d, m, a = [int(p) for p in texto.split("/")]
    try:
        date(a, m, d)
        return True
    except ValueError:
        return False


def gerar_oficio(data: Solicitacao) -> str:
    linhas = []
    linhas.append(f"Interessada(o): {data.nome} - {data.nusp}")
    linhas.append(f"E-mail: {data.email}")
    if data.tipo == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {data.tipo_auxilio}")
        linhas.append(f"Programa: {data.programa} - {data.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {data.programa}")
    linhas.append("")
    linhas.append("A CCP-" + data.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {data.evento}")
    linhas.append(f"Período: {data.periodo}")
    linhas.append(f"Local: {data.cidade_evento} - {data.estado_evento} - {data.pais_evento}")
    if data.link_evento:
        linhas.append(f"Link do evento: {data.link_evento}")
    linhas.append(f"Apresentação de trabalho: {data.apresentacao}")
    linhas.append(f"Valor solicitado: {formatar_valor(digitos(data.valor))}")
    linhas.append(f"Detalhamento: {data.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{data.logradouro}, {data.numero}")
    if data.complemento:
        linhas.append(f"Complemento: {data.complemento}")
    linhas.append(f"CEP: {data.cep}")
    linhas.append(f"{data.bairro}, {data.cidade} - {data.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {data.nascimento}")
    linhas.append(f"CPF: {data.cpf}")
    linhas.append(f"RG / RNM: {data.rg}")
    linhas.append(f"Banco: {data.banco}")
    linhas.append(f"Agência: {data.agencia}")
    linhas.append(f"Conta: {data.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber(data: Solicitacao):
    erros = validar(data)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(data)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
