import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_RE = re.compile(r"^\d{5}-\d{3}$")
DATA_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
DIGITS_RE = re.compile(r"^\d+$")

CAMPOS_ALUNOS = [
    "nome", "nusp", "programa", "nivel", "tipo", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo")]


def _clean(v):
    return (v or "").strip() if isinstance(v, str) else ""


def _digits(s):
    return re.sub(r"\D", "", s or "")


def _cpf_ok(cpf):
    d = _digits(cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    n = [int(c) for c in d]
    s1 = sum(n[i] * (10 - i) for i in range(9)) % 11
    if (0 if s1 < 2 else 11 - s1) != n[9]:
        return False
    s2 = sum(n[i] * (11 - i) for i in range(10)) % 11
    return (0 if s2 < 2 else 11 - s2) == n[10]


def _data_ok(v):
    m = DATA_RE.match(v)
    if not m:
        return False
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mo < 1 or mo > 12:
        return False
    dim = [31, 29 if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0) else 28,
           31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= d <= dim[mo - 1]


def validar(payload):
    aba = payload.get("aba")
    dados = payload.get("dados") or {}

    if aba == "docentes":
        obrig = CAMPOS_DOCENTES
        tipo = "docentes"
    else:
        obrig = CAMPOS_ALUNOS
        tipo = "alunos"

    campos = {k: _clean(dados.get(k)) for k in obrig + ["link", "complemento"]}
    erros = []

    if any(campos[k] == "" for k in obrig):
        erros.append("Preencha todos os campos")
    if campos["nusp"] and not DIGITS_RE.match(campos["nusp"]):
        erros.append("N. USP deve conter apenas n\u00fameros")
    if campos["agencia"] and not DIGITS_RE.match(campos["agencia"]):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")
    if campos["valor"]:
        dig = _digits(campos["valor"])
        if not dig or int(dig) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if campos["email"] and not EMAIL_RE.match(campos["email"]):
        erros.append("E-mail inv\u00e1lido")
    if campos["cpf"]:
        if not CPF_RE.match(campos["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_ok(campos["cpf"]):
            erros.append("CPF inv\u00e1lido")
    if campos["cep"] and not CEP_RE.match(campos["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if campos["nascimento"]:
        if not DATA_RE.match(campos["nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_ok(campos["nascimento"]):
            erros.append("Data de nascimento inv\u00e1lida")

    campos["tipo_aba"] = tipo
    return erros, campos
