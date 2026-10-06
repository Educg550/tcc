import re
import datetime


def validate(data):
    errors = []

    required_aluno = ["nome", "n_usp", "programa", "nivel", "tipo", "email", "evento", "periodo", "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta"]
    required_docente = ["nome", "n_usp", "programa", "email", "evento", "periodo", "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta"]

    fields = required_aluno if data.get("tipo_form") == "aluno" else required_docente

    missing = [k for k in fields if not str(data.get(k, "")).strip()]
    if missing:
        errors.append("Preencha todos os campos")

    if data.get("n_usp") and not str(data.get("n_usp", "")).strip().isdigit():
        errors.append("N. USP deve conter apenas números")

    if data.get("agencia") and not str(data.get("agencia", "")).strip().isdigit():
        errors.append("Número da agência deve conter apenas números")

    valor = str(data.get("valor", "")).replace(".", "").replace(",", ".")
    if data.get("valor") and (not valor.replace(".", "").isdigit() or float(valor) <= 0):
        errors.append("Valor solicitado deve ser maior que 0")

    email = str(data.get("email", ""))
    if email and ("@" not in email or email.startswith("@") or "." not in email.split("@")[-1]):
        errors.append("E-mail inválido")

    cpf = str(data.get("cpf", ""))
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            errors.append("CPF deve estar no formato 000.000.000-00")
        elif not _valid_cpf_digits(cpf):
            errors.append("CPF inválido")

    cep = str(data.get("cep", ""))
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        errors.append("CEP deve estar no formato 00000-000")

    nasc = str(data.get("nascimento", ""))
    if nasc:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nasc):
            errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            d, m, y = [int(x) for x in nasc.split("/")]
            try:
                datetime.date(y, m, d)
            except ValueError:
                errors.append("Data de nascimento inválida")

    return errors


def _valid_cpf_digits(cpf):
    digits = [int(c) for c in cpf if c.isdigit()]
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    a = sum(digits[i] * (10 - i) for i in range(9))
    d1 = (a * 10) % 11
    d1 = 0 if d1 == 10 else d1
    b = sum(digits[i] * (11 - i) for i in range(10))
    d2 = (b * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return digits[9] == d1 and digits[10] == d2
