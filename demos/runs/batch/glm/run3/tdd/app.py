from datetime import date
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


def _limpar(v):
    return re.sub(r"\D", "", v or "")


def _formatar_valor(s):
    d = _limpar(s)
    if not d:
        return ""
    d = d.lstrip("0") or "0"
    cent = d[-2:]
    int = d[:-2]
    int = int.zfill(1) if int else ""
    partes = []
    while len(int) > 3:
        partes.insert(0, int[-3:])
        int = int[:-3]
    if int:
        partes.insert(0, int)
    inteiro = ".".join(partes)
    return f"R$ {inteiro},{cent}"

def _formatar_cpf(d):
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def _cpf_valido(d):
    if len(d) != 11 or d == d[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * ((i + 1 - j) if i == 9 else (i - j + 2)) for j in range(i))
        resto = soma % 11
        dig = 0 if resto < 2 else 11 - resto
        if dig != int(d[i]):
            return False
    return True

def _validar(dados):
    erros = []
    tipo = dados.get("tipo", "alunos")
    campos = ["nome", "n_usp", "programa", "email", "evento", "periodo", "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end", "estado_end", "cpf", "rg", "banco", "agencia", "conta"]
    if tipo == "alunos":
        campos += ["nivel", "auxilio"]
    if any(not str(dados.get(c, "")).strip() for c in campos):
        erros.append("Preencha todos os campos")
    if not _limpar(dados.get("n_usp", "")) == str(dados.get("n_usp", "")):
        erros.append("N. USP deve conter apenas números")
    if not _limpar(dados.get("agencia", "")) == str(dados.get("agencia", "")):
        erros.append("Número da agência deve conter apenas números")
    valor_d = _limpar(dados.get("valor", ""))
    try:
        val = int(valor_d)
        if val <= 0:
            raise ValueError
    except ValueError:
        erros.append("Valor solicitado deve ser maior que 0")
    email = str(dados.get("email", ""))
    if "@" not in email or not email.split("@")[-1].strip():
        erros.append("E-mail inválido")
    cpf_d = _limpar(dados.get("cpf", ""))
    if len(cpf_d) != 11:
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(cpf_d):
        erros.append("CPF inválido")
    cep_d = _limpar(dados.get("cep", ""))
    if len(cep_d) != 8:
        erros.append("CEP deve estar no formato 00000-000")
    nasc_d = _limpar(dados.get("data_nascimento", ""))
    if len(nasc_d) != 8:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    else:
        try:
            date(int(nasc_d[4:]), int(nasc_d[2:4]), int(nasc_d[:2]))
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros

def _gerar_oficio(dados):
    tipo = dados.get("tipo", "alunos")
    nome = dados.get("nome", "")
    n_usp = dados.get("n_usp", "")
    programa = dados.get("programa", "")
    email = dados.get("email", "")
    assunto = "Solicitação de Auxílio Financeiro - " + (dados.get("auxilio", "Verba do programa") if tipo == "alunos" else "Verba do programa")
    prog_linha = f"Programa: {programa} - {dados.get('nivel', '')}" if tipo == "alunos" else f"Programa: {programa}"
    valor_fmt = _formatar_valor(dados.get("valor", ""))
    cpf_fmt = _formatar_cpf(_limpar(dados.get("cpf", "")))
    cep_fmt = f"{cep_d[:5]}-{cep_d[5:]}" if len((cep_d := _limpar(dados.get("cep", "")))) == 8 else dados.get("cep", "")
    nasc_fmt = f"{n[:2]}/{n[2:4]}/{n[4:]}" if len((n := _limpar(dados.get("data_nascimento", "")))) == 8 else dados.get("data_nascimento", "")
    linhas = [
        f"Interessada(o): {nome} - {n_usp}",
        f"E-mail: {email}",
        f"Assunto: {assunto}",
        prog_linha,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.get('evento', '')}",
        f"Período: {dados.get('periodo', '')}",
        f"Local: {dados.get('cidade', '')} - {dados.get('estado', '')} - {dados.get('pais', '')}",
    ]
    link = str(dados.get("link", "")).strip()
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {dados.get('apresentacao', '')}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {dados.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
    ]
    comp = str(dados.get("complemento", "")).strip()
    if comp:
        linhas.append(f"Complemento: {comp}")
    linhas += [
        f"CEP: {cep_fmt}",
        f"{dados.get('bairro', '')}, {dados.get('cidade_end', '')} - {dados.get('estado_end', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {nasc_fmt}",
        f"CPF: {cpf_fmt}",
        f"RG / RNM: {dados.get('rg', '')}",
        f"Banco: {dados.get('banco', '')}",
        f"Agência: {dados.get('agencia', '')}",
        f"Conta: {dados.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)

@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/style.css")
def style():
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")

@app.get("/app.js")
def script():
    return FileResponse(BASE_DIR / "app.js", media_type="text/javascript")

@app.post("/api/solicitacao")
async def solicitacao(request: Request):
    dados = await request.json()
    erros = _validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": _gerar_oficio(dados), "titulo": "Solicitação registrada"}
