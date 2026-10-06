import re
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


class Solicitacao(BaseModel):
    aba: str = ""
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_do_evento: str = ""
    periodo_do_evento: str = ""
    cidade_do_evento: str = ""
    estado_do_evento: str = ""
    pais_do_evento: str = ""
    link_do_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao_trabalho: str = ""
    data_de_nascimento: str = ""
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
    numero_agencia: str = ""
    numero_conta: str = ""


app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_do_evento",
    "periodo_do_evento", "cidade_do_evento", "estado_do_evento",
    "pais_do_evento", "valor_solicitado", "detalhamento",
    "apresentacao_trabalho", "data_de_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm",
    "nome_banco", "numero_agencia", "numero_conta",
]
ALUNOS = OBRIGATORIOS + ["nivel", "tipo_auxilio"]


def _cpf_valido(cpf: str) -> bool:
    num = [int(c) for c in cpf if c.isdigit()]
    if len(num) != 11:
        return False
    dv1 = (sum(num[i] * (10 - i) for i in range(9)) * 10 % 11) % 10
    dv2 = (sum(num[i] * (11 - i) for i in range(10)) * 10 % 11) % 10
    return num[9] == dv1 and num[10] == dv2


def _erros(dados: Solicitacao) -> list:
    obrigatorios = ALUNOS if dados.aba == "alunos" else OBRIGATORIOS
    erros = []
    if dados.aba not in ("alunos", "docentes") or any(
        not getattr(dados, campo) for campo in obrigatorios
    ):
        erros.append("Preencha todos os campos")
    if dados.n_usp and not dados.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if dados.numero_agencia and not dados.numero_agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if dados.valor_solicitado:
        centavos = re.sub(r"\D", "", dados.valor_solicitado)
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if dados.email:
        local, _, dominio = dados.email.partition("@")
        if not local or not dominio:
            erros.append("E-mail inválido")
    if dados.cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", dados.cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(dados.cpf):
            erros.append("CPF inválido")
    if dados.cep and not re.fullmatch(r"\d{5}-\d{3}", dados.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if dados.data_de_nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados.data_de_nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(dados.data_de_nascimento, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def _oficio(dados: Solicitacao) -> str:
    if dados.aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados.programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}"
        programa = f"Programa: {dados.programa} - {dados.nivel}"
    linhas = [
        f"Interessada(o): {dados.nome_completo} - {dados.n_usp}",
        f"E-mail: {dados.email}",
        f"Assunto: {assunto}",
        programa,
        "",
        f"A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.nome_do_evento}",
        f"Período: {dados.periodo_do_evento}",
        f"Local: {dados.cidade_do_evento} - {dados.estado_do_evento} - {dados.pais_do_evento}",
    ]
    if dados.link_do_evento:
        linhas.append(f"Link do evento: {dados.link_do_evento}")
    linhas += [
        f"Apresentação de trabalho: {dados.apresentacao_trabalho}",
        f"Valor solicitado: {dados.valor_solicitado}",
        f"Detalhamento: {dados.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.logradouro}, {dados.numero}",
    ]
    if dados.complemento:
        linhas.append(f"Complemento: {dados.complemento}")
    linhas += [
        f"CEP: {dados.cep}",
        f"{dados.bairro}, {dados.cidade} - {dados.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.data_de_nascimento}",
        f"CPF: {dados.cpf}",
        f"RG / RNM: {dados.rg_rnm}",
        f"Banco: {dados.nome_banco}",
        f"Agência: {dados.numero_agencia}",
        f"Conta: {dados.numero_conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(dados: Annotated[Solicitacao, Form()]) -> dict:
    erros = _erros(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(dados)}


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parent, html=True),
    name="raiz",
)
