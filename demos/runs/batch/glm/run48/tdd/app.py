"""Solicitação de auxílio financeiro — Pós-Graduação do IME-USP.

Backend FastAPI: valida a solicitação recebida, devolve o ofício já redigido
e serve os arquivos estáticos do frontend. Nada é gravado.
"""

import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DIRETORIO_ASSETS = BASE_DIR / "assets"
DIRETORIO_ASSETS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Solicitação de Auxílio Financeiro — Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=DIRETORIO_ASSETS), name="assets")


class Solicitacao(BaseModel):
    nome_completo: str = ""
    numero_usp: str = ""
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
    banco: str = ""
    agencia: str = ""
    conta: str = ""


class Digitos(BaseModel):
    digitos: str = ""


OBRIGATORIOS = (
    "nome_completo", "numero_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg_rnm", "banco", "agencia", "conta",
)
OBRIGATORIOS_ALUNOS = OBRIGATORIOS + ("nivel", "tipo_auxilio")

REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REGEX_CPF = re.compile(r"^[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}$")
REGEX_CEP = re.compile(r"^0[0-9]{4}-[0-9]{3}$")
REGEX_DATA = re.compile(r"^[0-9]{2}/[0-9]{2}/[0-9]{4}$")


def apenas_digitos(texto: str) -> str:
    return "".join(digito for digito in texto if digito in "0123456789")


def formatar_valor(bruto: str) -> str:
    digitos = apenas_digitos(bruto)
    if not digitos:
        return ""
    reais, centavos = divmod(int(digitos), 100)
    milhar = f"{reais:,}".replace(",", ".")
    return f"R$ {milhar},{centavos:02d}"


def formatar_cpf(bruto: str) -> str:
    digitos = apenas_digitos(bruto)[:11]
    formatado = digitos[:3]
    if len(digitos) > 3:
        formatado += "." + digitos[3:6]
    if len(digitos) > 6:
        formatado += "." + digitos[6:9]
    if len(digitos) > 9:
        formatado += "-" + digitos[9:11]
    return formatado


def formatar_cep(bruto: str) -> str:
    digitos = apenas_digitos(bruto)[:8]
    return digitos if len(digitos) <= 5 else digitos[:5] + "-" + digitos[5:]


def formatar_data(bruto: str) -> str:
    digitos = apenas_digitos(bruto)[:8]
    if len(digitos) <= 2:
        return digitos
    if len(digitos) <= 4:
        return digitos[:2] + "/" + digitos[2:]
    return digitos[:2] + "/" + digitos[2:4] + "/" + digitos[4:]


def digito_verificador(digitos, peso_inicial: int) -> int:
    soma = sum(digito * peso for digito, peso in zip(digitos, range(peso_inicial, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    numeros = apenas_digitos(cpf)
    if len(set(numeros)) == 1:
        return False
    digitos = [int(numero) for numero in numeros]
    return (
        digito_verificador(digitos[:9], 10) == digitos[9]
        and digito_verificador(digitos[:10], 11) == digitos[10]
    )


def validar(dados: Solicitacao, e_aluno: bool) -> list:
    erros = []
    obrigatorios = OBRIGATORIOS_ALUNOS if e_aluno else OBRIGATORIOS
    if any(getattr(dados, campo).strip() == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    numero_usp = dados.numero_usp.strip()
    if numero_usp and apenas_digitos(numero_usp) != numero_usp:
        erros.append("N. USP deve conter apenas números")
    agencia = dados.agencia.strip()
    if agencia and apenas_digitos(agencia) != agencia:
        erros.append("Número da agência deve conter apenas números")
    valor = dados.valor_solicitado.strip()
    if valor and (apenas_digitos(valor) != valor or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    email = dados.email.strip()
    if email and not REGEX_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")
    cpf = dados.cpf.strip()
    if cpf:
        if not REGEX_CPF.fullmatch(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")
    cep = dados.cep.strip()
    if cep and not REGEX_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = dados.data_nascimento.strip()
    if nascimento:
        if not REGEX_DATA.fullmatch(nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(nascimento, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(dados: Solicitacao, e_aluno: bool) -> str:
    if e_aluno:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados.tipo_auxilio}"
        programa = f"Programa: {dados.programa} - {dados.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados.programa}"
    linhas = [
        f"Interessada(o): {dados.nome_completo} - {dados.numero_usp}",
        f"E-mail: {dados.email}",
        assunto,
        programa,
        "",
        f"A CCP-{dados.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.nome_evento}",
        f"Período: {dados.periodo_evento}",
        f"Local: {dados.cidade_evento} - {dados.estado_evento} - {dados.pais_evento}",
    ]
    if dados.link_evento.strip():
        linhas.append(f"Link do evento: {dados.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {dados.apresentacao_trabalho}",
        f"Valor solicitado: {formatar_valor(dados.valor_solicitado)}",
        f"Detalhamento: {dados.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.logradouro}, {dados.numero}",
    ]
    if dados.complemento.strip():
        linhas.append(f"Complemento: {dados.complemento}")
    linhas += [
        f"CEP: {dados.cep}",
        f"{dados.bairro}, {dados.cidade} - {dados.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.data_nascimento}",
        f"CPF: {dados.cpf}",
        f"RG / RNM: {dados.rg_rnm}",
        f"Banco: {dados.banco}",
        f"Agência: {dados.agencia}",
        f"Conta: {dados.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE_DIR / "index.html", media_type="text/html")


@app.get("/app.js")
def app_js():
    return FileResponse(BASE_DIR / "app.js", media_type="application/javascript")


@app.get("/style.css")
def estilo_css():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.post("/solicitacao/alunos")
def solicitar_alunos(dados: Solicitacao):
    erros = validar(dados, e_aluno=True)
    if erros:
        return JSONResponse(status_code=422, content={"erros": erros})
    return {"oficio": gerar_oficio(dados, e_aluno=True)}


@app.post("/solicitacao/docentes")
def solicitar_docentes(dados: Solicitacao):
    erros = validar(dados, e_aluno=False)
    if erros:
        return JSONResponse(status_code=422, content={"erros": erros})
    return {"oficio": gerar_oficio(dados, e_aluno=False)}


@app.post("/formatacao/valor")
def formatacao_valor(dados: Digitos):
    return {"valor": formatar_valor(dados.digitos)}


@app.post("/formatacao/cpf")
def formatacao_cpf(dados: Digitos):
    return {"cpf": formatar_cpf(dados.digitos)}


@app.post("/formatacao/cep")
def formatacao_cep(dados: Digitos):
    return {"cep": formatar_cep(dados.digitos)}


@app.post("/formatacao/data")
def formatacao_data(dados: Digitos):
    return {"data": formatar_data(dados.digitos)}
