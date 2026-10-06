from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import re
from datetime import date

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


class Dados(BaseModel):
    aba: str
    nomeCompleto: str
    numeroUSP: str
    programa: str
    nivel: str = ""
    tipoAuxilio: str = ""
    email: str
    nomeEvento: str
    periodo: str
    cidadeEvento: str
    estadoEvento: str
    paisEvento: str
    linkEvento: str = ""
    valor: str
    detalhamento: str
    apresentacao: str
    nascimento: str
    logradouro: str
    numeroEndereco: str
    complemento: str = ""
    bairro: str
    cep: str
    cidadeEndereco: str
    estadoEndereco: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


def validarCPF(cpf: str) -> bool:
    if not re.match(r"^\d{11}$", cpf):
        return False
    soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma1 * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != int(cpf[9]):
        return False
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma2 * 10) % 11
    if d2 == 10:
        d2 = 0
    return d2 == int(cpf[10])


def validar(data: Dados) -> dict:
    obrig = [data.nomeCompleto, data.numeroUSP, data.programa, data.email, data.nomeEvento, data.periodo,
             data.cidadeEvento, data.estadoEvento, data.paisEvento, data.valor, data.detalhamento, data.apresentacao,
             data.nascimento, data.logradouro, data.numeroEndereco, data.bairro, data.cep, data.cidadeEndereco,
             data.estadoEndereco, data.cpf, data.rg, data.banco, data.agencia, data.conta]
    if data.aba == "ALUNOS":
        obrig.extend([data.nivel, data.tipoAuxilio])
    msgs = []
    if any(c.strip() == "" for c in obrig):
        msgs.append("Preencha todos os campos")
    if not re.fullmatch(r"\d+", data.numeroUSP.strip()):
        msgs.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"\d+", data.agencia.strip()):
        msgs.append("Número da agência deve conter apenas números")
    if not re.fullmatch(r"R\$\s?\d{1,3}(\.\d{3})*(,\d{2})?", data.valor.strip()):
        msgs.append("Valor solicitado deve ser maior que 0")
    elif data.valor.strip() == "R$ 0,00":
        msgs.append("Valor solicitado deve ser maior que 0")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data.email.strip()):
        msgs.append("E-mail inválido")
    if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", data.cpf.strip()):
        msgs.append("CPF deve estar no formato 000.000.000-00")
    elif not validarCPF(data.cpf.replace(".", "").replace("-", "")):
        msgs.append("CPF inválido")
    if not re.match(r"^\d{5}-\d{3}$", data.cep.strip()):
        msgs.append("CEP deve estar no formato 00000-000")
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", data.nascimento.strip()):
        msgs.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            d, m, a = map(int, data.nascimento.split("/"))
            date(a, m, d)
        except ValueError:
            msgs.append("Data de nascimento inválida")
    return msgs


def gerarOficio(data: Dados) -> str:
    if data.aba == "ALUNOS":
        assunto = f"Solicitação de Auxílio Financeiro - {data.tipoAuxilio}"
        prog = f"{data.programa} - {data.nivel}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        prog = data.programa
    texto = f"Interessada(o): {data.nomeCompleto} - {data.numeroUSP}\n"
    texto += f"E-mail: {data.email}\n"
    texto += f"Assunto: {assunto}\n"
    texto += f"Programa: {prog}\n\n"
    texto += "A CCP-" + data.programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a\n"
    texto += "interessada(o) acima, conforme segue:\n\n"
    texto += "Dados do evento\n"
    texto += f"Evento: {data.nomeEvento}\n"
    texto += f"Período: {data.periodo}\n"
    texto += f"Local: {data.cidadeEvento} - {data.estadoEvento} - {data.paisEvento}\n"
    if data.linkEvento.strip():
        texto += f"Link do evento: {data.linkEvento}\n"
    texto += f"Apresentação de trabalho: {data.apresentacao}\n"
    texto += f"Valor solicitado: {data.valor}\n"
    texto += f"Detalhamento: {data.detalhamento}\n\n"
    texto += "Endereço da(o) interessada(o)\n"
    texto += f"{data.logradouro}, {data.numeroEndereco}\n"
    if data.complemento.strip():
        texto += f"Complemento: {data.complemento}\n"
    texto += f"CEP: {data.cep}\n"
    texto += f"{data.bairro}, {data.cidadeEndereco} - {data.estadoEndereco}\n\n"
    texto += "Dados para pagamento\n"
    texto += f"Data de nascimento: {data.nascimento}\n"
    texto += f"CPF: {data.cpf}\n"
    texto += f"RG / RNM: {data.rg}\n"
    texto += f"Banco: {data.banco}\n"
    texto += f"Agência: {data.agencia}\n"
    texto += f"Conta: {data.conta}\n\n"
    texto += "Encaminhe-se ao Serviço Financeiro para providências."
    return texto


@app.post("/api/solicitar")
def solicitar(data: Dados):
    msgs = validar(data)
    if msgs:
        return {"ok": False, "erros": msgs}
    return {"ok": True, "oficio": gerarOficio(data)}
