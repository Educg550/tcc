import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    aba: str = "alunos"
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
    detalhamento: str = ""
    apresentacao: str = ""
    data_de_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg: str = ""
    nome_do_banco: str = ""
    numero_da_agencia: str = ""
    numero_da_conta: str = ""


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in re.sub(r"[^0-9]", "", cpf)]
    if len(set(digitos)) == 1:
        return False
    for posicao in (9, 10):
        soma = sum(d * (posicao + 1 - i) for i, d in enumerate(digitos[:posicao]))
        resto = soma % 11
        if (0 if resto < 2 else 11 - resto) != digitos[posicao]:
            return False
    return True


def _validar(s: Solicitacao) -> list[str]:
    erros = []

    obrigatorios = [
        s.nome_completo,
        s.n_usp,
        s.programa,
        s.email,
        s.nome_do_evento,
        s.periodo_do_evento,
        s.cidade_do_evento,
        s.estado_do_evento,
        s.pais_do_evento,
        s.valor_solicitado,
        s.detalhamento,
        s.apresentacao,
        s.data_de_nascimento,
        s.logradouro,
        s.numero,
        s.bairro,
        s.cep,
        s.cidade,
        s.estado,
        s.cpf,
        s.rg,
        s.nome_do_banco,
        s.numero_da_agencia,
        s.numero_da_conta,
    ]
    if s.aba != "docentes":
        obrigatorios += [s.nivel, s.tipo_de_auxilio]

    if any(not campo.strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not re.fullmatch(r"[0-9]+", s.n_usp.strip()):
        erros.append("N. USP deve conter apenas números")

    if s.numero_da_agencia.strip() and not re.fullmatch(r"[0-9]+", s.numero_da_agencia.strip()):
        erros.append("Número da agência deve conter apenas números")

    centavos = re.sub(r"[^0-9]", "", s.valor_solicitado)
    if not centavos or int(centavos) == 0:
        erros.append("Valor solicitado deve ser maior que 0")

    partes_email = s.email.strip().split("@")
    if len(partes_email) != 2 or not partes_email[0] or "." not in partes_email[1]:
        erros.append("E-mail inválido")

    cpf = s.cpf.strip()
    if not re.fullmatch(r"[0-9]{3}[.][0-9]{3}[.][0-9]{3}-[0-9]{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if not re.fullmatch(r"[0-9]{5}-[0-9]{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = s.data_de_nascimento.strip()
    if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dia, mes, ano = (int(parte) for parte in nascimento.split("/"))
        try:
            date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def _oficio(s: Solicitacao) -> str:
    if s.aba == "docentes":
        assunto = "Verba do programa"
        programa = s.programa
    else:
        assunto = s.tipo_de_auxilio
        programa = f"{s.programa} - {s.nivel}"

    linhas = [
        f"Interessada(o): {s.nome_completo} - {s.n_usp}",
        f"E-mail: {s.email}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_do_evento}",
        f"Período: {s.periodo_do_evento}",
        f"Local: {s.cidade_do_evento} - {s.estado_do_evento} - {s.pais_do_evento}",
    ]
    if s.link_do_evento.strip():
        linhas.append(f"Link do evento: {s.link_do_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {s.valor_solicitado}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ]
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas += [
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_de_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg}",
        f"Banco: {s.nome_do_banco}",
        f"Agência: {s.numero_da_agencia}",
        f"Conta: {s.numero_da_conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def enviar_solicitacao(solicitacao: Solicitacao):
    erros = _validar(solicitacao)
    if erros:
        return JSONResponse({"erros": erros, "oficio": ""})
    return JSONResponse({"erros": [], "oficio": _oficio(solicitacao)})


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css", include_in_schema=False)
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


@app.get("/assets/usp-logo.png", include_in_schema=False)
def logotipo():
    return FileResponse(RAIZ / "assets" / "usp-logo.png")
