import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
    "pais_evento", "valor_solicitado", "detalhamento", "ira_apresentar",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "agencia", "numero_conta",
]

RE_EMAIL = re.compile(r"[^@\s]+@[^@\s]+")
RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_CEP = re.compile(r"\d{5}-\d{3}")
RE_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")


class Solicitacao(BaseModel):
    aba: str = "alunos"
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
    ira_apresentar: str = ""
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


def cpf_valido(texto: str) -> bool:
    digitos = re.sub(r"\D", "", texto)
    if len(digitos) != 11:
        return False
    soma = sum(int(digito) * peso for digito, peso in zip(digitos[:9], range(10, 1, -1)))
    dv1 = 11 - (soma % 11)
    if dv1 > 9:
        dv1 = 0
    soma = sum(int(digito) * peso for digito, peso in zip(digitos[:10], range(11, 1, -1)))
    dv2 = 11 - (soma % 11)
    if dv2 > 9:
        dv2 = 0
    return digitos[9:] == f"{dv1}{dv2}"


def data_valida(texto: str) -> bool:
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def centavos_de(texto: str) -> int:
    digitos = re.sub(r"\D", "", texto)
    return int(digitos) if digitos else 0


def valor_formatado(texto: str) -> str:
    centavos = centavos_de(texto)
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def erros_de(dados: Solicitacao) -> list[str]:
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if dados.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not getattr(dados, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if dados.n_usp.strip() and not dados.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if dados.agencia.strip() and not dados.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    if dados.valor_solicitado.strip() and centavos_de(dados.valor_solicitado) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if dados.email.strip() and not RE_EMAIL.fullmatch(dados.email.strip()):
        erros.append("E-mail inválido")
    cpf = dados.cpf.strip()
    if cpf:
        if not RE_CPF.fullmatch(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")
    if dados.cep.strip() and not RE_CEP.fullmatch(dados.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = dados.data_nascimento.strip()
    if nascimento:
        if not RE_DATA.fullmatch(nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(nascimento):
            erros.append("Data de nascimento inválida")
    return erros


def oficio_de(dados: Solicitacao) -> str:
    v = {
        campo: getattr(dados, campo).strip()
        for campo in (
            "nome_completo", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
            "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
            "pais_evento", "link_evento", "detalhamento", "ira_apresentar",
            "data_nascimento", "logradouro", "numero", "complemento", "bairro",
            "cep", "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "agencia",
            "numero_conta",
        )
    }
    if dados.aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {v['tipo_auxilio']}"
        programa = f"Programa: {v['programa']} - {v['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {v['programa']}"
    linhas = [
        f"Interessada(o): {v['nome_completo']} - {v['n_usp']}",
        f"E-mail: {v['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{v['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v['nome_evento']}",
        f"Período: {v['periodo_evento']}",
        f"Local: {v['cidade_evento']} - {v['estado_evento']} - {v['pais_evento']}",
    ]
    if v["link_evento"]:
        linhas.append(f"Link do evento: {v['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {v['ira_apresentar']}",
        f"Valor solicitado: {valor_formatado(dados.valor_solicitado)}",
        f"Detalhamento: {v['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v['logradouro']}, {v['numero']}",
    ]
    if v["complemento"]:
        linhas.append(f"Complemento: {v['complemento']}")
    linhas += [
        f"CEP: {v['cep']}",
        f"{v['bairro']}, {v['cidade']} - {v['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v['data_nascimento']}",
        f"CPF: {v['cpf']}",
        f"RG / RNM: {v['rg_rnm']}",
        f"Banco: {v['nome_banco']}",
        f"Agência: {v['agencia']}",
        f"Conta: {v['numero_conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


@app.post("/api/solicitacao")
def receber_solicitacao(dados: Solicitacao):
    erros = erros_de(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": oficio_de(dados)}


@app.get("/", include_in_schema=False)
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css", include_in_schema=False)
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js", include_in_schema=False)
def roteiro():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=str(RAIZ / "assets")), name="assets")
