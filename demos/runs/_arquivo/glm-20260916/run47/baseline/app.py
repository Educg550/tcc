import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

PASTA = Path(__file__).resolve().parent


class Dados(BaseModel):
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao_trabalho: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg_rnm: str = ""
    nome_banco: str = ""
    agencia: str = ""
    conta: str = ""


class Solicitacao(BaseModel):
    perfil: str = "alunos"
    dados: Dados = Dados()


app = FastAPI()


def so_digitos(texto: str) -> str:
    return re.sub(r"[^0-9]", "", texto)


def cpf_valido(cpf: str) -> bool:
    n = [int(c) for c in so_digitos(cpf)]
    if len(n) != 11:
        return False
    dv1 = (sum(a * b for a, b in zip(n[:9], range(10, 1, -1))) * 10) % 11 % 10
    dv2 = (sum(a * b for a, b in zip(n[:10], range(11, 1, -1))) * 10) % 11 % 10
    return n[9] == dv1 and n[10] == dv2


def data_valida(texto: str) -> bool:
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def email_valido(texto: str) -> bool:
    partes = texto.split("@")
    return len(partes) == 2 and partes[0] != "" and partes[1] != ""


def centavos(texto: str):
    digitos = so_digitos(texto)
    return int(digitos) if digitos else None


def validar(perfil: str, d: Dados) -> list:
    obrigatorios = [
        "nome_completo", "n_usp", "programa", "email",
        "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
        "pais_evento", "valor_solicitado", "detalhamento", "apresentacao_trabalho",
        "data_nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "agencia", "conta",
    ]
    if perfil == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not getattr(d, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if d.n_usp.strip() and not re.fullmatch(r"[0-9]+", d.n_usp.strip()):
        erros.append("N. USP deve conter apenas números")

    if d.agencia.strip() and not re.fullmatch(r"[0-9]+", d.agencia.strip()):
        erros.append("Número da agência deve conter apenas números")

    if d.valor_solicitado.strip():
        valor = centavos(d.valor_solicitado)
        if valor is None or valor == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if d.email.strip() and not email_valido(d.email.strip()):
        erros.append("E-mail inválido")

    cpf = d.cpf.strip()
    cpf_formatado = re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf) is not None
    if cpf and not cpf_formatado:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if d.cep.strip() and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", d.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    data = d.data_nascimento.strip()
    data_formatada = re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", data) is not None
    if data and not data_formatada:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formatado and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_formatada and not data_valida(data):
        erros.append("Data de nascimento inválida")

    return erros


def moeda(cent: int) -> str:
    inteiro = f"{cent // 100:,}".replace(",", ".")
    return f"R$ {inteiro},{cent % 100:02d}"


def redigir(perfil: str, d: Dados, cent: int) -> str:
    if perfil == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {d.programa.strip()}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {d.tipo_auxilio.strip()}"
        programa = f"Programa: {d.programa.strip()} - {d.nivel.strip()}"

    linhas = [
        f"Interessada(o): {d.nome_completo.strip()} - {d.n_usp.strip()}",
        f"E-mail: {d.email.strip()}",
        assunto,
        programa,
        "",
        f"A CCP-{d.programa.strip()} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.nome_evento.strip()}",
        f"Período: {d.periodo_evento.strip()}",
        f"Local: {d.cidade_evento.strip()} - {d.estado_evento.strip()} - {d.pais_evento.strip()}",
    ]
    if d.link_evento.strip():
        linhas.append(f"Link do evento: {d.link_evento.strip()}")
    linhas += [
        f"Apresentação de trabalho: {d.apresentacao_trabalho.strip()}",
        f"Valor solicitado: {moeda(cent)}",
        f"Detalhamento: {d.detalhamento.strip()}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro.strip()}, {d.numero.strip()}",
    ]
    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento.strip()}")
    linhas += [
        f"CEP: {d.cep.strip()}",
        f"{d.bairro.strip()}, {d.cidade.strip()} - {d.estado.strip()}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.data_nascimento.strip()}",
        f"CPF: {d.cpf.strip()}",
        f"RG / RNM: {d.rg_rnm.strip()}",
        f"Banco: {d.nome_banco.strip()}",
        f"Agência: {d.agencia.strip()}",
        f"Conta: {d.conta.strip()}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    perfil = "docentes" if solicitacao.perfil == "docentes" else "alunos"
    erros = validar(perfil, solicitacao.dados)
    if erros:
        return {"ok": False, "erros": erros}
    cent = centavos(solicitacao.dados.valor_solicitado) or 0
    return {"ok": True, "oficio": redigir(perfil, solicitacao.dados, cent)}


app.mount("/", StaticFiles(directory=PASTA, html=True), name="raiz")
