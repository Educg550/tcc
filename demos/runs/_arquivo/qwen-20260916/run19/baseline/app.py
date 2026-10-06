import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


def _digitos(v):
    return re.sub(r"\D", "", v or "")


def _cpf_valido(v):
    d = _digitos(v)
    if len(d) != 11 or d == d[0] * 11:
        return False
    n = [int(c) for c in d]
    for k in (10, 11):
        soma = sum(n[i] * (k - i) for i in range(k - 1))
        if (soma * 10) % 11 % 10 != n[k - 1]:
            return False
    return True


def _data_valida(v):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", v)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mes <= 12) or not (1 <= ano <= 9999):
        return False
    dias_mes = [31, 29 if (ano % 4 == 0 and ano % 100 != 0) or ano % 400 == 0 else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dia <= dias_mes[mes - 1]


def _moeda(v):
    reais = int(v) / 100.0
    inteiro, cent = f"{reais:.2f}".split(".")
    inteiro = "{:,}".format(int(inteiro)).replace(",", ".")
    return f"R$ {inteiro},{cent}"


@app.get("/")
def index():
    return HTMLResponse(open("index.html", encoding="utf-8").read())


@app.get("/style.css")
def css():
    return HTMLResponse(open("style.css", encoding="utf-8").read(), media_type="text/css")


@app.get("/app.js")
def js():
    return HTMLResponse(open("app.js", encoding="utf-8").read(), media_type="application/javascript")


@app.post("/solicitacao/{tipo}")
def solicita(tipo: str, dados: dict):
    def get(campo):
        return (dados.get(campo) or "").strip()

    obrigatorios = [
        "nome", "nusp", "email", "programa", "evento", "periodo", "cidade_evento",
        "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
        "nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado",
        "cpf", "rg", "banco", "agencia", "conta",
    ]
    if tipo == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not get(c) for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if get("nusp") and not get("nusp").isdigit():
        erros.append("N. USP deve conter apenas números")
    if get("agencia") and not get("agencia").isdigit():
        erros.append("Número da agência deve conter apenas números")
    if get("valor") and not (get("valor").isdigit() and int(get("valor")) > 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if get("email") and ("@" not in get("email") or get("email").split("@", 1)[1].strip(".") == ""):
        erros.append("E-mail inválido")
    if get("cpf"):
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", get("cpf")):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(get("cpf")):
            erros.append("CPF inválido")
    if get("cep") and not re.fullmatch(r"\d{5}-\d{3}", get("cep")):
        erros.append("CEP deve estar no formato 00000-000")
    if get("nascimento"):
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", get("nascimento")):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(get("nascimento")):
            erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    assunto = "Solicitação de Auxílio Financeiro - " + (
        get("tipo_auxilio") if tipo == "alunos" else "Verba do programa")
    programa_linha = f"Programa: {get('programa')}"
    if tipo == "alunos":
        programa_linha += f" - {get('nivel')}"

    linhas = [
        f"Interessada(o): {get('nome')} - {get('nusp')}",
        f"E-mail: {get('email')}",
        assunto,
        programa_linha,
        "",
        "A CCP-" + get("programa") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {get('evento')}",
        f"Período: {get('periodo')}",
        f"Local: {get('cidade_evento')} - {get('estado_evento')} - {get('pais_evento')}",
    ]
    if get("link"):
        linhas.append(f"Link do evento: {get('link')}")
    linhas += [
        f"Apresentação de trabalho: {get('apresentacao')}",
        f"Valor solicitado: {_moeda(get('valor'))}",
        f"Detalhamento: {get('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{get('logradouro')}, {get('numero')}",
    ]
    if get("complemento"):
        linhas.append(f"Complemento: {get('complemento')}")
    linhas += [
        f"CEP: {get('cep')}",
        f"{get('bairro')}, {get('cidade')} - {get('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {get('nascimento')}",
        f"CPF: {get('cpf')}",
        f"RG / RNM: {get('rg')}",
        f"Banco: {get('banco')}",
        f"Agência: {get('agencia')}",
        f"Conta: {get('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return {"ok": True, "oficio": "\n".join(linhas)}
