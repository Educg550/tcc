"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
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


OBRIGATORIOS_COMUNS = [
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
    "detalhamento",
    "apresentacao",
    "data_nascimento",
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


def _valor_solicitado(valor):
    """Converte 'R$ 1.500,00' em 1500; None se não for número natural."""
    digitos = re.sub(r"[^0-9]", "", valor)
    if not digitos or not valor.strip():
        return None
    if re.search(r"[^0-9R$.,\s]", valor):
        return None
    centavos = int(digitos)
    reais = centavos // 100
    if re.search(r"[-−]", valor):
        return None
    return reais


def _formatar_moeda(valor):
    return "R$ {:,}".format(valor).replace(",", ".") + ",00"


def _cpf_valido(cpf):
    digitos = re.sub(r"[^0-9]", "", cpf)
    if len(digitos) != 11 or not digitos.isdigit():
        return False
    if digitos == digitos[0] * 11:
        return False
    soma = sum(int(d) * (10 - i) for i, d in enumerate(digitos[:9]))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    if int(digitos[9]) != d1:
        return False
    soma = sum(int(d) * (11 - i) for i, d in enumerate(digitos[:10]))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    return int(digitos[10]) == d2


def _data_valida(data):
    try:
        dia, mes, ano = (int(p) for p in data.split("/"))
        date(ano, mes, dia)
        return True
    except (ValueError, TypeError):
        return False


def _validar(s):
    erros = []
    obrigatorios = list(OBRIGATORIOS_COMUNS)
    if s.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not getattr(s, c).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if s.n_usp and not re.fullmatch(r"[0-9]+", s.n_usp):
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not re.fullmatch(r"[0-9]+", s.agencia):
        erros.append("Número da agência deve conter apenas números")
    valor = _valor_solicitado(s.valor_solicitado)
    if s.valor_solicitado and (valor is None or valor <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    email = s.email
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")
    if s.cpf and not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif s.cpf and not _cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if s.cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if s.data_nascimento and not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", s.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif s.data_nascimento and not _data_valida(s.data_nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def _oficio(s):
    linhas = [
        f"Interessada(o): {s.nome_completo} - {s.n_usp}",
        f"E-mail: {s.email}",
    ]
    if s.aba == "docentes":
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f"Programa: {s.programa}",
        ]
    else:
        linhas += [
            f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}",
            f"Programa: {s.programa} - {s.nivel}",
        ]
    linhas += [
        "",
        "A CCP-{0} aprovou na data de hoje, a solicitação de auxílio financeiro para a".format(s.programa),
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo_evento}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento:
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {s.valor_solicitado}",
        f"Detalhamento: {s.detalhamento}",
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
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitar(solicitacao: Solicitacao):
    erros = _validar(solicitacao)
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(solicitacao)}


@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory="."), name="estaticos")
