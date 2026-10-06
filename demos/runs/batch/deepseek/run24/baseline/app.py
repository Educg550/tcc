import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE = Path(__file__).resolve().parent

CAMPOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "evento_nome", "evento_periodo", "evento_cidade", "evento_estado",
    "evento_pais", "valor", "detalhamento", "apresentacao", "nascimento",
    "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]


def campos_obrigatorios(aba):
    if aba == "docentes":
        return [c for c in CAMPOS if c not in ("nivel", "tipo_auxilio")]
    return CAMPOS


def valor_em_centavos(v):
    m = re.fullmatch(r"R\$ (\d{1,3}(?:\.\d{3})*),(\d{2})", v)
    if not m:
        return None
    return int(m.group(1).replace(".", "")) * 100 + int(m.group(2))


def cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11 or len(set(nums)) == 1:
        return False
    for i in (9, 10):
        soma = sum(nums[j] * (i + 1 - j) for j in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != nums[i]:
            return False
    return True


def data_valida(s):
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validar(d):
    aba = d.get("aba", "alunos")
    erros = []

    if any(not str(d.get(c, "")).strip() for c in campos_obrigatorios(aba)):
        erros.append("Preencha todos os campos")

    n_usp = str(d.get("n_usp", "")).strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(d.get("agencia", "")).strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(d.get("valor", "")).strip()
    if valor:
        centavos = valor_em_centavos(valor)
        if centavos is None or centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = str(d.get("email", "")).strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = str(d.get("cpf", "")).strip()
    cpf_formato_ok = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = str(d.get("cep", "")).strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nasc = str(d.get("nascimento", "")).strip()
    nasc_formato_ok = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nasc))
    if nasc and not nasc_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato_ok and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if nasc_formato_ok and not data_valida(nasc):
        erros.append("Data de nascimento inválida")

    return erros


def g(d, k):
    return str(d.get(k, "")).strip()


def gerar_oficio(d):
    aba = d.get("aba", "alunos")
    linhas = []
    linhas.append(f"Interessada(o): {g(d, 'nome')} - {g(d, 'n_usp')}")
    linhas.append(f"E-mail: {g(d, 'email')}")
    if aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {g(d, 'programa')}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {g(d, 'tipo_auxilio')}")
        linhas.append(f"Programa: {g(d, 'programa')} - {g(d, 'nivel')}")
    linhas.append("")
    linhas.append(f"A CCP-{g(d, 'programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {g(d, 'evento_nome')}")
    linhas.append(f"Período: {g(d, 'evento_periodo')}")
    linhas.append(
        f"Local: {g(d, 'evento_cidade')} - {g(d, 'evento_estado')} - {g(d, 'evento_pais')}"
    )
    if g(d, "link_evento"):
        linhas.append(f"Link do evento: {g(d, 'link_evento')}")
    linhas.append(f"Apresentação de trabalho: {g(d, 'apresentacao')}")
    linhas.append(f"Valor solicitado: {g(d, 'valor')}")
    linhas.append(f"Detalhamento: {g(d, 'detalhamento')}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{g(d, 'logradouro')}, {g(d, 'numero')}")
    if g(d, "complemento"):
        linhas.append(f"Complemento: {g(d, 'complemento')}")
    linhas.append(f"CEP: {g(d, 'cep')}")
    linhas.append(f"{g(d, 'bairro')}, {g(d, 'cidade')} - {g(d, 'estado')}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {g(d, 'nascimento')}")
    linhas.append(f"CPF: {g(d, 'cpf')}")
    linhas.append(f"RG / RNM: {g(d, 'rg')}")
    linhas.append(f"Banco: {g(d, 'banco')}")
    linhas.append(f"Agência: {g(d, 'agencia')}")
    linhas.append(f"Conta: {g(d, 'conta')}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    erros = validar(dados)
    if erros:
        return JSONResponse({"erros": erros, "oficio": None})
    return JSONResponse({"erros": [], "oficio": gerar_oficio(dados)})


app.mount("/", StaticFiles(directory=BASE, html=True), name="static")
