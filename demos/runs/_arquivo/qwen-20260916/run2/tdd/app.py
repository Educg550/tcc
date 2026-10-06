import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

templates = Jinja2Templates(directory=BASE_DIR)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def is_cpf_valid(cpf: str) -> bool:
    digits = re.sub(r"\D", "", cpf)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False
    s = 0
    for i in range(9):
        s += int(digits[i]) * (10 - i)
    d1 = (s * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != int(digits[9]):
        return False
    s = 0
    for i in range(10):
        s += int(digits[i]) * (11 - i)
    d2 = (s * 10) % 11
    if d2 == 10:
        d2 = 0
    return d2 == int(digits[10])


@app.post("/solicitacao")
async def solicitacao(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Malformed body"})

    aba = data.get("aba", "")
    nome_completo = data.get("nome_completo", "")
    nusp = data.get("nusp", "")
    programa = data.get("programa", "")
    nivel = data.get("nivel", "")
    tipo_auxilio = data.get("tipo_auxilio", "")
    email = data.get("email", "")
    nome_evento = data.get("nome_evento", "")
    periodo_evento = data.get("periodo_evento", "")
    cidade_evento = data.get("cidade_evento", "")
    estado_evento = data.get("estado_evento", "")
    pais_evento = data.get("pais_evento", "")
    link_evento = data.get("link_evento", "")
    valor_solicitado = data.get("valor_solicitado", "")
    detalhamento = data.get("detalhamento", "")
    apresenta_trabalho = data.get("apresenta_trabalho", "")
    data_nascimento = data.get("data_nascimento", "")
    logradouro = data.get("logradouro", "")
    numero = data.get("numero", "")
    complemento = data.get("complemento", "")
    bairro = data.get("bairro", "")
    cep = data.get("cep", "")
    cidade = data.get("cidade", "")
    estado = data.get("estado", "")
    cpf = data.get("cpf", "")
    rg = data.get("rg", "")
    banco = data.get("banco", "")
    agencia = data.get("agencia", "")
    conta = data.get("conta", "")

    errors = []

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
        "apresenta_trabalho": apresenta_trabalho,
        "data_nascimento": data_nascimento,
        "logradouro": logradouro,
        "numero": numero,
        "bairro": bairro,
        "cep": cep,
        "cidade": cidade,
        "estado": estado,
        "cpf": cpf,
        "rg": rg,
        "banco": banco,
        "agencia": agencia,
        "conta": conta,
    }

    if aba == "alunos":
        required["nivel"] = nivel
        required["tipo_auxilio"] = tipo_auxilio

    if any(str(v).strip() == "" for v in required.values()):
        errors.append("Preencha todos os campos")

    if nusp and not re.fullmatch(r"\d+", str(nusp)):
        errors.append("N. USP deve conter apenas números")

    if agencia and not re.fullmatch(r"\d+", str(agencia)):
        errors.append("Número da agência deve conter apenas números")

    try:
        v = int(valor_solicitado)
        if v <= 0 or v > 999999999:
            errors.append("Valor solicitado deve ser maior que 0")
    except (ValueError, TypeError):
        if errors or "Preencha todos os campos" not in errors:
            errors.append("Valor solicitado deve ser maior que 0")

    if email:
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append("E-mail inválido")

    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", str(cpf)):
            errors.append("CPF deve estar no formato 000.000.000-00")
        elif not is_cpf_valid(str(cpf)):
            errors.append("CPF inválido")

    if cep:
        if not re.fullmatch(r"\d{5}-\d{3}", str(cep)):
            errors.append("CEP deve estar no formato 00000-000")

    if data_nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", str(data_nascimento)):
            errors.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            d, m, y = [int(x) for x in str(data_nascimento).split("/")]
            try:
                import datetime
                datetime.date(y, m, d)
            except ValueError:
                errors.append("Data de nascimento inválida")

    if errors:
        return JSONResponse(status_code=422, content={"detail": errors})

    try:
        cents = int(valor_solicitado)
    except (ValueError, TypeError):
        cents = 0

    valor_str = "R$ {:,}.2f".format(cents // 100, cents % 100).replace(",", "X").replace(".", ",").replace("X", ".")

    if aba == "alunos":
        lines = [
            f"Interessada(o): {nome_completo} - {nusp}",
            f"E-mail: {email}",
            f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}",
            f"Programa: {programa} - {nivel}",
            "",
            "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
            "interessada(o) acima, conforme segue:",
            "",
            "Dados do evento",
            f"Evento: {nome_evento}",
            f"Período: {periodo_evento}",
            f"Local: {cidade_evento} - {estado_evento} - {pais_evento}",
        ]
    else:
        lines = [
            f"Interessada(o): {nome_completo} - {nusp}",
            f"E-mail: {email}",
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f"Programa: {programa}",
            "",
            "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
            "interessada(o) acima, conforme segue:",
            "",
            "Dados do evento",
            f"Evento: {nome_evento}",
            f"Período: {periodo_evento}",
            f"Local: {cidade_evento} - {estado_evento} - {pais_evento}",
        ]

    if link_evento:
        lines.append(f"Link do evento: {link_evento}")

    lines += [
        f"Apresentação de trabalho: {apresenta_trabalho}",
        f"Valor solicitado: {valor_str}",
        f"Detalhamento: {detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{logradouro}, {numero}",
    ]

    if complemento:
        lines.append(f"Complemento: {complemento}")

    lines += [
        f"CEP: {cep}",
        f"{bairro}, {cidade} - {estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data_nascimento}",
        f"CPF: {cpf}",
        f"RG / RNM: {rg}",
        f"Banco: {banco}",
        f"Agência: {agencia}",
        f"Conta: {conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return JSONResponse(content={"oficio": "\n".join(lines)})
