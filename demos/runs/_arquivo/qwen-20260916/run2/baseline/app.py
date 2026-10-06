from typing import Optional

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import re
import unicodedata

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_RE = re.compile(r"^\d{5}-\d{3}$")
DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
ONLY_DIGITS_RE = re.compile(r"^\d+$")


def _is_blank(s):
    return s is None or unicodedata.normalize("NFC", s).strip() == ""


def _digits(s):
    return re.sub(r"\D", "", s or "")


def _validate_cpf(cpf):
    digits = _digits(cpf)
    if len(digits) != 11:
        return False
    s = sum(int(digits[i]) * (10 - i) for i in range(9)) % 11
    d1 = 0 if s < 2 else 11 - s
    s2 = sum(int(digits[i]) * (11 - i) for i in range(10)) % 11
    d2 = 0 if s2 < 2 else 11 - s2
    return int(digits[9]) == d1 and int(digits[10]) == d2


def _valid_date(d):
    m = DATE_RE.match(d)
    if not m:
        return False
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if month < 1 or month > 12:
        return False
    md = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        md[1] = 29
    return 1 <= day <= md[month - 1]


BASE_FIELDS = [
    "nome_completo",
    "nusp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentar_trabalho",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "nome_banco",
    "numero_agencia",
    "numero_conta",
]


def _build_oficio(nome_completo, nusp, email, assunto, programa, nivel, nome_evento,
                  periodo_evento, cidade_evento, estado_evento, pais_evento,
                  link_evento, apresentar_trabalho, valor_fmt, detalhamento,
                  logradouro, numero, complemento, cep, bairro, cidade, estado,
                  data_nascimento, cpf, rg, nome_banco, numero_agencia, numero_conta):
    lines = []
    lines.append(f"Interessada(o): {nome_completo} - {nusp}")
    lines.append(f"E-mail: {email}")
    lines.append(f"Assunto: Solicitação de Auxílio Financeiro - {assunto}")
    if nivel:
        lines.append(f"Programa: {programa} - {nivel}")
    else:
        lines.append(f"Programa: {programa}")
    lines.append("")
    lines.append("A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    lines.append("interessada(o) acima, conforme segue:")
    lines.append("")
    lines.append("Dados do evento")
    lines.append("Evento: " + nome_evento)
    lines.append("Período: " + periodo_evento)
    lines.append("Local: " + cidade_evento + " - " + estado_evento + " - " + pais_evento)
    if link_evento:
        lines.append("Link do evento: " + link_evento)
    lines.append("Apresentação de trabalho: " + apresentar_trabalho)
    lines.append("Valor solicitado: " + valor_fmt)
    lines.append("Detalhamento: " + detalhamento)
    lines.append("")
    lines.append("Endereço da(o) interessada(o)")
    lines.append(logradouro + ", " + numero)
    if complemento:
        lines.append("Complemento: " + complemento)
    lines.append("CEP: " + cep)
    lines.append(bairro + ", " + cidade + " - " + estado)
    lines.append("")
    lines.append("Dados para pagamento")
    lines.append("Data de nascimento: " + data_nascimento)
    lines.append("CPF: " + cpf)
    lines.append("RG / RNM: " + rg)
    lines.append("Banco: " + nome_banco)
    lines.append("Agência: " + numero_agencia)
    lines.append("Conta: " + numero_conta)
    lines.append("")
    lines.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(lines)


@app.post("/solicitacao", response_class=HTMLResponse)
async def solicitar(
    aba: str = Form("alunos"),
    nome_completo: str = Form(""),
    nusp: str = Form(""),
    programa: str = Form(""),
    nivel: Optional[str] = Form(None),
    tipo_auxilio: Optional[str] = Form(None),
    email: str = Form(""),
    nome_evento: str = Form(""),
    periodo_evento: str = Form(""),
    cidade_evento: str = Form(""),
    estado_evento: str = Form(""),
    pais_evento: str = Form(""),
    link_evento: Optional[str] = Form(None),
    valor_solicitado: str = Form(""),
    detalhamento: str = Form(""),
    apresentar_trabalho: str = Form(""),
    data_nascimento: str = Form(""),
    logradouro: str = Form(""),
    numero: str = Form(""),
    complemento: Optional[str] = Form(None),
    bairro: str = Form(""),
    cep: str = Form(""),
    cidade: str = Form(""),
    estado: str = Form(""),
    cpf: str = Form(""),
    rg: str = Form(""),
    nome_banco: str = Form(""),
    numero_agencia: str = Form(""),
    numero_conta: str = Form(""),
):
    errors = []

    if aba == "alunos":
        required = {
            "nome_completo": nome_completo,
            "nusp": nusp,
            "programa": programa,
            "nivel": nivel,
            "tipo_auxilio": tipo_auxilio,
            "email": email,
            "nome_evento": nome_evento,
            "periodo_evento": periodo_evento,
            "cidade_evento": cidade_evento,
            "estado_evento": estado_evento,
            "pais_evento": pais_evento,
            "valor_solicitado": valor_solicitado,
            "detalhamento": detalhamento,
            "apresentar_trabalho": apresentar_trabalho,
            "data_nascimento": data_nascimento,
            "logradouro": logradouro,
            "numero": numero,
            "bairro": bairro,
            "cep": cep,
            "cidade": cidade,
            "estado": estado,
            "cpf": cpf,
            "rg": rg,
            "nome_banco": nome_banco,
            "numero_agencia": numero_agencia,
            "numero_conta": numero_conta,
        }
    else:
        required = {
            "nome_completo": nome_completo,
            "nusp": nusp,
            "programa": programa,
            "email": email,
            "nome_evento": nome_evento,
            "periodo_evento": periodo_evento,
            "cidade_evento": cidade_evento,
            "estado_evento": estado_evento,
            "pais_evento": pais_evento,
            "valor_solicitado": valor_solicitado,
            "detalhamento": detalhamento,
            "apresentar_trabalho": apresentar_trabalho,
            "data_nascimento": data_nascimento,
            "logradouro": logradouro,
            "numero": numero,
            "bairro": bairro,
            "cep": cep,
            "cidade": cidade,
            "estado": estado,
            "cpf": cpf,
            "rg": rg,
            "nome_banco": nome_banco,
            "numero_agencia": numero_agencia,
            "numero_conta": numero_conta,
        }

    if any(_is_blank(v) for v in required.values()):
        errors.append("Preencha todos os campos")

    if not _is_blank(nusp) and not ONLY_DIGITS_RE.match(unicodedata.normalize("NFC", nusp).strip()):
        errors.append("N. USP deve conter apenas números")

    if not _is_blank(numero_agencia) and not ONLY_DIGITS_RE.match(unicodedata.normalize("NFC", numero_agencia).strip()):
        errors.append("Número da agência deve conter apenas números")

    if not _is_blank(valor_solicitado):
        v = unicodedata.normalize("NFC", valor_solicitado).strip()
        digits = _digits(v)
        if not (digits.isdigit() and int(digits) > 0):
            errors.append("Valor solicitado deve ser maior que 0")

    if not _is_blank(email):
        e = unicodedata.normalize("NFC", email).strip()
        if "@" not in e or "." not in e.split("@", 1)[1] if "@" in e else True:
            pass
        if not EMAIL_RE.match(e):
            errors.append("E-mail inválido")

    if not _is_blank(cpf):
        c = unicodedata.normalize("NFC", cpf).strip()
        if not CPF_RE.match(c):
            errors.append("CPF deve estar no formato 000.000.000-00")
        elif not _validate_cpf(c):
            errors.append("CPF inválido")

    if not _is_blank(cep):
        ce = unicodedata.normalize("NFC", cep).strip()
        if not CEP_RE.match(ce):
            errors.append("CEP deve estar no formato 00000-000")

    if not _is_blank(data_nascimento):
        d = unicodedata.normalize("NFC", data_nascimento).strip()
        if not DATE_RE.match(d):
            errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _valid_date(d):
            errors.append("Data de nascimento inválida")

    if errors:
        return HTMLResponse("\n".join(errors), status_code=400)

    n = _digits(unicodedata.normalize("NFC", valor_solicitado).strip())
    v = int(n) / 100
    valor_fmt = "R$ " + "{:,.2f}".format(v).replace(",", "@").replace(".", ",").replace("@", ".")

    if aba == "alunos":
        assunto = unicodedata.normalize("NFC", tipo_auxilio).strip()
        nivel_final = unicodedata.normalize("NFC", nivel).strip()
    else:
        assunto = "Verba do programa"
        nivel_final = ""

    oficio = _build_oficio(
        unicodedata.normalize("NFC", nome_completo).strip(),
        unicodedata.normalize("NFC", nusp).strip(),
        unicodedata.normalize("NFC", email).strip(),
        assunto,
        unicodedata.normalize("NFC", programa).strip(),
        nivel_final,
        unicodedata.normalize("NFC", nome_evento).strip(),
        unicodedata.normalize("NFC", periodo_evento).strip(),
        unicodedata.normalize("NFC", cidade_evento).strip(),
        unicodedata.normalize("NFC", estado_evento).strip(),
        unicodedata.normalize("NFC", pais_evento).strip(),
        (unicodedata.normalize("NFC", link_evento).strip() if link_evento else ""),
        unicodedata.normalize("NFC", apresentar_trabalho).strip(),
        valor_fmt,
        unicodedata.normalize("NFC", detalhamento).strip(),
        unicodedata.normalize("NFC", logradouro).strip(),
        unicodedata.normalize("NFC", numero).strip(),
        (unicodedata.normalize("NFC", complemento).strip() if complemento else ""),
        unicodedata.normalize("NFC", cep).strip(),
        unicodedata.normalize("NFC", bairro).strip(),
        unicodedata.normalize("NFC", cidade).strip(),
        unicodedata.normalize("NFC", estado).strip(),
        unicodedata.normalize("NFC", data_nascimento).strip(),
        unicodedata.normalize("NFC", cpf).strip(),
        unicodedata.normalize("NFC", rg).strip(),
        unicodedata.normalize("NFC", nome_banco).strip(),
        unicodedata.normalize("NFC", numero_agencia).strip(),
        unicodedata.normalize("NFC", numero_conta).strip(),
    )
    return HTMLResponse(oficio, status_code=200)
