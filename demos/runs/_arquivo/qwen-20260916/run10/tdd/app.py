import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


def _is_cpf_valido(cpf: str) -> bool:
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11:
        return False

    # 1st check digit
    s = sum(nums[i] * (10 - i) for i in range(9)) % 11
    d1 = 0 if s < 2 else 11 - s
    # 2nd check digit
    s = sum(nums[i] * (11 - i) for i in range(10)) % 11
    d2 = 0 if s < 2 else 11 - s

    return nums[9] == d1 and nums[10] == d2


CAMPOS_ALUNOS = [
    "nome", "nuspp", "programa", "nivel", "tipo_auxilio", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "link_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "complemento", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]

OBRIGATORIOS = set(CAMPOS_ALUNOS) - {"link_evento", "complemento"}


@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE / "index.html").read_text(encoding="utf-8")


@app.get("/style.css")
def style():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


@app.post("/solicitar")
async def solicitar(payload: dict):
    erros = []
    aba = payload.get("aba", "ALUNOS")
    campos = CAMPOS_ALUNOS if aba == "ALUNOS" else CAMPOS_DOCENTES

    # Check empty fields
    tem_vazio = False
    for c in campos:
        if c in OBRIGATORIOS:
            if not str(payload.get(c, "")).strip():
                tem_vazio = True
                break
    if tem_vazio:
        erros.append("Preencha todos os campos")

    # Format validations
    def _check(cond, msg):
        if not cond and msg not in erros:
            erros.append(msg)

    if payload.get("nuspp") and not str(payload["nuspp"]).isdigit():
        _check(True, "N. USP deve conter apenas números")

    if payload.get("agencia") and not str(payload["agencia"]).isdigit():
        _check(True, "Número da agência deve conter apenas números")

    valor_raw = payload.get("valor")
    try:
        valor_int = int(valor_raw)
        if valor_int <= 0:
            _check(True, "Valor solicitado deve ser maior que 0")
    except (ValueError, TypeError):
        _check(True, "Valor solicitado deve ser maior que 0")

    email = str(payload.get("email", ""))
    if email and ("@" not in email or len(email.split("@")[-1]) == 0):
        _check(True, "E-mail inválido")

    cpf = str(payload.get("cpf", ""))
    if cpf:
        import re
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            _check(True, "CPF deve estar no formato 000.000.000-00")
        elif not _is_cpf_valido(cpf):
            _check(True, "CPF inválido")

    cep = str(payload.get("cep", ""))
    if cep:
        import re
        if not re.match(r"^\d{5}-\d{3}$", cep):
            _check(True, "CEP deve estar no formato 00000-000")

    data = str(payload.get("data_nascimento", ""))
    if data:
        import re
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", data):
            _check(True, "Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                from datetime import datetime
                datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                _check(True, "Data de nascimento inválida")

    if erros:
        return {"erros": erros, "oficio": None}

    # Generate oficio
    valor_fmt = "R$ {:,.2f}".format(valor_int / 100.0)
    valor_fmt = valor_fmt.replace(",", ",").replace(".", ",").replace(",", ".", 1).replace(".", ",", 1)

    linhas = []
    linhas.append(f"Interessada(o): {payload['nome']} - {payload['nuspp']}")
    linhas.append(f"E-mail: {payload['email']}")
    if aba == "ALUNOS":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {payload['tipo_auxilio']}")
        linhas.append(f"Programa: {payload['programa']} - {payload['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {payload['programa']}")

    linhas.append("")
    linhas.append("A CCP-" + payload["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {payload['evento']}")
    linhas.append(f"Período: {payload['periodo']}")
    linhas.append(f"Local: {payload['cidade_evento']} - {payload['estado_evento']} - {payload['pais_evento']}")
    if payload.get("link_evento", "").strip():
        linhas.append(f"Link do evento: {payload['link_evento']}")
    linhas.append(f"Apresentação de trabalho: {payload['apresentacao']}")
    linhas.append(f"Valor solicitado: {valor_fmt}")
    linhas.append(f"Detalhamento: {payload['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{payload['logradouro']}, {payload['numero']}")
    if payload.get("complemento", "").strip():
        linhas.append(f"Complemento: {payload['complemento']}")
    linhas.append(f"CEP: {payload['cep']}")
    linhas.append(f"{payload['bairro']}, {payload['cidade']} - {payload['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {payload['data_nascimento']}")
    linhas.append(f"CPF: {payload['cpf']}")
    linhas.append(f"RG / RNM: {payload['rg']}")
    linhas.append(f"Banco: {payload['banco']}")
    linhas.append(f"Agência: {payload['agencia']}")
    linhas.append(f"Conta: {payload['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    oficio = "\n".join(linhas)
    return {"erros": [], "oficio": oficio}
