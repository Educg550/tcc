"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP.

A aplicação valida a solicitação recebida e devolve o ofício já redigido.
Sem persistência: a solicitação se encerra na resposta.
"""

import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

MENSAGENS = {
    "faltando": "Preencha todos os campos",
    "n_usp": "N. USP deve conter apenas números",
    "agencia": "Número da agência deve conter apenas números",
    "valor": "Valor solicitado deve ser maior que 0",
    "email": "E-mail inválido",
    "cpf_formato": "CPF deve estar no formato 000.000.000-00",
    "cep": "CEP deve estar no formato 00000-000",
    "data_formato": "Data de nascimento deve estar no formato dd/mm/aaaa",
    "cpf_invalido": "CPF inválido",
    "data_invalida": "Data de nascimento inválida",
}

# Campos obrigatórios comuns às duas abas.
OBRIGATORIOS = {
    "nome": "Preencha todos os campos",
    "n_usp": "Preencha todos os campos",
    "programa": "Preencha todos os campos",
    "email": "Preencha todos os campos",
    "evento": "Preencha todos os campos",
    "periodo": "Preencha todos os campos",
    "cidade_evento": "Preencha todos os campos",
    "estado_evento": "Preencha todos os campos",
    "pais_evento": "Preencha todos os campos",
    "valor": "Preencha todos os campos",
    "detalhamento": "Preencha todos os campos",
    "apresentacao": "Preencha todos os campos",
    "nascimento": "Preencha todos os campos",
    "logradouro": "Preencha todos os campos",
    "numero": "Preencha todos os campos",
    "bairro": "Preencha todos os campos",
    "cep": "Preencha todos os campos",
    "cidade": "Preencha todos os campos",
    "estado": "Preencha todos os campos",
    "cpf": "Preencha todos os campos",
    "rg": "Preencha todos os campos",
    "banco": "Preencha todos os campos",
    "agencia": "Preencha todos os campos",
    "conta": "Preencha todos os campos",
}


def _so_digitos(texto):
    return bool(texto) and texto.isdigit()


def _cpf_valido(cpf):
    """Confere o formato e os dígitos verificadores do CPF."""
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    for i in (9, 10):
        resto = sum(d * peso for d, peso in zip(digitos[:i], range(i + 1, 1, -1))) % 11
        if resto < 2:
            if digitos[i] != 0:
                return False
        elif digitos[i] != 11 - resto:
            return False
    return True


def _data_valida(data):
    """Confere o formato dd/mm/aaaa e a existência da data."""
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return False
    dia, mes, ano = (int(p) for p in m.groups())
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _validar(dados):
    """Devolve todas as mensagens de erro que se aplicam, na ordem do requisito."""
    erros = []
    extras = {"nivel", "tipo"} if dados["aba"] == "alunos" else set()
    if any(not str(dados.get(c) or "").strip() for c in list(OBRIGATORIOS) + list(extras)):
        erros.append(MENSAGENS["faltando"])
    if dados["n_usp"] and not _so_digitos(dados["n_usp"]):
        erros.append(MENSAGENS["n_usp"])
    if dados["agencia"] and not _so_digitos(dados["agencia"]):
        erros.append(MENSAGENS["agencia"])
    if dados["valor"] and not (_so_digitos(dados["valor"]) and int(dados["valor"]) > 0):
        erros.append(MENSAGENS["valor"])
    if dados["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", dados["email"]):
        erros.append(MENSAGENS["email"])
    if dados["cpf"] and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", dados["cpf"]):
        erros.append(MENSAGENS["cpf_formato"])
    elif dados["cpf"] and not _cpf_valido(dados["cpf"]):
        erros.append(MENSAGENS["cpf_invalido"])
    if dados["cep"] and not re.fullmatch(r"\d{5}-\d{3}", dados["cep"]):
        erros.append(MENSAGENS["cep"])
    if dados["nascimento"] and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados["nascimento"]):
        erros.append(MENSAGENS["data_formato"])
    elif dados["nascimento"] and not _data_valida(dados["nascimento"]):
        erros.append(MENSAGENS["data_invalida"])
    return erros


def _formatar_valor(valor):
    """Converte dígitos em centavos para moeda brasileira."""
    centavos = int(valor)
    inteiro, resto = divmod(centavos, 100)
    return f"R$ {inteiro:,}." + f"{resto:02d}".replace(",", ".")


def _formatar_valor(valor):
    """Converte dígitos em centavos para o formato R$ 1.500,00."""
    inteiro, centavos = divmod(int(valor), 100)
    milhar = f"{inteiro:,}".replace(",", ".")
    return f"R$ {milhar},{centavos:02d}"


def _oficio(dados):
    """Redige o ofício com os dados no lugar dos marcadores."""
    valor = _formatar_valor(dados["valor"])
    if dados["aba"] == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link"].strip():
        linhas.append(f"Link do evento: {dados['link']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados["complemento"].strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def index():
    return FileResponse("index.html")


@app.get("/api/programas")
def programas():
    return {
        "programas": [
            "Matemática",
            "Estatística",
            "Ciência da Computação",
        ]
    }


@app.post("/api/solicitacao")
async def solicitacao(solicitacao: dict):
    """Valida a solicitação e devolve o ofício, ou as mensagens de erro."""
    campos_texto = [
        "aba", "nome", "n_usp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
        "apresentacao", "nascimento", "logradouro", "numero", "complemento",
        "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia",
        "conta", "link", "nivel", "tipo",
    ]
    dados = {c: str(solicitacao.get(c) or "").strip() for c in campos_texto}
    if dados["aba"] not in ("alunos", "docentes"):
        return {"ok": False, "erros": ["Preencha todos os campos"]}
    erros = _validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(dados)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
