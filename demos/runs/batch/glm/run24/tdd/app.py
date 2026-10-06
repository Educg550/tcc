import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
ASSETS_DIR = STATIC_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")


CAMPOS_OBRIGATORIOS_COMUNS = [
    "nome",
    "n_usp",
    "programa",
    "email",
    "evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
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

CAMPOS_ALUNOS = CAMPOS_OBRIGATORIOS_COMUNS + ["nivel", "tipo_auxilio"]


def _cpf_valido(cpf: str) -> bool:
    if not re.fullmatch(r"\d{11}", cpf):
        return False
    if cpf == cpf[0] * 11:
        return False
    digits = [int(c) for c in cpf]
    for i in range(9, 11):
        soma = sum(digits[j] * ((i + 1 - j) if j < i else 0) for j in range(i))
        resto = soma % 11
        if resto < 2:
            dv = 0
        else:
            dv = 11 - resto
        if dv != digits[i]:
            return False
    return True


def _data_valida(dia: int, mes: int, ano: int) -> bool:
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formatar_valor(valor: str) -> str:
    inteiro = int(valor)
    reais, centavos = divmod(inteiro, 100)
    texto = str(reais)
    grupos = []
    while len(texto) > 3:
        grupos.insert(0, texto[-3:])
        texto = texto[:-3]
    grupos.insert(0, texto)
    return f"R$ {'.'.join(grupos)},{centavos:02d}"


def gerar_oficio(d: dict) -> str:
    aba = d.get("aba", "ALUNOS")
    linhas = []
    linhas.append(f"Interessada(o): {d['nome']} - {d['n_usp']}")
    linhas.append(f"E-mail: {d['email']}")
    if aba == "DOCENTES":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d['programa']}")
    else:
        linhas.append(
            f"Assunto: Solicitação de Auxílio Financeiro - {d['tipo_auxilio']}"
        )
        linhas.append(f"Programa: {d['programa']} - {d['nivel']}")
    linhas.append("")
    linhas.append(
        "A CCP-" + d["programa"] + " aprovou na data de hoje, a solicitação de "
        "auxílio financeiro para a interessada(o) acima, conforme segue:"
    )
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {d['evento']}")
    linhas.append(f"Período: {d['periodo']}")
    linhas.append(
        f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}"
    )
    if d.get("link_evento"):
        linhas.append(f"Link do evento: {d['link_evento']}")
    linhas.append(f"Apresentação de trabalho: {d['apresentacao']}")
    linhas.append(f"Valor solicitado: {formatar_valor(d['valor_solicitado'])}")
    linhas.append(f"Detalhamento: {d['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['logradouro']}, {d['numero']}")
    if d.get("complemento"):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas.append(f"CEP: {d['cep'][:5]}-{d['cep'][5:]}")
    linhas.append(f"{d['bairro']}, {d['cidade']} - {d['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(
        f"Data de nascimento: {d['data_nascimento'][:2]}/{d['data_nascimento'][2:4]}"
        f"/{d['data_nascimento'][4:]}"
    )
    linhas.append(
        f"CPF: {d['cpf'][:3]}.{d['cpf'][3:6]}.{d['cpf'][6:9]}-{d['cpf'][9:]}"
    )
    linhas.append(f"RG / RNM: {d['rg']}")
    linhas.append(f"Banco: {d['banco']}")
    linhas.append(f"Agência: {d['agencia']}")
    linhas.append(f"Conta: {d['conta']}")
    linn = []
    linhas = linhas + linhas
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linn)


def validar(d: dict):
    erros = []
    aba = d.get("aba", "ALUNOS")
    obrigatorios = CAMPOS_OBRIGATORIOS_COMUNS + (
        ["nivel", "tipo_auxilio"] if aba != "DOCENTES" else []
    )
    if any(str(d.get(c, "")).strip() == "" for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if not re.fullmatch(r"\d+", str(d.get("n_usp", ""))):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"\d+", str(d.get("agencia", ""))):
        erros.append("Número da agência deve conter apenas números")
    valor = str(d.get("valor_solicitado", ""))
    if not valor.isdigit() or int(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    email = str(d.get("email", ""))
    if "@" not in email or not email.split("@", 1)[1].strip():
        erros.append("E-mail inválido")
    cpf = re.sub(r"\D", "", str(d.get("cpf", "")))
    if not re.fullmatch(r"\d{11}", cpf) or not _cpf_valido(cpf):
        if not re.fullmatch(r"\d{11}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        else:
            erros.append("CPF inválido")
    cep = re.sub(r"\D", "", str(d.get("cep", "")))
    if not re.fullmatch(r"\d{8}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    data = re.sub(r"\D", "", str(d.get("data_nascimento", "")))
    if not re.fullmatch(r"\d{8}", data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        dia, mes, ano = int(data[:2]), int(data[2:4]), int(data[4:])
        if not _data_valida(dia, mes, ano):
            erros.append("Data de nascimento inválida")
    return erros


@app.post("/solicitar")
def solicitar(payload: dict):
    erros = validar(payload)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": gerar_oficio(payload), "erros": []})
