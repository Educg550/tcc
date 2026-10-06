import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_RE = re.compile(r"^\d{5}-\d{3}$")
DATA_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CAMPOS = (
    "nome", "n_usp", "programa", "email", "evento", "periodo", "cidade_evento",
    "estado_evento", "pais_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
)


def obrigatorios(aba):
    campos = list(CAMPOS)
    if aba != "docentes":
        campos += ["nivel", "tipo_auxilio"]
    return campos


def cpf_valido(cpf):
    d = [int(c) for c in re.sub(r"\D", "", cpf)]
    for n in (9, 10):
        soma = sum(d[i] * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != d[n]:
            return False
    return True


def data_existente(valor):
    dia, mes, ano = (int(x) for x in valor.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formatar_moeda(valor):
    centavos = int(re.sub(r"\D", "", str(valor)) or 0)
    inteiro, resto = divmod(centavos, 100)
    return "R$ " + f"{inteiro:,}".replace(",", ".") + f",{resto:02d}"


def valida(dados, aba):
    def v(campo):
        return str(dados.get(campo) or "").strip()

    erros = []
    if any(not v(c) for c in obrigatorios(aba)):
        erros.append("Preencha todos os campos")
    if v("n_usp") and not v("n_usp").isdigit():
        erros.append("N. USP deve conter apenas números")
    if v("agencia") and not v("agencia").isdigit():
        erros.append("Número da agência deve conter apenas números")
    if v("valor"):
        digitos = re.sub(r"\D", "", v("valor"))
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if v("email") and not EMAIL_RE.match(v("email")):
        erros.append("E-mail inválido")
    if v("cpf") and not CPF_RE.match(v("cpf")):
        erros.append("CPF deve estar no formato 000.000.000-00")
    if v("cep") and not CEP_RE.match(v("cep")):
        erros.append("CEP deve estar no formato 00000-000")
    if v("data_nascimento") and not DATA_RE.match(v("data_nascimento")):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if v("cpf") and CPF_RE.match(v("cpf")) and not cpf_valido(v("cpf")):
        erros.append("CPF inválido")
    if v("data_nascimento") and DATA_RE.match(v("data_nascimento")) and not data_existente(v("data_nascimento")):
        erros.append("Data de nascimento inválida")
    return erros


def gerar_oficio(dados, aba):
    def v(campo):
        return str(dados.get(campo) or "").strip()

    if aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {v('programa')}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {v('tipo_auxilio')}"
        programa = f"Programa: {v('programa')} - {v('nivel')}"

    linhas = [
        f"Interessada(o): {v('nome')} - {v('n_usp')}",
        f"E-mail: {v('email')}",
        assunto,
        programa,
        "",
        f"A CCP-{v('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v('evento')}",
        f"Período: {v('periodo')}",
        f"Local: {v('cidade_evento')} - {v('estado_evento')} - {v('pais_evento')}",
    ]
    if v("link"):
        linhas.append(f"Link do evento: {v('link')}")
    linhas += [
        f"Apresentação de trabalho: {v('apresentacao')}",
        f"Valor solicitado: {formatar_moeda(v('valor'))}",
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
    dados = None
    try:
        dados = await request.json()
    except Exception:
        try:
            dados = dict(await request.form())
        except Exception:
            dados = None
    if not isinstance(dados, dict):
        dados = {}
    aba = str(dados.get("aba") or "alunos").strip().lower()
    if aba not in ("alunos", "docentes"):
        aba = "alunos"
    erros = valida(dados, aba)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados, aba)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="static")
