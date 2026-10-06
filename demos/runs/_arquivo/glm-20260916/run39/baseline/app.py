import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    perfil: str = ""
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: str = ""
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


CAMPOS = [
    "perfil", "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "link_evento", "valor", "detalhamento", "apresentacao", "data_nascimento",
    "logradouro", "numero", "complemento", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]

OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def _so_digitos(texto):
    return bool(re.fullmatch(r"[0-9]+", texto))


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False

    def digito(base, peso_inicial):
        soma = sum(int(caractere) * (peso_inicial - posicao) for posicao, caractere in enumerate(base))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    verificador = digito(digitos[:9], 10) + digito(digitos[:10], 11)
    return digitos[9:] == verificador


def _data_valida(texto):
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _email_valido(email):
    partes = email.split("@")
    return len(partes) == 2 and partes[0] != "" and partes[1] != ""


def _formata_valor(centavos):
    texto = str(centavos).rjust(3, "0")
    reais = f"{int(texto[:-2]):,}".replace(",", ".")
    return f"R$ {reais},{texto[-2:]}"


def _validar(dados):
    erros = []
    obrigatorio = OBRIGATORIOS if dados["perfil"] == "docentes" else OBRIGATORIOS + ["nivel", "tipo_auxilio"]
    if any(not dados[campo] for campo in obrigatorio):
        erros.append("Preencha todos os campos")
    if dados["n_usp"] and not _so_digitos(dados["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if dados["agencia"] and not _so_digitos(dados["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    centavos = 0
    if dados["valor"]:
        digitos = re.sub(r"\D", "", dados["valor"])
        centavos = int(digitos) if digitos else 0
        if centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if dados["email"] and not _email_valido(dados["email"]):
        erros.append("E-mail inválido")
    cpf_no_formato = False
    if dados["cpf"]:
        if re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", dados["cpf"]):
            cpf_no_formato = True
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")
    if dados["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    data_no_formato = False
    if dados["data_nascimento"]:
        if re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", dados["data_nascimento"]):
            data_no_formato = True
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_no_formato and not _cpf_valido(dados["cpf"]):
        erros.append("CPF inválido")
    if data_no_formato and not _data_valida(dados["data_nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros, centavos


def _oficio(dados, centavos):
    if dados["perfil"] == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link_evento"]:
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas.extend([
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {_formata_valor(centavos)}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ])
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.extend([
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


@app.post("/api/solicitacao")
def registrar_solicitacao(solicitacao: Solicitacao):
    dados = {campo: getattr(solicitacao, campo).strip() for campo in CAMPOS}
    erros, centavos = _validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(dados, centavos)}


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def roteiro():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
