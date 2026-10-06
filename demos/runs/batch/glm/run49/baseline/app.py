"""Backend FastAPI da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""

from datetime import date

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

VALID_TIPOS = {"Participação em evento", "Banca de exame ou defesa", "Outro"}
VALID_NIVEIS = {"Mestrado", "Doutorado"}
VALID_APRESENTACAO = {
    "Pôster",
    "Apresentação oral",
    "Outra",
    "Não irá apresentar trabalho",
}


def _somente_digitos(valor):
    return valor.isdigit() if valor else False


def _email_valido(valor):
    if "@" not in valor:
        return False
    usuario, dominio = valor.rsplit("@", 1)
    return usuario != "" and dominio != "" and "." in dominio


def _cpf_valido(valor):
    digitos = [int(c) for c in valor if c.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    soma = sum(digitos[i] * (10 - i) for i in range(9))
    dv1 = (soma * 10 % 11) % 10
    soma = sum(digitos[i] * (11 - i) for i in range(10))
    dv2 = (soma * 10 % 11) % 10
    return dv1 == digitos[9] and dv2 == digitos[10]


def _data_valida(valor):
    try:
        dia, mes, ano = valor.split("/")
        date(int(ano), int(mes), int(dia))
        return True
    except (ValueError, IndexError):
        return False


def _valor_valido(valor):
    try:
        return float(valor) > 0
    except (TypeError, ValueError):
        return False


def validar(dados, aba):
    """Valida os dados de uma solicitação e retorna a lista de erros."""
    erros = []

    obrigatórios = [
        "nome_completo",
        "n_usp",
        "programa",
        "email",
        "evento_nome",
        "periodo",
        "cidade_evento",
        "estado_evento",
        "pais_evento",
        "valor",
        "detalhamento",
        "apresentacao",
        "nascimento",
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
    if aba == "alunos":
        obrigatórios += ["nivel", "tipo_auxilio"]

    if any(not str(dados.get(campo, "")).strip() for campo in obrigatórios):
        erros.append("Preencha todos os campos")

    if not _somente_digitos(dados.get("n_usp", "")):
        erros.append("N. USP deve conter apenas números")

    if not _somente_digitos(dados.get("agencia", "")):
        erros.append("Número da agência deve conter apenas números")

    if not _valor_valido(dados.get("valor")):
        erros.append("Valor solicitado deve ser maior que 0")

    if not _email_valido(dados.get("email", "")):
        erros.append("E-mail inválido")

    if len(dados.get("cpf", "")) != 14 or not _cpf_valido(dados.get("cpf", "")):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(dados.get("cpf", "")):
        erros.append("CPF inválido")

    if len(dados.get("cep", "")) != 9:
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get("nascimento", "")
    if len(nascimento) != 10 or not _data_valida(nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not _data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    if aba == "alunos" and dados.get("tipo_auxilio") not in VALID_TIPOS:
        erros.append("Tipo de auxílio inválido")
    if aba == "alunos" and dados.get("nivel") not in VALID_NIVEIS:
        erros.append("Nível inválido")

    return erros


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.post("/api/solicitar")
async def solicitar(dados: dict):
    """Recebe os dados do formulário, valida e gera o ofício."""
    aba = dados.get("aba", "alunos")
    erros = validar(dados, aba)
    if erros:
        return {"erros": erros}

    return {"erros": [], "oficio": "Ofício gerado com sucesso"}
