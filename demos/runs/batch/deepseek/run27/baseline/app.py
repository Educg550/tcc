import re
from datetime import date

from fastapi import FastAPI, Request
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


CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def cpf_valido(cpf):
    n = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(n) != 11:
        return False
    for i in (9, 10):
        soma = sum(n[j] * (i + 1 - j) for j in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != n[i]:
            return False
    return True


def data_valida(s):
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    try:
        date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return False
    return True


def validar(d, tab):
    v = lambda k: str(d.get(k, "")).strip()

    obrig = CAMPOS_OBRIGATORIOS[:]
    if tab == "alunos":
        obrig += ["nivel", "tipo_auxilio"]

    n_usp_ruim = bool(v("n_usp")) and not v("n_usp").isdigit()
    agencia_ruim = bool(v("agencia")) and not v("agencia").isdigit()

    valor_ruim = False
    if v("valor"):
        digitos = re.sub(r"\D", "", v("valor"))
        valor_ruim = (not digitos) or int(digitos) == 0

    email_ruim = bool(v("email")) and not re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v("email")
    )

    cpf = v("cpf")
    cpf_formato = bool(cpf) and not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf)
    cpf_digitos = bool(cpf) and not cpf_formato and not cpf_valido(cpf)

    cep = v("cep")
    cep_ruim = bool(cep) and not re.match(r"^\d{5}-\d{3}$", cep)

    dn = v("data_nascimento")
    dn_formato = bool(dn) and not re.match(r"^\d{2}/\d{2}/\d{4}$", dn)
    dn_invalida = bool(dn) and not dn_formato and not data_valida(dn)

    erros = []
    if any(not v(c) for c in obrig):
        erros.append("Preencha todos os campos")
    if n_usp_ruim:
        erros.append("N. USP deve conter apenas números")
    if agencia_ruim:
        erros.append("Número da agência deve conter apenas números")
    if valor_ruim:
        erros.append("Valor solicitado deve ser maior que 0")
    if email_ruim:
        erros.append("E-mail inválido")
    if cpf_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if cep_ruim:
        erros.append("CEP deve estar no formato 00000-000")
    if dn_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_digitos:
        erros.append("CPF inválido")
    if dn_invalida:
        erros.append("Data de nascimento inválida")
    return erros


def formatar_valor(v):
    digitos = re.sub(r"\D", "", str(v)).lstrip("0") or "0"
    digitos = digitos.zfill(3)
    centavos = digitos[-2:]
    reais = f"{int(digitos[:-2]):,}".replace(",", ".")
    return f"R$ {reais},{centavos}"


def gerar_oficio(tab, d):
    v = lambda k: str(d.get(k, "")).strip()

    if tab == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {v('tipo_auxilio')}"
        programa = f"{v('programa')} - {v('nivel')}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = v("programa")

    linhas = [
        f"Interessada(o): {v('nome')} - {v('n_usp')}",
        f"E-mail: {v('email')}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{v('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v('nome_evento')}",
        f"Período: {v('periodo')}",
        f"Local: {v('cidade_evento')} - {v('estado_evento')} - {v('pais_evento')}",
    ]
    if v("link"):
        linhas.append(f"Link do evento: {v('link')}")
    linhas += [
        f"Apresentação de trabalho: {v('apresentacao')}",
        f"Valor solicitado: {formatar_valor(v('valor'))}",
        f"Detalhamento: {v('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v('logradouro')}, {v('numero')}",
    ]
    if v("complemento"):
        linhas.append(f"Complemento: {v('complemento')}")
    linhas += [
        f"CEP: {v('cep')}",
        f"{v('bairro')}, {v('cidade')} - {v('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v('data_nascimento')}",
        f"CPF: {v('cpf')}",
        f"RG / RNM: {v('rg')}",
        f"Banco: {v('banco')}",
        f"Agência: {v('agencia')}",
        f"Conta: {v('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(request: Request):
    dados = await request.json()
    tab = dados.get("tab", "alunos")
    erros = validar(dados, tab)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(tab, dados)}
