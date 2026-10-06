import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


def _txt(d, k):
    v = d.get(k)
    return v.strip() if isinstance(v, str) else ""


def _cpf_valido(cpf):
    n = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(n) != 11:
        return False
    for tam in (9, 10):
        soma = sum(n[i] * (tam + 1 - i) for i in range(tam))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != n[tam]:
            return False
    return True


def _data_valida(s):
    dia, mes, ano = (int(x) for x in s.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(d):
    aba = _txt(d, "aba")
    obrigatorios = [
        "nome", "n_usp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado",
        "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not _txt(d, k) for k in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = _txt(d, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _txt(d, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _txt(d, "valor")
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = _txt(d, "email")
    if email and not RE_EMAIL.match(email):
        erros.append("E-mail inválido")

    cpf = _txt(d, "cpf")
    if cpf:
        if not RE_CPF.match(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = _txt(d, "cep")
    if cep and not RE_CEP.match(cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_nasc = _txt(d, "data_nascimento")
    if data_nasc:
        if not RE_DATA.match(data_nasc):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data_nasc):
            erros.append("Data de nascimento inválida")

    return erros


def _formata_moeda(digitos):
    reais, cent = divmod(int(digitos), 100)
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{cent:02d}"


def gerar_oficio(d):
    aba = _txt(d, "aba")
    programa = _txt(d, "programa")
    if aba == "alunos":
        assunto = _txt(d, "tipo_auxilio")
        programa_linha = f"{programa} - {_txt(d, 'nivel')}"
    else:
        assunto = "Verba do programa"
        programa_linha = programa

    link = _txt(d, "link_evento")
    complemento = _txt(d, "complemento")
    valor = _formata_moeda(re.sub(r"\D", "", _txt(d, "valor")))

    linhas = [
        f"Interessada(o): {_txt(d, 'nome')} - {_txt(d, 'n_usp')}",
        f"E-mail: {_txt(d, 'email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {programa_linha}",
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_txt(d, 'evento')}",
        f"Período: {_txt(d, 'periodo')}",
        f"Local: {_txt(d, 'cidade_evento')} - {_txt(d, 'estado_evento')} - {_txt(d, 'pais_evento')}",
    ]
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {_txt(d, 'apresentacao')}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {_txt(d, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_txt(d, 'logradouro')}, {_txt(d, 'numero')}",
    ]
    if complemento:
        linhas.append(f"Complemento: {complemento}")
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


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    dados = await request.json()
    erros = validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(dados)}
