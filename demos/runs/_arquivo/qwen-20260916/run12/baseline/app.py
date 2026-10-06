import os
import re

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

RE_NUM = re.compile(r"^\\d+$")
RE_EMAIL = re.compile(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
RE_CPF = re.compile(r"^\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}$")
RE_CEP = re.compile(r"^\\d{5}-\\d{3}$")
RE_DATA = re.compile(r"^(\\d{2})/(\\d{2})/(\\d{4})$")


def cpf_valido(cpf: str) -> bool:
    nums = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(n * (i + 1 - j) for j, n in enumerate(nums[:i - 1]))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != nums[i]:
            return False
    return True


def data_valida(data: str) -> bool:
    dia, mes, ano = (int(x) for x in RE_DATA.match(data).groups())
    ultimo = [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28,
              31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
    return 1 <= dia <= ultimo


def valor_para_moeda(bruto: str) -> str:
    centavos = int(bruto)
    inteiro, frac = divmod(centavos, 100)
    inteiro_str = f"{inteiro:,}".replace(",", ".")
    return f"R$ {inteiro_str},{frac:02d}"


CAMPOS_ALUNOS = [
    "nome_completo", "num_usp", "programa", "nivel", "tipo_auxilio",
    "email", "nome_evento", "periodo_evento", "cidade_evento",
    "estado_evento", "pais_evento", "link_evento", "valor_solicitado",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "complemento", "bairro", "cep", "cidade", "estado",
    "cpf", "rg_rnm", "nome_banco", "num_agencia", "num_conta",
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]
OBRIGATORIOS = CAMPOS_ALUNOS - {"link_evento", "complemento"}


def validar(p: dict, aba: str) -> list:
    erros = []
    obrigatorios = OBRIGATORIOS if aba == "alunos" else OBRIGATORIOS - {"nivel", "tipo_auxilio"}
    if any(not p.get(c, "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if p.get("num_usp", "").strip() and not RE_NUM.fullmatch(p["num_usp"].strip()):
        erros.append("N. USP deve conter apenas números")
    if p.get("num_agencia", "").strip() and not RE_NUM.fullmatch(p["num_agencia"].strip()):
        erros.append("Número da agência deve conter apenas números")
    v = p.get("valor_solicitado", "").strip()
    if v and (not RE_NUM.fullmatch(v) or int(v) == 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if p.get("email", "").strip() and not RE_EMAIL.fullmatch(p["email"].strip()):
        erros.append("E-mail inválido")
    if p.get("cpf", "").strip() and not RE_CPF.fullmatch(p["cpf"].strip()):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif p.get("cpf", "").strip() and not cpf_valido(p["cpf"].strip()):
        erros.append("CPF inválido")
    if p.get("cep", "").strip() and not RE_CEP.fullmatch(p["cep"].strip()):
        erros.append("CEP deve estar no formato 00000-000")
    if p.get("data_nascimento", "").strip() and not RE_DATA.fullmatch(p["data_nascimento"].strip()):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif p.get("data_nascimento", "").strip() and not data_valida(p["data_nascimento"].strip()):
        erros.append("Data de nascimento inválida")
    return erros


def gera_oficio(p: dict, aba: str) -> str:
    g = lambda k: p.get(k, "").strip()
    linhas = []
    linhas.append(f"Interessada(o): {g('nome_completo')} - {g('num_usp')}")
    linhas.append(f"E-mail: {g('email')}")
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {g('tipo_auxilio')}")
        linhas.append(f"Programa: {g('programa')} - {g('nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {g('programa')}")
    linhas.append("")
    linhas.append("A CCP-" + g("programa") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {g('nome_evento')}")
    linhas.append(f"Período: {g('periodo_evento')}")
    linhas.append(f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}")
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas.append(f"Apresentação de trabalho: {g('apresentacao')}")
    linhas.append(f"Valor solicitado: {valor_para_moeda(g('valor_solicitado'))}")
    linhas.append(f"Detalhamento: {g('detalhamento')}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{g('logradouro')}, {g('numero')}")
    if g("complemento"):
        linhas.append(f"Complemento: {g('complemento')}")
    linhas.append(f"CEP: {g('cep')}")
    linhas.append(f"{g('bairro')}, {g('cidade')} - {g('estado')}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {g('data_nascimento')}")
    linhas.append(f"CPF: {g('cpf')}")
    linhas.append(f"RG / RNM: {g('rg_rnm')}")
    linhas.append(f"Banco: {g('nome_banco')}")
    linhas.append(f"Agência: {g('num_agencia')}")
    linhas.append(f"Conta: {g('num_conta')}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitacao(request: Request):
    dados = await request.json()
    aba = dados.pop("_aba", "alunos")
    p = {k: v or "" for k, v in dados.items()}
    erros = validar(p, aba)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    return JSONResponse({"ok": True, "oficio": gera_oficio(p, aba)})


app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="statics")
