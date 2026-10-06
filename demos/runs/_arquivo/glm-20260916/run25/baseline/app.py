import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    perfil: str = "alunos"
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
    rg_rnm: str = ""
    nome_banco: str = ""
    agencia: str = ""
    numero_conta: str = ""


OPCIONAIS = {"link_evento", "complemento"}
EXCLUSIVOS_ALUNOS = {"nivel", "tipo_auxilio"}


def cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * ((i + 1) - j) for j in range(i))
        if (soma * 10) % 11 % 10 != digitos[i]:
            return False
    return True


def formatar_moeda(valor: str) -> str:
    digitos = "".join(c for c in valor if c.isdigit()) or "0"
    centavos = int(digitos)
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    valores = s.model_dump()
    obrigatorios = [
        campo
        for campo in valores
        if campo != "perfil"
        and campo not in OPCIONAIS
        and not (s.perfil == "docentes" and campo in EXCLUSIVOS_ALUNOS)
    ]
    if any(not valores[campo].strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not s.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia.strip() and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    digitos_valor = "".join(c for c in s.valor_solicitado if c.isdigit())
    if s.valor_solicitado.strip() and (not digitos_valor or int(digitos_valor) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    if s.email.strip() and ("@" not in s.email or not s.email.split("@")[-1].strip()):
        erros.append("E-mail inválido")

    cpf_em_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf.strip()))
    if s.cpf.strip() and not cpf_em_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if s.cep.strip() and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    data_em_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento.strip()))
    if s.data_nascimento.strip() and not data_em_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_em_formato and not cpf_valido(s.cpf.strip()):
        erros.append("CPF inválido")
    if data_em_formato:
        try:
            datetime.strptime(s.data_nascimento.strip(), "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(s: Solicitacao) -> str:
    if s.perfil == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {s.programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        linha_programa = f"Programa: {s.programa} - {s.nivel}"

    linhas = [
        f"Interessada(o): {s.nome_completo} - {s.n_usp}",
        f"E-mail: {s.email}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.nome_evento}",
        f"Período: {s.periodo_evento}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {formatar_moeda(s.valor_solicitado)}",
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
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg_rnm}",
        f"Banco: {s.nome_banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.numero_conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": gerar_oficio(solicitacao)}


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
