import re
from datetime import date

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = __file__.rsplit("/", 1)[0]

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "nome",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
]


def cpf_valido(cpf: str) -> bool:
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False
    digitos = [int(d) for d in cpf if d.isdigit()]
    for i in range(9, 11):
        resto = sum(d * peso for d, peso in zip(digitos[:i], range(i + 1, 1, -1))) % 11
        if (resto < 2 and digitos[i] != 0) or (resto >= 2 and digitos[i] != 11 - resto):
            return False
    return True


def formatar_valor(valor: str) -> str | None:
    m = re.fullmatch(r"R\$\s*([\d.]*),(\d{2})", valor)
    if not m:
        return None
    centavos = m.group(1).replace(".", "") + m.group(2)
    return centavos if centavos.isdigit() else None


def formatar_data(data: str) -> str | None:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return None
    dia, mes, ano = (int(g) for g in m.groups())
    try:
        date(ano, mes, dia)
    except ValueError:
        return None
    return f"{dia:02d}/{mes:02d}/{ano:04d}"


def validar(dados: dict, aba: str) -> list[str]:
    erros = []
    if any(not str(dados.get(campo, "")).strip() for campo in CAMPOS_OBRIGATORIOS):
        erros.append("Preencha todos os campos")
    if "n_usp" in dados and not str(dados["n_usp"]).isdigit():
        erros.append("N. USP deve conter apenas números")
    if "agencia" in dados and not str(dados["agencia"]).isdigit():
        erros.append("Número da agência deve conter apenas números")
    valor = formatar_valor(str(dados.get("valor", "")))
    if valor is None or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = str(dados.get("email", ""))
    if email.count("@") != 1 or not email.rsplit("@", 1)[1]:
        erros.append("E-mail inválido")
    cpf = str(dados.get("cpf", ""))
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not cpf_valido(cpf):
        erros.append("CPF inválido")
    cep = str(dados.get("cep", ""))
    if not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    data = str(dados.get("data_nascimento", ""))
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif formatar_data(data) is None:
        erros.append("Data de nascimento inválida")
    return erros


def montar_oficio(dados: dict, aba: str) -> str:
    valor = formatar_valor(str(dados["valor"]))
    reais, centavos = valor[:-2], valor[-2:]
    partes = []
    while len(reais) > 3:
        partes.insert(0, reais[-3:])
        reais = reais[:-3]
    partes.insert(0, reais)
    valor_fmt = f"R$ {'.'.join(partes)},{centavos}"
    if aba == "ALUNOS":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados.get("link_evento"):
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas.extend([
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ])
    if dados.get("complemento"):
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.extend([
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/enviar")
async def enviar(request: Request, aba: str = Form(...)):
    dados = {k: v for k, v in (await request.form()).items() if k != "aba"}
    if aba not in ("ALUNOS", "DOCENTES"):
        return JSONResponse(status_code=422, content={"ok": False, "erros": ["Aba inválida"]})
    erros = validar(dados, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": montar_oficio(dados, aba)}


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")
