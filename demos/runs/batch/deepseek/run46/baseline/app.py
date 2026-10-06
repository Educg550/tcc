import re
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

# Campos obrigatórios comuns às duas abas.
OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def _obrigatorios(aba):
    if aba == "docentes":
        return OBRIGATORIOS
    return OBRIGATORIOS + ["nivel", "tipo_auxilio"]


def _cpf_valido(cpf):
    d = re.sub(r"\D", "", cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False

    def dv(base, peso):
        soma = sum(int(c) * (peso - i) for i, c in enumerate(base))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    return dv(d[:9], 10) == int(d[9]) and dv(d[:10], 11) == int(d[10])


def _formata_brl(centavos):
    reais, resto = divmod(centavos, 100)
    milhares = f"{reais:,}".replace(",", ".")
    return f"R$ {milhares},{resto:02d}"


def _valida(aba, c):
    erros = []
    g = lambda k: c.get(k, "").strip()

    if any(not g(k) for k in _obrigatorios(aba)):
        erros.append("Preencha todos os campos")

    n_usp = g("n_usp")
    agencia = g("agencia")
    valor = g("valor")
    email = g("email")
    cpf = g("cpf")
    cep = g("cep")
    data = g("data_nascimento")

    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    centavos = None
    if valor:
        digitos = re.sub(r"\D", "", valor)
        centavos = int(digitos) if digitos else 0
        if centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf)) if cpf else False
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", data)) if data else False
    if data and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_no_formato:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros, centavos


def _oficio(aba, c, centavos):
    g = lambda k: c.get(k, "").strip()
    programa = g("programa")

    linhas = [
        f"Interessada(o): {g('nome')} - {g('n_usp')}",
        f"E-mail: {g('email')}",
    ]
    if aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {g('tipo_auxilio')}")
        linhas.append(f"Programa: {programa} - {g('nivel')}")

    linhas += [
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {g('evento')}",
        f"Período: {g('periodo')}",
        f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}",
    ]
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {g('apresentacao')}",
        f"Valor solicitado: {_formata_brl(centavos)}",
        f"Detalhamento: {g('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{g('logradouro')}, {g('numero')}",
    ]
    if g("complemento"):
        linhas.append(f"Complemento: {g('complemento')}")
    linhas += [
        f"CEP: {g('cep')}",
        f"{g('bairro')}, {g('cidade')} - {g('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {g('data_nascimento')}",
        f"CPF: {g('cpf')}",
        f"RG / RNM: {g('rg')}",
        f"Banco: {g('banco')}",
        f"Agência: {g('agencia')}",
        f"Conta: {g('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def solicitar(payload: dict):
    aba = payload.get("aba") or "alunos"
    campos = {
        k: ("" if v is None else str(v))
        for k, v in (payload.get("campos") or {}).items()
    }

    erros, centavos = _valida(aba, campos)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(aba, campos, centavos)}


@app.get("/")
def raiz():
    return FileResponse("index.html", media_type="text/html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse("app.js", media_type="application/javascript")
