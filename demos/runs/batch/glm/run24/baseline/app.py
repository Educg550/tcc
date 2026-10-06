"""Backend FastAPI do formulário de auxílio financeiro da Pós-Graduação do IME-USP.

Recebe a solicitação enviada, decide se ela é válida e devolve ao frontend
as mensagens de erro e o ofício redigido. Não grava nada.
"""

from datetime import date
import re

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


# ---------------------------------------------------------------------------
# Modelos de dados
# ---------------------------------------------------------------------------


class Solicitacao(BaseModel):
    """Dados de uma solicitação de auxílio, enviados pelo frontend."""

    tipo: str  # "alunos" ou "docentes"

    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_de_auxilio: str = ""
    email: str = ""
    nome_do_evento: str = ""
    periodo_do_evento: str = ""
    cidade_do_evento: str = ""
    estado_do_evento: str = ""
    pais_do_evento: str = ""
    link_do_evento: str = ""
    valor_solicitado: str = ""
    detalhamento_do_pedido: str = ""
    ira_apresentar_trabalho: str = ""

    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""

    data_de_nascimento: str = ""
    cpf: str = ""
    rg: str = ""
    nome_do_banco: str = ""
    numero_da_agencia: str = ""
    numero_da_conta: str = ""


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s.]+(\.[^@\s.]+)+$")


def cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores de um CPF formatado."""
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(d * (i + 1 - j) for j, d in enumerate(digitos[:i]))
        resto = (soma * 10) % 11
        if resto % 10 != digitos[i]:
            return False
    return True


def _dia_no_mes(dia: int, mes: int, ano: int) -> bool:
    if mes < 1 or mes > 12:
        return False
    if mes == 2:
        limite = 29 if (ano % 4 == 0 and ano % 100 != 0) or ano % 400 == 0 else 28
    elif mes in (4, 6, 9, 11):
        limite = 30
    else:
        limite = 31
    return 1 <= dia <= limite


def validar(s: Solicitacao) -> list[str]:
    """Devolve a lista de mensagens de erro; vazia significa solicitação válida."""
    erros: list[str] = []

    obrigatórios = [
        s.nome_completo, s.n_usp, s.programa, s.email,
        s.nome_do_evento, s.periodo_do_evento, s.cidade_do_evento,
        s.estado_do_evento, s.pais_do_evento, s.valor_solicitado,
        s.detalhamento_do_pedido, s.ira_apresentar_trabalho,
        s.logradouro, s.numero, s.bairro, s.cep, s.cidade, s.estado,
        s.data_de_nascimento, s.cpf, s.rg, s.nome_do_banco,
        s.numero_da_agencia, s.numero_da_conta,
    ]
    if s.tipo == "alunos":
        obrigatórios += [s.nivel, s.tipo_de_auxilio]
    if not all(campo.strip() for campo in obrigatórios):
        erros.append("Preencha todos os campos")

    if s.n_usp and not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.numero_da_agencia and not s.numero_da_agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor_solicitado and not _valor_em_centavos(s.valor_solicitado):
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email and not RE_EMAIL.fullmatch(s.email.strip()):
        erros.append("E-mail inválido")
    if s.cpf and not RE_CPF.fullmatch(s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif s.cpf and not cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if s.cep and not RE_CEP.fullmatch(s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if s.data_de_nascimento and not RE_DATA.fullmatch(s.data_de_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif s.data_de_nascimento and not _dia_no_mes(
        int(s.data_de_nascimento[:2]),
        int(s.data_de_nascimento[3:5]),
        int(s.data_de_nascimento[6:]),
    ):
        erros.append("Data de nascimento inválida")

    return erros


def _valor_em_centavos(valor: str) -> int | None:
    """Converte "R$ 1.500,00" para 150000; None se não for natural > 0."""
    digitos = "".join(c for c in valor if c.isdigit())
    if not digitos or not RE_MOEDA.fullmatch(valor.strip()):
        return None
    centavos = int(digitos)
    return centavos if centavos > 0 else None


RE_MOEDA = re.compile(r"^R\$\s\d{1,3}(\.\d{3})*(,\d{2})?$")


# ---------------------------------------------------------------------------
# Formatação e geração do ofício
# ---------------------------------------------------------------------------


def formatar_moeda(centavos: int) -> str:
    """150000 -> "R$ 1.500,00", na convenção brasileira."""
    texto = f"{centavos:,}".replace(",", ".")
    return f"R$ {texto[:-3]},{texto[-2:]}"


def gerar_oficio(s: Solicitacao) -> str:
    """Redige o ofício substituindo os marcadores pelos dados informados."""
    valor = formatar_moeda(_valor_em_centavos(s.valor_solicitado) or 0)
    linhas: list[str] = []

    linhas.append(f"Interessada(o): {s.nome_completo} - {s.n_usp}")
    linhas.append(f"E-mail: {s.email}")
    if s.tipo == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_de_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    linhampty = linhas.append  # apelido curto p/ manter as linhas legíveis
    linhas.append("")
    linhas.append(
        "A CCP-" + s.programa + " aprovou na data de hoje, a solicitação de auxílio "
        "financeiro para a interessada(o) acima, conforme segue:"
    )
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.nome_do_evento}")
    linhas.append(f"Período: {s.periodo_do_evento}")
    local = f"{s.cidade_do_evento} - {s.estado_do_evento} - {s.pais_do_evento}"
    linhas.append(f"Local: {local}")
    if s.link_do_evento.strip():
        linhas.append(f"Link do evento: {s.link_do_evento}")
    linhas.append(f"Apresentação de trabalho: {s.ira_apresentar_trabalho}")
    linhas.append(f"Valor solicitado: {valor}")
    linhas.append(f"Detalhamento: {s.detalhamento_do_pedido}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.logradouro}, {s.numero}")
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas.append(f"CEP: {s.cep}")
    linhas.append(f"{s.bairro}, {s.cidade} - {s.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.data_de_nascimento}")
    linhas.append(f"CPF: {s.cpf}")
    linhas.append(f"RG / RNM: {s.rg}")
    linhas.append(f"Banco: {s.nome_do_banco}")
    linhas.append(f"Agência: {s.numero_da_agencia}")
    linhas.append(f"Conta: {s.numero_da_conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "date": date.today().isoformat()}


@app.post("/api/solicitacao")
def processar(s: Solicitacao) -> dict:
    erros = validar(s)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "erros": [], "oficio": gerar_oficio(s)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
