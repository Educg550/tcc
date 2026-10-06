"""Validação dos campos da solicitação."""

import re

from util import validar_cpf_digitos, validar_data

PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

OBRIGATORIOS = {
    "alunos": [
        "nome", "nusp", "programa", "nivel", "tipo", "email",
        "evento_nome", "evento_periodo", "evento_cidade", "evento_estado",
        "evento_pais", "valor", "detalhamento", "apresentacao", "nascimento",
        "logradouro", "numero", "bairro", "cep", "cidade", "estado", "cpf",
        "rg", "banco", "agencia", "conta",
    ],
    "docentes": [
        "nome", "nusp", "programa", "email", "evento_nome", "evento_periodo",
        "evento_cidade", "evento_estado", "evento_pais", "valor",
        "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
        "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco",
        "agencia", "conta",
    ],
}


def validar(aba, c):
    erros = []
    for campo in OBRIGATORIOS[aba]:
        if not c.get(campo, "").strip():
            erros.append("Preencha todos os campos")
            break
    if not c.get("nusp", "").strip().isdigit():
        erros.append("N. USP deve conter apenas números")
    if not c.get("agencia", "").strip().isdigit():
        erros.append("Número da agência deve conter apenas números")
    try:
        valor = int(c.get("valor", "").strip())
    except ValueError:
        valor = 0
    if valor <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not PADRAO_EMAIL.match(c.get("email", "").strip()):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", c.get("cpf", "").strip()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not validar_cpf_digitos(c["cpf"]):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", c.get("cep", "").strip()):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", c.get("nascimento", "").strip()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not validar_data(c["nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros
