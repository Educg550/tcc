"""Solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

O frontend vive em index.html, style.css e app.js, servidos como arquivos
estáticos. Este módulo recebe a solicitação enviada, decide se ela é válida
e devolve o ofício já redigido. Nada é gravado: a solicitação se encerra na
resposta.
"""
import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent

app = FastAPI()


@app.get("/")
def indice():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css; charset=utf-8")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript; charset=utf-8")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


class Solicitacao(BaseModel):
    """Campos do formulário; os ausentes chegam como string vazia."""

    aba: str = "ALUNOS"
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade: str = ""
    estado: str = ""
    pais: str = ""
    link: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade_end: str = ""
    estado_end: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade",
    "estado", "pais", "valor", "detalhamento", "apresentacao", "nascimento",
    "logradouro", "numero", "bairro", "cep", "cidade_end", "estado_end",
    "cpf", "rg", "banco", "agencia", "conta",
]


def _centavos(valor: str) -> int:
    """Converte o valor digitado em centavos; 0 se não der para converter."""
    texto = valor.strip().removeprefix("R$").strip().replace(".", "")
    reais, _, centavos = texto.partition(",")
    try:
        return int(reais or "0") * 100 + int((centavos[:2] + "00")[:2])
    except ValueError:
        return 0


def _moeda(centavos: int) -> str:
    """Formata centavos em moeda brasileira, como R$ 1.500,00."""
    reais, centavos = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{centavos:02d}"


def _cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores contra os nove primeiros."""
    numeros = [int(c) for c in cpf if c.isdigit()]
    for quantidade in (9, 10):
        soma = sum(
            digito * (quantidade + 1 - posicao)
            for posicao, digito in enumerate(numeros[:quantidade])
        )
        if soma * 10 % 11 % 10 != numeros[quantidade]:
            return False
    return True


def _data_valida(data: str) -> bool:
    """Confere se dd/mm/aaaa é uma data que existe no calendário."""
    dia, mes, ano = (int(parte) for parte in data.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _validar(solicitacao: Solicitacao) -> list[str]:
    erros = []
    if solicitacao.aba == "DOCENTES":
        obrigatorios = OBRIGATORIOS
    else:
        obrigatorios = OBRIGATORIOS + ["nivel", "tipo"]
    if any(not getattr(solicitacao, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if solicitacao.n_usp and not solicitacao.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if solicitacao.agencia and not solicitacao.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if solicitacao.valor and _centavos(solicitacao.valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if solicitacao.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", solicitacao.email):
        erros.append("E-mail inválido")
    if solicitacao.cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", solicitacao.cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(solicitacao.cpf):
            erros.append("CPF inválido")
    if solicitacao.cep and not re.fullmatch(r"\d{5}-\d{3}", solicitacao.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if solicitacao.nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", solicitacao.nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(solicitacao.nascimento):
            erros.append("Data de nascimento inválida")
    return erros


def _oficio(solicitacao: Solicitacao) -> str:
    s = solicitacao
    if s.aba == "DOCENTES":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    linhas = [
        f"Interessada(o): {s.nome} - {s.n_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
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
        f"Valor solicitado: {_moeda(_centavos(s.valor))}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade_end} - {s.estado_end}",
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


@app.post("/api/solicitacao")
def criar_solicitacao(solicitacao: Solicitacao):
    """Devolve o ofício redigido, ou as mensagens de erro que se aplicam."""
    erros = _validar(solicitacao)
    if erros:
        return JSONResponse(status_code=400, content={"ok": False, "erros": erros})
    return {"ok": True, "oficio": _oficio(solicitacao)}
