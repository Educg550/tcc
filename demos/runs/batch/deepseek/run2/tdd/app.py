import re
from datetime import datetime
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
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
    detalhamento_pedido: str = ""
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
    numero_agencia: str = ""
    numero_conta: str = ""


OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento_pedido",
    "apresentacao_trabalho",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg_rnm",
    "nome_banco",
    "numero_agencia",
    "numero_conta",
]

CPF_RE = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
CEP_RE = re.compile(r"\d{5}-\d{3}")
DATA_RE = re.compile(r"\d{2}/\d{2}/\d{4}")
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def _cpf_valido(cpf: str) -> bool:
    numeros = [int(digito) for digito in _digitos(cpf)]
    for tamanho in (9, 10):
        soma = sum(numeros[i] * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10 % 11) % 10 != numeros[tamanho]:
            return False
    return True


def _validar(dados: Solicitacao, aluno: bool) -> list[str]:
    erros: list[str] = []

    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if aluno else [])
    if any(getattr(dados, campo).strip() == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if dados.n_usp and not dados.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if dados.numero_agencia and not dados.numero_agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if dados.valor_solicitado and int(_digitos(dados.valor_solicitado) or "0") <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if dados.email and not EMAIL_RE.fullmatch(dados.email):
        erros.append("E-mail inválido")
    if dados.cpf:
        if not CPF_RE.fullmatch(dados.cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(dados.cpf):
            erros.append("CPF inválido")
    if dados.cep and not CEP_RE.fullmatch(dados.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if dados.data_nascimento:
        if not DATA_RE.fullmatch(dados.data_nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(dados.data_nascimento, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _montar_oficio(dados: Solicitacao, aluno: bool) -> str:
    if aluno:
        assunto = f"Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}"
        programa = f"{dados.programa} - {dados.nivel}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = dados.programa

    linhas = [
        f"Interessada(o): {dados.nome_completo} - {dados.n_usp}",
        f"E-mail: {dados.email}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.nome_evento}",
        f"Período: {dados.periodo_evento}",
        f"Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}",
    ]
    if dados.link_evento:
        linhas.append(f"Link do evento: {dados.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {dados.apresentacao_trabalho}",
        f"Valor solicitado: {dados.valor_solicitado}",
        f"Detalhamento: {dados.detalhamento_pedido}",
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
        f"Data de nascimento: {dados.data_nascimento}",
        f"CPF: {dados.cpf}",
        f"RG / RNM: {dados.rg_rnm}",
        f"Banco: {dados.nome_banco}",
        f"Agência: {dados.numero_agencia}",
        f"Conta: {dados.numero_conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


@app.post("/solicitar")
def solicitar(dados: Solicitacao):
    aluno = bool(dados.nivel or dados.tipo_auxilio)
    erros = _validar(dados, aluno)
    if erros:
        corpo = "".join(f"<p>{escape(mensagem)}</p>" for mensagem in erros)
        return HTMLResponse(f'<div class="erros" role="alert">{corpo}</div>', status_code=400)

    oficio = _montar_oficio(dados, aluno)
    return HTMLResponse(
        '<div class="confirmacao">'
        "<h2>Solicitação registrada</h2>"
        f'<pre class="oficio">{escape(oficio)}</pre>'
        "</div>"
    )


app.mount("/assets", StaticFiles(directory=str(BASE / "assets"), check_dir=False), name="assets")
