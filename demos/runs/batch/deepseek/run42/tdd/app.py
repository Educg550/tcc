import datetime
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


def _digitos(valor):
    return re.sub(r"\D", "", str(valor or ""))


def _requeridos(aba):
    base = [
        "nome_completo", "n_usp", "programa", "email", "nome_evento",
        "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
        "valor_solicitado", "detalhamento", "apresentacao", "data_nascimento",
        "logradouro", "numero", "bairro", "cep", "cidade", "estado",
        "cpf", "rg", "banco", "agencia", "conta",
    ]
    if aba == "alunos":
        return base + ["nivel", "tipo_auxilio"]
    return base


def _cpf_valido(cpf):
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        if ((soma * 10) % 11) % 10 != int(cpf[i]):
            return False
    return True


def _moeda(cents):
    reais, cent = divmod(cents, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def _cpf_fmt(d):
    return f"{d[0:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def _cep_fmt(d):
    return f"{d[0:5]}-{d[5:8]}"


def _data_fmt(d):
    return f"{d[0:2]}/{d[2:4]}/{d[4:8]}"


def validar(aba, dados):
    def g(campo):
        return str(dados.get(campo, "") or "").strip()

    erros = []
    if any(not g(c) for c in _requeridos(aba)):
        erros.append("Preencha todos os campos")

    n_usp = g("n_usp")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas n\u00fameros")

    agencia = g("agencia")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    valor = g("valor_solicitado")
    if valor:
        d = _digitos(valor)
        if not d or int(d) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = g("email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inv\u00e1lido")

    cpf = g("cpf")
    if cpf:
        d = _digitos(cpf)
        if len(d) != 11:
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(d):
            erros.append("CPF inv\u00e1lido")

    cep = g("cep")
    if cep and len(_digitos(cep)) != 8:
        erros.append("CEP deve estar no formato 00000-000")

    data = g("data_nascimento")
    if data:
        d = _digitos(data)
        if len(d) != 8:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.date(int(d[4:8]), int(d[2:4]), int(d[0:2]))
            except ValueError:
                erros.append("Data de nascimento inv\u00e1lida")

    return erros


def gerar_oficio(aba, dados):
    def g(campo):
        return str(dados.get(campo, "") or "").strip()

    programa = g("programa")
    if aba == "alunos":
        linha_assunto = (
            "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - " + g("tipo_auxilio")
        )
        linha_programa = f"Programa: {programa} - {g('nivel')}"
    else:
        linha_assunto = "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        linha_programa = f"Programa: {programa}"

    linhas = [
        f"Interessada(o): {g('nome_completo')} - {g('n_usp')}",
        f"E-mail: {g('email')}",
        linha_assunto,
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {g('nome_evento')}",
        f"Per\u00edodo: {g('periodo_evento')}",
        f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}",
    ]
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas += [
        f"Apresenta\u00e7\u00e3o de trabalho: {g('apresentacao')}",
        f"Valor solicitado: {_moeda(int(_digitos(g('valor_solicitado'))))}",
        f"Detalhamento: {g('detalhamento')}",
        "",
        "Endere\u00e7o da(o) interessada(o)",
        f"{g('logradouro')}, {g('numero')}",
    ]
    if g("complemento"):
        linhas.append(f"Complemento: {g('complemento')}")
    linhas += [
        f"CEP: {_cep_fmt(_digitos(g('cep')))}",
        f"{g('bairro')}, {g('cidade')} - {g('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_data_fmt(_digitos(g('data_nascimento')))}",
        f"CPF: {_cpf_fmt(_digitos(g('cpf')))}",
        f"RG / RNM: {g('rg')}",
        f"Banco: {g('banco')}",
        f"Ag\u00eancia: {g('agencia')}",
        f"Conta: {g('conta')}",
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
def solicitar(payload: dict):
    aba = payload.get("aba", "alunos")
    dados = payload.get("dados", {}) or {}
    erros = validar(aba, dados)
    if erros:
        return {"erros": erros, "oficio": ""}
    return {"erros": [], "oficio": gerar_oficio(aba, dados)}
