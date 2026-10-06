from pathlib import Path
import re

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


def _txt(d, chave):
    return str(d.get(chave) or "").strip()


def _cpf_valido(cpf):
    d = re.sub(r"\D", "", cpf)
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(d[i]):
            return False
    return True


def _data_valida(data):
    dia, mes, ano = (int(p) for p in data.split("/"))
    if mes < 1 or mes > 12 or dia < 1:
        return False
    bissexto = ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)
    dias = [31, 29 if bissexto else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dia <= dias[mes - 1]


def validar(d):
    alunos = d.get("aba") == "alunos"
    erros = []

    obrigatorios = [
        "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
        "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
    ]
    if alunos:
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not _txt(d, c) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _txt(d, "n_usp")
    if n_usp and not re.fullmatch(r"\d+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = _txt(d, "agencia")
    if agencia and not re.fullmatch(r"\d+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = _txt(d, "valor")
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _txt(d, "email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = _txt(d, "cpf")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _txt(d, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = _txt(d, "data_nascimento")
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return erros


def _moeda(valor):
    digitos = re.sub(r"\D", "", str(valor))
    if not digitos:
        return valor
    n = int(digitos)
    reais = f"{n // 100:,}".replace(",", ".")
    return f"R$ {reais},{n % 100:02d}"


def gerar_oficio(d):
    alunos = d.get("aba") == "alunos"
    linhas = [
        f"Interessada(o): {_txt(d, 'nome_completo')} - {_txt(d, 'n_usp')}",
        f"E-mail: {_txt(d, 'email')}",
    ]
    if alunos:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {_txt(d, 'tipo_auxilio')}")
        linhas.append(f"Programa: {_txt(d, 'programa')} - {_txt(d, 'nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {_txt(d, 'programa')}")
    linhas += [
        "",
        f"A CCP-{_txt(d, 'programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_txt(d, 'nome_evento')}",
        f"Período: {_txt(d, 'periodo')}",
        f"Local: {_txt(d, 'cidade_evento')} - {_txt(d, 'estado_evento')} - {_txt(d, 'pais_evento')}",
    ]
    if _txt(d, "link_evento"):
        linhas.append(f"Link do evento: {_txt(d, 'link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {_txt(d, 'apresentacao')}",
        f"Valor solicitado: {_moeda(_txt(d, 'valor'))}",
        f"Detalhamento: {_txt(d, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_txt(d, 'logradouro')}, {_txt(d, 'numero')}",
    ]
    if _txt(d, "complemento"):
        linhas.append(f"Complemento: {_txt(d, 'complemento')}")
    linhas += [
        f"CEP: {_txt(d, 'cep')}",
        f"{_txt(d, 'bairro')}, {_txt(d, 'cidade')} - {_txt(d, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_txt(d, 'data_nascimento')}",
        f"CPF: {_txt(d, 'cpf')}",
        f"RG / RNM: {_txt(d, 'rg')}",
        f"Banco: {_txt(d, 'banco')}",
        f"Agência: {_txt(d, 'agencia')}",
        f"Conta: {_txt(d, 'conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    d = await request.json()
    erros = validar(d)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(d)}
