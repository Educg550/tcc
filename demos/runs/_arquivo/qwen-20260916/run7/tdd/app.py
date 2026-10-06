import re
import calendar

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def digits(s):
    return re.sub(r"\D", "", s or "")


def validate(data, is_student):
    erros = []

    # Campos obrigatórios
    required = [
        "nome", "nusp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta"
    ]
    if is_student:
        required.extend(["nivel", "tipo_auxilio"])

    for campo in required:
        if not str(data.get(campo, "")).strip():
            erros.append("Preencha todos os campos")
            break

    # N. USP
    nusp = str(data.get("nusp", ""))
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    # Agência
    agencia = str(data.get("agencia", ""))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    # Valor
    try:
        valor = int(data.get("valor", 0))
        if valor <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    except (ValueError, TypeError):
        erros.append("Valor solicitado deve ser maior que 0")

    # E-mail
    email = str(data.get("email", ""))
    if email:
        if "@" not in email or email.endswith("@"):
            erros.append("E-mail inválido")
        else:
            local, _, dominio = email.partition("@")
            if not local or not dominio or "." not in dominio:
                erros.append("E-mail inválido")

    # CPF formato
    cpf = str(data.get("cpf", ""))
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        else:
            dcpf = digits(cpf)
            if len(dcpf) == 11:
                # Validação dos dígitos verificadores
                nums = [int(c) for c in dcpf]
                # Primeiro dígito
                soma = sum(nums[i] * (10 - i) for i in range(9))
                resto = soma % 11
                dv1 = 0 if resto < 2 else 11 - resto
                if dv1 != nums[9]:
                    erros.append("CPF inválido")
                else:
                    # Segundo dígito
                    soma2 = sum(nums[i] * (11 - i) for i in range(10))
                    resto2 = soma2 % 11
                    dv2 = 0 if resto2 < 2 else 11 - resto2
                    if dv2 != nums[10]:
                        erros.append("CPF inválido")

    # CEP
    cep = str(data.get("cep", ""))
    if cep:
        if not re.match(r"^\d{5}-\d{3}$", cep):
            erros.append("CEP deve estar no formato 00000-000")

    # Data de nascimento formato
    data_nasc = str(data.get("data_nascimento", ""))
    if data_nasc:
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", data_nasc)
        if not m:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if mes < 1 or mes > 12 or dia < 1 or dia > calendar.monthrange(ano, mes)[1]:
                erros.append("Data de nascimento inválida")

    return erros


def format_valor_centavos(centavos):
    reais = centavos // 100
    c = centavos % 100
    s = f"{reais}"
    # Adicionar pontos de milhar
    if len(s) > 3:
        parts = []
        while len(s) > 3:
            parts.append(s[-3:])
            s = s[:-3]
        parts.append(s)
        s = ".".join(reversed(parts))
    return f"R$ {s},{c:02d}"


def build_oficio(data, is_student):
    valor_formatado = format_valor_centavos(int(data["valor"]))

    linhas = []
    linhas.append(f"Interessada(o): {data['nome']} - {data['nusp']}")
    linhas.append(f"E-mail: {data['email']}")

    if is_student:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {data['tipo_auxilio']}")
        linhas.append(f"Programa: {data['programa']} - {data['nivel']}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {data['programa']}")

    linhas.append("")
    linhas.append(f"A CCP-{data['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {data['evento']}")
    linhas.append(f"Período: {data['periodo']}")
    linhas.append(f"Local: {data['cidade_evento']} - {data['estado_evento']} - {data['pais_evento']}")

    if data.get("link", "").strip():
        linhas.append(f"Link do evento: {data['link']}")

    linhas.append(f"Apresentação de trabalho: {data['apresentacao']}")
    linhas.append(f"Valor solicitado: {valor_formatado}")
    linhas.append(f"Detalhamento: {data['detalhamento']}")

    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{data['logradouro']}, {data['numero']}")

    if data.get("complemento", "").strip():
        linhas.append(f"Complemento: {data['complemento']}")

    linhas.append(f"CEP: {data['cep']}")
    linhas.append(f"{data['bairro']}, {data['cidade']} - {data['estado']}")

    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {data['data_nascimento']}")
    linhas.append(f"CPF: {data['cpf']}")
    linhas.append(f"RG / RNM: {data['rg']}")
    linhas.append(f"Banco: {data['banco']}")
    linhas.append(f"Agência: {data['agencia']}")
    linhas.append(f"Conta: {data['conta']}")

    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    return "\n".join(linhas)


@app.get("/")
async def index():
    return FileResponse("index.html")


@app.get("/index.html")
async def index2():
    return FileResponse("index.html")


@app.get("/app.js")
async def app_js():
    return FileResponse("app.js", media_type="application/javascript")


@app.get("/style.css")
async def style_css():
    return FileResponse("style.css", media_type="text/css")


@app.post("/api/solicitacoes/{tipo}")
async def solicitacao(tipo: str, request: Request):
    data = await request.json()
    is_student = tipo == "aluno"
    erros = validate(data, is_student)

    if erros:
        return JSONResponse({"ok": False, "erros": erros})

    oficio = build_oficio(data, is_student)
    return JSONResponse({"ok": True, "oficio": oficio})
