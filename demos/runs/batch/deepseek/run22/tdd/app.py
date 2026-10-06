import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


OBRIGATORIOS = [
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
    "apresentacao_trabalho",
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

OBRIGATORIOS_ALUNOS = ["nivel", "tipo_auxilio"]


@app.post("/api/solicitacao")
def solicitar(dados: dict):
    erros = _validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": _gerar_oficio(dados)}


def _texto(dados, chave):
    return str(dados.get(chave, "") or "")


def _validar(dados):
    erros = []
    aba = _texto(dados, "aba") or "alunos"
    obrigatorios = OBRIGATORIOS + (OBRIGATORIOS_ALUNOS if aba != "docentes" else [])
    if any(not _texto(dados, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor_solicitado")
    if valor and not _valor_valido(valor):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email and not _email_valido(email):
        erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = _texto(dados, "data_nascimento")
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return erros


def _valor_valido(valor):
    digitos = re.sub(r"\D", "", valor)
    return bool(digitos) and int(digitos) > 0


def _email_valido(email):
    if "@" not in email:
        return False
    dominio = email.split("@", 1)[1]
    return "." in dominio


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11:
        return False
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if digitos[posicao] != esperado:
            return False
    return True


def _data_valida(data):
    dia, mes, ano = (int(parte) for parte in data.split("/"))
    try:
        datetime(ano, mes, dia)
    except ValueError:
        return False
    return True


def _formatar_moeda(valor):
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return valor
    reais, centavos = divmod(int(digitos), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def _gerar_oficio(dados):
    aba = _texto(dados, "aba") or "alunos"
    programa = _texto(dados, "programa")

    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = programa
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {_texto(dados, 'tipo_auxilio')}"
        linha_programa = f"{programa} - {_texto(dados, 'nivel')}"

    linhas = [
        f"Interessada(o): {_texto(dados, 'nome_completo')} - {_texto(dados, 'n_usp')}",
        f"E-mail: {_texto(dados, 'email')}",
        f"Assunto: {assunto}",
        f"Programa: {linha_programa}",
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados, 'nome_evento')}",
        f"Período: {_texto(dados, 'periodo_evento')}",
        f"Local: {_texto(dados, 'cidade_evento')} - {_texto(dados, 'estado_evento')} - {_texto(dados, 'pais_evento')}",
    ]

    link = _texto(dados, "link_evento")
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {_texto(dados, 'apresentacao_trabalho')}",
        f"Valor solicitado: {_formatar_moeda(_texto(dados, 'valor_solicitado'))}",
        f"Detalhamento: {_texto(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_texto(dados, 'logradouro')}, {_texto(dados, 'numero')}",
    ]

    complemento = _texto(dados, "complemento")
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {_texto(dados, 'cep')}",
        f"{_texto(dados, 'bairro')}, {_texto(dados, 'cidade')} - {_texto(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_texto(dados, 'data_nascimento')}",
        f"CPF: {_texto(dados, 'cpf')}",
        f"RG / RNM: {_texto(dados, 'rg')}",
        f"Banco: {_texto(dados, 'banco')}",
        f"Agência: {_texto(dados, 'agencia')}",
        f"Conta: {_texto(dados, 'conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)
