import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

@app.post("/api/solicitar")
async def solicitar(payload: dict):
    dados = payload.get("dados", {})
    aba = payload.get("aba", "alunos")
    erros = []

    def eh_digitos(v):
        return bool(re.fullmatch(r"\d+", v))

    campos_obrigatorios = [
        "nome", "nusp", "programa", "nivel" if aba == "alunos" else "tipo", "email",
        "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
        "valor", "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"
    ]
    if aba == "alunos":
        campos_obrigatorios.append("tipo")

    for c in campos_obrigatorios:
        if not str(dados.get(c, "")).strip():
            erros.append("Preencha todos os campos")
            break

    nusp = str(dados.get("nusp", "")).strip()
    if nusp and not eh_digitos(nusp):
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", "")).strip()
    if agencia and not eh_digitos(agencia):
        erros.append("Número da agência deve conter apenas números")

    email = str(dados.get("email", "")).strip()
    if email and ("@" not in email or not re.search(r"@.+\..+", email)):
        erros.append("E-mail inválido")

    valor_str = str(dados.get("valor", "")).strip()
    valor_num = 0
    if valor_str:
        clean = re.sub(r"[^\d]", "", valor_str)
        valor_num = int(clean) if clean else 0
        if valor_num <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    cpf = str(dados.get("cpf", "")).strip()
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf:
        num = re.sub(r"[^\d]", "", cpf)
        if not validar_cpf(num):
            erros.append("CPF inválido")

    cep = str(dados.get("cep", "")).strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = str(dados.get("data_nascimento", "")).strip()
    if data and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data:
        try:
            d, m, y = map(int, data.split("/"))
            if not eh_data_valida(d, m, y):
                erros.append("Data de nascimento inválida")
        except ValueError:
            erros.append("Data de nascimento inválida")

    if erros:
        return JSONResponse({"status": "erro", "erros": list(dict.fromkeys(erros))})

    valor_fmt = format_brl(valor_num)
    tipo = dados.get("tipo", "Verba do programa")
    nivel = dados.get("nivel", "")

    lin_1 = f"Interessada(o): {dados.get('nome')} - {dados.get('nusp')}"
    lin_2 = f"E-mail: {dados.get('email')}"
    lin_3 = f"Assunto: Solicitação de Auxílio Financeiro - {tipo}"
    if aba == "alunos" and nivel:
        lin_4 = f"Programa: {dados.get('programa')} - {nivel}"
    else:
        lin_4 = f"Programa: {dados.get('programa')}"

    p1 = "A CCP-" + dados.get("programa", "") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    p2 = "interessada(o) acima, conforme segue:"

    evento = "Dados do evento\n"
    evento += f"Evento: {dados.get('evento')}\n"
    evento += f"Período: {dados.get('periodo')}\n"
    evento += f"Local: {dados.get('cidade_evento')} - {dados.get('estado_evento')} - {dados.get('pais_evento')}\n"
    if dados.get("link"):
        evento += f"Link do evento: {dados.get('link')}\n"
    evento += f"Apresentação de trabalho: {dados.get('apresentacao')}\n"
    evento += f"Valor solicitado: {valor_fmt}\n"
    evento += f"Detalhamento: {dados.get('detalhamento')}"

    end = "Endereço da(o) interessada(o)\n"
    end += f"{dados.get('logradouro')}, {dados.get('numero')}\n"
    if dados.get("complemento"):
        end += f"Complemento: {dados.get('complemento')}\n"
    end += f"CEP: {dados.get('cep')}\n"
    end += f"{dados.get('bairro')}, {dados.get('cidade')} - {dados.get('estado')}"

    pag = "Dados para pagamento\n"
    pag += f"Data de nascimento: {dados.get('data_nascimento')}\n"
    pag += f"CPF: {dados.get('cpf')}\n"
    pag += f"RG / RNM: {dados.get('rg')}\n"
    pag += f"Banco: {dados.get('banco')}\n"
    pag += f"Agência: {dados.get('agencia')}\n"
    pag += f"Conta: {dados.get('conta')}\n"

    off = "\n".join([lin_1, lin_2, lin_3, lin_4, "", p1, p2, "", evento, "", end, "", pag, "Encaminhe-se ao Serviço Financeiro para providências."])

    return JSONResponse({"status": "sucesso", "oficio": off})


def validar_cpf(cpf):
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    if d2 == 10:
        d2 = 0
    if d2 != int(cpf[10]):
        return False
    return True


def eh_data_valida(d, m, y):
    if not (1 <= m <= 12):
        return False
    dias_mes = [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= d <= dias_mes[m - 1]


def format_brl(v):
    s = str(v).zfill(3)
    cents = s[-2:]
    reais = int(s[:-2])
    r_str = f"{reais:,}"
    return f"R$ {r_str.replace(',', '.')} ,{cents}".replace(" ", "")

app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")
