import re

def validar(s):
    erros = []
    obrigatorios = [s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo, s.cidade,
        s.estado_evento, s.pais, s.valor, s.detalhamento, s.apresentacao, s.nascimento,
        s.logradouro, s.numero, s.bairro, s.cep, s.cidade_end, s.estado, s.cpf, s.rg,
        s.banco, s.agencia, s.conta]
    if any(not c.strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = extrair_valor(s.valor)
    if valor is None or valor <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not email_valido(s.email):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not data_valida(s.nascimento):
        erros.append("Data de nascimento inválida")
    return erros

def extrair_valor(v):
    v = v.replace(".", "").replace(",", "").replace("R$", "").strip()
    return int(v) if v.isdigit() else None

def email_valido(e):
    return re.fullmatch(r"[^@]+@[^@]+\.[a-zA-Z]{2,}", e) is not None

def cpf_valido(cpf):
    d = [int(c) for c in cpf if c.isdigit()]
    if len(set(d)) == 1:
        return False
    soma = sum(d[i] * (10 - i) for i in range(9))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    if dv1 != d[9]:
        return False
    soma = sum(d[i] * (11 - i) for i in range(10))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return dv2 == d[10]

def data_valida(data):
    d, m, a = map(int, data.split("/"))
    if m < 1 or m > 12:
        return False
    dias = [31, 29 if bissexto(a) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= d <= dias[m - 1]

def bissexto(a):
    return a % 4 == 0 and (a % 100 != 0 or a % 400 == 0)
