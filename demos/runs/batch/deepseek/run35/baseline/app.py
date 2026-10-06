import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS_ALUNOS = [
    "nome", "n_usp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg", "banco", "agencia", "conta",
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]


def _cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11:
        return False
    for pesos in ((10, 9, 8, 7, 6, 5, 4, 3, 2), (11, 10, 9, 8, 7, 6, 5, 4, 3, 2)):
        soma = sum(n * p for n, p in zip(nums, pesos))
        digito = 11 - (soma % 11)
        if digito >= 10:
            digito = 0
        if digito != nums[len(pesos)]:
            return False
    return True


def _data_valida(s):
    dia, mes, ano = (int(x) for x in s.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _valor_formatado(dados):
    digitos = re.sub(r"\D", "", dados.get("valor") or "")
    if not digitos:
        return ""
    n = int(digitos)
    reais = f"{n // 100:,}".replace(",", ".")
    return f"R$ {reais},{n % 100:02d}"


def validar(campos, dados):
    g = lambda k: (dados.get(k) or "").strip()
    erros = []

    if any(not g(k) for k in campos):
        erros.append("Preencha todos os campos")

    nusp = g("n_usp")
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = g("agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = g("valor")
    digitos = re.sub(r"\D", "", valor)
    if valor and (not digitos or int(digitos) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = g("email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = g("cpf")
    cpf_ok = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = g("cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nasc = g("data_nascimento")
    nasc_ok = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nasc))
    if nasc and not nasc_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_ok and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if nasc and nasc_ok and not _data_valida(nasc):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(aba, dados):
    g = lambda k: (dados.get(k) or "").strip()
    if aba == "alunos":
        assunto = g("tipo_auxilio")
        linha_programa = f"{g('programa')} - {g('nivel')}"
    else:
        assunto = "Verba do programa"
        linha_programa = g("programa")

    linhas = [
        f"Interessada(o): {g('nome')} - {g('n_usp')}",
        f"E-mail: {g('email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {linha_programa}",
        "",
        f"A CCP-{g('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {g('nome_evento')}",
        f"Período: {g('periodo')}",
        f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}",
    ]
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {g('apresentacao')}",
        f"Valor solicitado: {_valor_formatado(dados)}",
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


@app.post("/solicitar")
async def solicitar(request: Request):
    corpo = await request.json()
    aba = corpo.get("aba")
    dados = corpo.get("dados") or {}
    if aba == "alunos":
        campos = CAMPOS_ALUNOS
    else:
        aba = "docentes"
        campos = CAMPOS_DOCENTES

    erros = validar(campos, dados)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"oficio": gerar_oficio(aba, dados)})


BASE = Path(__file__).resolve().parent
app.mount("/", StaticFiles(directory=str(BASE), html=True), name="static")
