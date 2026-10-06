import re
from calendar import monthrange
from datetime import date


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        resto = sum(d * (i + 1 - j) for j, d in enumerate(digitos[:i])) % 11
        if (resto < 2 and digitos[i] != 0) or (resto >= 2 and digitos[i] != 11 - resto):
            return False
    return True


def _data_valida(data: str) -> bool:
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return False
    dia, mes, ano = (int(p) for p in data.split("/"))
    return 1 <= mes <= 12 and 1 <= dia <= monthrange(ano, mes)[1]


def _email_valido(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def _valor_valido(valor: str) -> bool:
    digitos = re.sub(r"\D", "", valor)
    return bool(digitos) and digitos != "0" and digitos.isdigit()


def _centavos_para_moeda(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor)
    centavos = digitos[-2:]
    inteiros = digitos[:-2]
    partes = []
    while len(inteiros) > 3:
        partes.insert(0, inteiros[-3:])
        inteiros = inteiros[:-3]
    if inteiros:
        partes.insert(0, inteiros)
    return "R$ " + ".".join(partes) + "," + centavos


def _validar(d) -> list:
    erros = []
    obrigatorios = [
        "nome", "n_usp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta",
    ]
    if d.aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(getattr(d, c).strip() == "" for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if d.n_usp and not d.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if d.agencia and not d.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if d.valor and not _valor_valido(d.valor):
        erros.append("Valor solicitado deve ser maior que 0")
    if d.email and not _email_valido(d.email):
        erros.append("E-mail inválido")
    if d.cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", d.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif d.cpf and not _cpf_valido(d.cpf):
        erros.append("CPF inválido")
    if d.cep and not re.fullmatch(r"\d{5}-\d{3}", d.cep):
        erros.append("CEP deve estar no formato 00000-000")
    if d.nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", d.nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif d.nascimento and not _data_valida(d.nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def _oficio(d) -> str:
    assunto = (d.tipo_auxilio if d.aba == "alunos" else "Verba do programa")
    programa = d.programa + (" - " + d.nivel if d.aba == "alunos" else "")
    valor = _centavos_para_moeda(d.valor) if d.valor else ""
    hoje = date.today().strftime("%d/%m/%Y")
    linhas = [
        "Interessada(o): {} - {}".format(d.nome, d.n_usp),
        "E-mail: {}".format(d.email),
        "Assunto: Solicitação de Auxílio Financeiro - {}".format(assunto),
        "Programa: {}".format(programa),
        "",
        "A CCP-{} aprovou na data de hoje ({}), a solicitação de auxílio financeiro para a(o) interessada(o) acima, conforme segue:".format(d.programa, hoje),
        "",
        "Dados do evento",
        "Evento: {}".format(d.evento),
        "Período: {}".format(d.periodo),
        "Local: {} - {} - {}".format(d.cidade_evento, d.estado_evento, d.pais_evento),
    ]
    if d.link:
        linhas.append("Link do evento: {}".format(d.link))
    linhas += [
        "Apresentação de trabalho: {}".format(d.apresentacao),
        "Valor solicitado: {}".format(valor),
        "Detalhamento: {}".format(d.detalhamento),
        "",
        "Endereço da(o) interessada(o)",
        "{}, {}".format(d.logradouro, d.numero),
    ]
    if d.complemento:
        linhas.append("Complemento: {}".format(d.complemento))
    linhas += [
        "CEP: {}".format(d.cep),
        "{}, {} - {}".format(d.bairro, d.cidade, d.estado),
        "",
        "Dados para pagamento",
        "Data de nascimento: {}".format(d.nascimento),
        "CPF: {}".format(d.cpf),
        "RG / RNM: {}".format(d.rg),
        "Banco: {}".format(d.banco),
        "Agência: {}".format(d.agencia),
        "Conta: {}".format(d.conta),
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def validar_e_gerar(d):
    erros = _validar(d)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "erros": [], "oficio": _oficio(d)}
