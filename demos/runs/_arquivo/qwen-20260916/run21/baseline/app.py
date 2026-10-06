from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import re

app = FastAPI()
app.mount("/", StaticFiles(directory=".", html=True), name="statics")


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_RE = re.compile(r"^\d{5}-\d{3}$")
DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _cpf_ok(cpf: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", cpf)]
    base = digits[:9]
    if len(base) == 9 and all(d == base[0] for d in base):
        return False

    s = sum((10 - i) * base[i] for i in range(9)) % 11
    d1 = 0 if s < 2 else 11 - s
    s2 = d1 * 2
    for i in range(9):
        s2 += (11 - i) * base[i]
    s2 %= 11
    d2 = 0 if s2 < 2 else 11 - s2

    return digits[9] == d1 and digits[10] == d2


def _date_ok(value: str) -> bool:
    m = DATE_RE.match(value)
    if not m:
        return False
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if year < 1 or month < 1 or month > 12:
        return False
    days_in_month = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= day <= days_in_month[month - 1]


@app.post("/api/solicitacao")
async def solicitacao(request: Request) -> HTMLResponse:
    data = await request.json()

    aba = data.get("aba", "")

    def get(key):
        v = data.get(key)
        if isinstance(v, str):
            v = v.strip()
        return v or ""

    errors = []

    required_keys = [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERIODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAIS DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IRAPRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
        "DATA DE NASCIMENTO",
        "LOGRADOURO",
        "NUMERO",
        "BAIRRO",
        "CEP",
        "CIDADE",
        "ESTADO",
        "CPF (SEPARADOS POR PONTOS E TRACO)",
        "RG / RNM (SEPARADOS POR PONTOS E TRACO)",
        "NOME DO BANCO",
        "NUMERO DA AGENCIA",
        "NUMERO DA CONTA",
    ]
    if aba == "ALUNOS":
        required_keys = [
            "NOME COMPLETO - SEM ABREVIAR",
            "N. USP",
            "PROGRAMA",
            "NIVEL",
            "TIPO DE AUXILIO",
            "E-MAIL",
            "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
            "PERIODO DO EVENTO, EXAME OU DEFESA",
            "CIDADE DO EVENTO, EXAME OU DEFESA",
            "ESTADO DO EVENTO, EXAME OU DEFESA",
            "PAIS DO EVENTO, EXAME OU DEFESA",
            "VALOR SOLICITADO (R$)",
            "DETALHAMENTO DO PEDIDO",
            "IRAPRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
            "DATA DE NASCIMENTO",
            "LOGRADOURO",
            "NUMERO",
            "BAIRRO",
            "CEP",
            "CIDADE",
            "ESTADO",
            "CPF (SEPARADOS POR PONTOS E TRACO)",
            "RG / RNM (SEPARADOS POR PONTOS E TRACO)",
            "NOME DO BANCO",
            "NUMERO DA AGENCIA",
            "NUMERO DA CONTA",
        ]

    for k in required_keys:
        if not get(k):
            errors.append("Preencha todos os campos")
            break

    nusp = get("N. USP")
    if nusp and not re.fullmatch(r"\d+", nusp):
        errors.append("N. USP deve conter apenas números")

    agencia = get("NUMERO DA AGENCIA")
    if agencia and not re.fullmatch(r"\d+", agencia):
        errors.append("Número da agência deve conter apenas números")

    valor = get("VALOR SOLICITADO (R$)")
    if valor:
        if not valor.isdigit() or int(valor) <= 0:
            errors.append("Valor solicitado deve ser maior que 0")

    email = get("E-MAIL")
    if email and not EMAIL_RE.fullmatch(email):
        errors.append("E-mail inválido")

    cpf = get("CPF (SEPARADOS POR PONTOS E TRACO)")
    if cpf and not CPF_RE.fullmatch(cpf):
        errors.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_ok(cpf):
        errors.append("CPF inválido")

    cep = get("CEP")
    if cep and not CEP_RE.fullmatch(cep):
        errors.append("CEP deve estar no formato 00000-000")

    data_nasc = get("DATA DE NASCIMENTO")
    if data_nasc and not DATE_RE.match(data_nasc):
        errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data_nasc and not _date_ok(data_nasc):
        errors.append("Data de nascimento inválida")

    if errors:
        items = "".join(f"<li>{e}</li>" for e in errors)
        body = f'<div class="errors"><ul>{items}</ul></div>'
        return HTMLResponse(content=body, status_code=422)

    if valor:
        cents = int(valor)
        reais = cents // 100
        centavos = cents % 100
        s = f"{reais:,}".replace(",", ".")
        valor_fmt = f"R$ {s},{centavos:02d}"
    else:
        valor_fmt = ""

    if aba == "ALUNOS":
        tipo_aux = get("TIPO DE AUXILIO")
        nivel = get("NIVEL")
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {tipo_aux}"
        programa_line = f"Programa: {get('PROGRAMA')} - {nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa_line = f"Programa: {get('PROGRAMA')}"

    link = get("LINK DO EVENTO, EXAME OU DEFESA")
    complemento = get("COMPLEMENTO")

    event_lines = [
        f"Evento: {get('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {get('PERIODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {get('CIDADE DO EVENTO, EXAME OU DEFESA')} - {get('ESTADO DO EVENTO, EXAME OU DEFESA')} - {get('PAIS DO EVENTO, EXAME OU DEFESA')}",
    ]
    if link:
        event_lines.append(f"Link do evento: {link}")
    event_lines += [
        f"Apresentação de trabalho: {get('IRAPRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {get('DETALHAMENTO DO PEDIDO')}",
    ]

    addr_lines = [
        f"{get('LOGRADOURO')}, {get('NUMERO')}",
    ]
    if complemento:
        addr_lines.append(f"Complemento: {complemento}")
    addr_lines += [
        f"CEP: {get('CEP')}",
        f"{get('BAIRRO')}, {get('CIDADE')} - {get('ESTADO')}",
    ]

    pay_lines = [
        f"Data de nascimento: {get('DATA DE NASCIMENTO')}",
        f"CPF: {get('CPF (SEPARADOS POR PONTOS E TRACO)')}",
        f"RG / RNM: {get('RG / RNM (SEPARADOS POR PONTOS E TRACO)')}",
        f"Banco: {get('NOME DO BANCO')}",
        f"Agência: {get('NUMERO DA AGENCIA')}",
        f"Conta: {get('NUMERO DA CONTA')}",
    ]

    oficio = f"""Interessada(o): {get('NOME COMPLETO - SEM ABREVIAR')} - {nusp}
E-mail: {email}
{assunto}
{programa_line}

A CCP-{get('PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a
interessada(o) acima, conforme segue:

Dados do evento
{"\n".join(event_lines)}

Endereço da(o) interessada(o)
{"\n".join(addr_lines)}

Dados para pagamento
{"\n".join(pay_lines)}

Encaminhe-se ao Serviço Financeiro para providências."""

    body = f'<div class="success"><h2 class="confirm-title">Solicitação registrada</h2><pre class="oficio">{oficio}</pre></div>'
    return HTMLResponse(content=body, status_code=200)


@app.get("/api/ping")
async def ping():
    return {"ok": True}
