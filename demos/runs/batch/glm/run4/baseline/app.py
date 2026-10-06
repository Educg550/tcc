"""Aplicação de solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


@app.get("/api/programas")
def programas() -> dict[str, list[str]]:
    return {
        "programas": [
            "ACIE",
            "Bioinformática",
            "Ciência da Computação",
            "Estatística",
            "Estatística e Experimentação Agrícola",
            "Matemática",
            "Matemática Aplicada",
        ]
    }


class Endereco(BaseModel):
    """Dados de endereço do(a) aluno(a)."""

    logradouro: str
    numero: str
    complemento: str = ""
    cidade: str
    uf: str
    cep: str


class Aluno(BaseModel):
    """Dados do(a) aluno(a)."""

    nome: str
    n_usp: str
    email: str
    endereco: Endereco


class Evento(BaseModel):
    """Dados do evento de interesse do(a) aluno(a)."""

    nome_evento: str
    data_inicio: str
    data_fim: str
    cidade: str
    uf: str
    valor: float


class Solicitacao(BaseModel):
    """Solicitação de auxílio de um(a) aluno(a)."""

    aluno: Aluno
    programa: str
    nivel: str
    evento: Evento
    email: str = ""


class SolicitacaoResponse(BaseModel):
    """Resposta de validação de uma solicitação."""

    ok: bool
    errors: list[str] = []


def _valida(s: Solicitacao) -> list[str]:
    """Valida uma solicitação e devolve os erros encontrados."""

    errors: list[str] = []

    if not s.aluno.nome.strip():
        errors.append("Informe o nome completo.")

    if not s.aluno.n_usp.isdigit():
        errors.append("Nº USP deve conter apenas dígitos.")

    if "@" not in s.email:
        errors.append("Informe um e-mail válido.")

    if s.nivel not in {"mestrado", "doutorado"}:
        errors.append("Informe o nível.")

    if s.evento.data_inicio != s.evento.data_fim:
        errors.append("Informe um período com datas iguais.")

    if s.evento.valor <= 0:
        errors.append("Informe um valor maior que zero.")

    if len(s.aluno.endereco.cep) != 9:
        errors.append("CEP deve ter exatamente 9 caracteres.")

    return errors


@app.post("/api/solicitacoes")
def valida_solicitacao(s: Solicitacao) -> SolicitacaoResponse:
    """Valida uma solicitação de auxílio financeiro."""

    return SolicitacaoResponse(ok=not (errors := _valida(s)), errors=errors)


# Servir os arquivos estáticos da interface por último, para que as rotas de
# API tenham precedência.
app.mount("/", StaticFiles(directory="public", html=True), name="public")
