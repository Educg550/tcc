"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import calendar
import datetime
import re

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


class Solicitacao(BaseModel):
    """Dados enviados pelo formulário. Sem persistência: a resposta encerra a solicitação."""

    aba: str
    nome_completo: str
    n_usp: str
    programa: str
    nivel: str = ""
    tipo_de_auxilio: str = ""
    email: str
    nome_do_evento: str
    periodo_do_evento: str
    cidade_do_evento: str
    estado_do_evento: str
    pais_do_evento: str
    link_do_evento: str
    valor_solicitado: str
    detalhamento_do_pedido: str
    apresentar_trabalho: str
    data_de_nascimento: str
    logradouro: str
    numero: str
    complemento: str
    bairro: str
    cep: str
    cidade: str
    estado: str
    cpf: str
    rg: str
    banco: str
    agencia: str
    conta: str


app = FastAPI()

OBRIGATORIOS_COMUNS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_do_evento",
    "periodo_do_evento",
    "cidade_do_evento",
    "estado_do_evento",
    "pais_do_evento",
    "valor_solicitado",
    "detalhamento_do_pedido",
    "apresentar_trabalho",
    "data_de_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]

OBRIGATORIOS_ALUNOS = OBRIGATORIOS_COMUNS + ["nivel", "tipo_de_auxilio"]


def _cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""

    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False
    if len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(d) * (i + 1 - j) for j, d in enumerate(digitos[:i]))
        resto = soma * 10 % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def _validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []

    obrigatorios = OBRIGATORIOS_ALUNOS if s.aba == "alunos" else OBRIGATORIOS_COMUNS
    if any(not getattr(s, c).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if s.n_usp and not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor_solicitado and not s.valor_solicitado.isdigit():
        erros.append("Valor solicitado deve ser maior que 0")
    if s.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", s.email):
        erros.append("E-mail inválido")

    digitos_cpf = re.sub(r"\D", "", s.cpf)
    if s.cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif s.cpf and not _cpf_valido(digitos_cpf):
        erros.append("CPF inválido")

    if s.cep and not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")

    if s.data_de_nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_de_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif s.data_de_nascimento:
        d, m, a = (int(p) for p in s.data_de_nascimento.split("/"))
        if not 1 <= m <= 12 or not 1 <= d <= calendar.monthrange(a, m)[1]:
            erros.append("Data de nascimento inválida")

    return erros


def _formatar_brl(centavos: str) -> str:
    if not centavos.isdigit():
        return ""
    centavos = centavos.lstrip("0") or "0"
    reais, resto = divmod(int(centavos), 100)
    texto = f"{reais:,}".replace(",", ".")
    return f"R$ {texto},{resto:02d}"


def _gerar_oficio(s: Solicitacao) -> str:
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    if s.aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_de_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"

    linhas = [
        f"Interessada(o): {s.nome_completo} - {s.n_usp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, {hoje}, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_do_evento}",
        f"Período: {s.periodo_do_evento}",
        f"Local: {s.cidade_do_evento} - {s.estado_do_evento} - {s.pais_do_evento}",
    ]
    if s.link_do_evento:
        linhas.append(f"Link do evento: {s.link_do_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentar_trabalho}",
        f"Valor solicitado: {_formatar_brl(s.valor_solicitado)}",
        f"Detalhamento: {s.detalhamento_do_pedido}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento:
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_de_nascimento}",
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
def enviar(solicitacao: Solicitacao):
    """Valida e devolve erros ou o ofício pronto; nada é gravado."""

    erros = _validar(solicitacao)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _gerar_oficio(solicitacao)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
