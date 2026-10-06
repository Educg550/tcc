"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


RAIZ = Path(__file__).resolve().parent

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str = ""
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
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


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


def valor_em_centavos(valor: str) -> int | None:
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return None
    return int(digitos)


def formata_valor(valor: str) -> str:
    centavos = valor_em_centavos(valor)
    inteiro, resto = divmod(centavos, 100)
    texto = f"{inteiro:,}".replace(",", ".")
    return f"R$ {texto},{resto:02d}"


def data_existe(data: str) -> bool:
    dia, mes, ano = (int(p) for p in data.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum(int(d) * peso for d, peso in zip(digitos[:9], range(10, 1, -1)))
    primeiro = (soma * 10) % 11 % 10
    soma = sum(int(d) * peso for d, peso in zip(digitos[:10], range(11, 1, -1)))
    segundo = (soma * 10) % 11 % 10
    return digitos[9] == str(primeiro) and digitos[10] == str(segundo)


def valida(d: Solicitacao) -> list[str]:
    erros = []
    faltando = [c for c in OBRIGATORIOS if not getattr(d, c).strip()]
    if d.tipo == "aluno" and not (d.nivel.strip() and d.tipo_auxilio.strip()):
        faltando.append("nivel")
    if faltando:
        erros.append("Preencha todos os campos")
        return erros
    if not d.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not d.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if valor_em_centavos(d.valor) is None or valor_em_centavos(d.valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in d.email or not d.email.split("@")[-1].strip():
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(d.cpf):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", d.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not data_existe(d.data_nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def gera_oficio(d: Solicitacao) -> str:
    if d.tipo == "docente":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {d.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio}"
        programa = f"Programa: {d.programa} - {d.nivel}"
    linhas = [
        f"Interessada(o): {d.nome} - {d.n_usp}",
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
        f"Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}",
    ]
    if d.link.strip():
        linhas.append(f"Link do evento: {d.link}")
    linhas += [
        f"Apresentação de trabalho: {d.apresentacao}",
        f"Valor solicitado: {formata_valor(d.valor)}",
        f"Detalhamento: {d.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro}, {d.numero}",
    ]
    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento}")
    linhas += [
        f"CEP: {d.cep}",
        f"{d.bairro}, {d.cidade} - {d.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.data_nascimento}",
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
def solicitacao(dados: Solicitacao):
    erros = valida(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gera_oficio(dados)}


app.mount("/", StaticFiles(directory=RAIZ, html=True), name="estaticos")
