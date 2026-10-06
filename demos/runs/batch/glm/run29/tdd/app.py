"""Backend do Requisito 01: valida a solicitação e devolve o ofício."""
import re
import calendar
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
ESTATICOS = BASE / "static"

app = FastAPI(title="Auxílio Financeiro Pós-Graduação IME-USP")

CAMPOS_OBRIGATORIOS_COMUNS = [
    "nome", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao",
    "nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end",
    "estado_end", "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_ALUNOS = CAMPOS_OBRIGATORIOS_COMUNS + ["nivel", "tipo_auxilio"]

ERRO_CAMPOS_VAZIOS = "Preencha todos os campos"


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((ESTATICOS / "index.html").read_text(encoding="utf-8"))


@app.get("/style.css")
def style() -> FileResponse:
    return FileResponse(ESTATICOS / "style.css", media_type="text/css")


@app.get("/app.js")
def script() -> FileResponse:
    return FileResponse(ESTATICOS / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


def formatar_valor(valor: str) -> str:
    """'150000' -> 'R$ 1.500,00'; aceita já formatado ou só dígitos."""
    digitos = re.sub(r"[^0-9]", "", valor)
    centavos = int(digitos)
    texto = f"{centavos:03d}"  # garante pelo menos uma unidade
    inteiro, dec = texto[:-2], texto[-2:]
    partes = []
    while len(inteiro) > 3:
        partes.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    partes.insert(0, inteiro)
    return "R$ " + ".".join(partes) + "," + dec


def valor_centavos(valor: str) -> int:
    """Converte a entrada em centavos; lança ValueError se inválida."""
    limpo = valor.strip().replace("R$", "").strip()
    if not re.fullmatch(r"[0-9][0-9.,]*", limpo):
        raise ValueError("valor")
    digitos = re.sub(r"[^0-9]", "", limpo)
    if not digitos:
        raise ValueError("valor")
    if digitos == "0" * len(digitos):
        return 0
    return int(digitos)


def cpf_valido(cpf: str) -> bool:
    if not re.fullmatch(r"[0-9]{3}.[0-9]{3}.[0-9]{3}-[0-9]{2}", cpf):
        return False
    digitos = [int(d) for d in re.sub(r"[^0-9]", "", cpf)]
    if digitos == digitos[::-1]:
        return False
    soma = sum(digitos[i] * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if d1 != digitos[9]:
        return False
    soma = sum(digitos[i] * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return d2 == digitos[10]


def data_valida(data: str) -> bool:
    if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", data):
        return False
    dia, mes, ano = (int(p) for p in data.split("/"))
    if not 1 <= mes <= 12:
        return False
    if not 1 <= dia <= calendar.monthrange(ano, mes)[1]:
        return False
    return True


def gerar_oficio(f: dict) -> str:
    tipo = f["tipo"]
    nome = f["nome"]
    n_usp = f["n_usp"]
    email = f["email"]
    programa = f["programa"]
    nivel = f.get("nivel", "")
    tipo_auxilio = f.get("tipo_auxilio", "")
    linhas = []
    linhas.append(f"Interessada(o): {nome} - {n_usp}")
    linhas.append(f"E-mail: {email}")
    if tipo == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}")
        linhas.append(f"Programa: {programa} - {nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    linhas.append("")
    linhas.append(
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {f['nome_evento']}")
    linhas.append(f"Período: {f['periodo']}")
    linhas.append(f"Local: {f['cidade']} - {f['estado']} - {f['pais']}")
    link = f["link_evento"].strip()
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas.append(f"Apresentação de trabalho: {f['apresentacao']}")
    linhas.append(f"Valor solicitado: {formatar_valor(f['valor'])}")
    linhas.append(f"Detalhamento: {f['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{f['logradouro']}, {f['numero']}")
    complemento = f["complemento"].strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.append(f"CEP: {f['cep']}")
    linhas.append(f"{f['bairro']}, {f['cidade_end']} - {f['estado_end']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {f['nascimento']}")
    linhas.append(f"CPF: {f['cpf']}")
    linhas.append(f"RG / RNM: {f['rg']}")
    linhas.append(f"Banco: {f['banco']}")
    linhas.append(f"Agência: {f['agencia']}")
    linhas.append(f"Conta: {f['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


async def _processar(request: Request, tipo: str):
    f = {k: v.strip() for k, v in (await request.form()).items()}
    f["tipo"] = tipo

    obrig = CAMPOS_ALUNOS if tipo == "alunos" else CAMPOS_OBRIGATORIOS_COMUNS
    erros = []
    if any(not f.get(c) for c in obrig):
        erros.append(ERRO_CAMPOS_VAZIOS)
    if not re.fullmatch(r"[0-9]+", f["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if not re.fullmatch(r"[0-9]+", f["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    try:
        centavos = valor_centavos(f["valor"])
    except ValueError:
        centavos = 0
    if centavos <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if "@" not in f["email"] or "@" not in f["email"][1:] or "." not in f["email"].rsplit("@", 1)[1]:
        erros.append("E-mail inválido")
    if re.fullmatch(r"[0-9]{3}.[0-9]{3}.[0-9]{3}-[0-9]{2}", f["cpf"]):
        if not cpf_valido(f["cpf"]):
            erros.append("CPF inválido")
    else:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if not re.fullmatch(r"[0-9]{5}-[0-9]{3}", f["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", f["nascimento"]):
        if not data_valida(f["nascimento"]):
            erros.append("Data de nascimento inválida")
    else:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if erros:
        return {"ok": False, "erros": erros, "oficio": ""}
    return {"ok": True, "erros": [], "oficio": gerar_oficio(f)}


@app.post("/solicitar/alunos")
async def solicitar_alunos(request: Request):
    return await _processar(request, "alunos")


@app.post("/solicitar/docentes")
async def solicitar_docentes(request: Request):
    return await _processar(request, "docentes")
