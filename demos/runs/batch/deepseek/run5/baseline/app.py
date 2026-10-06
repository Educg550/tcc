import re
from datetime import datetime

from fastapi import FastAPI
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


def cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[j]) * (i + 1 - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def validar(dados, aba):
    campos = CAMPOS_DOCENTES if aba == "docentes" else CAMPOS_ALUNOS
    erros = []

    if any(not (dados.get(c) or "").strip() for c in campos):
        erros.append("Preencha todos os campos")

    n_usp = (dados.get("n_usp") or "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas n\u00fameros")

    agencia = (dados.get("agencia") or "").strip()
    if agencia and not agencia.isdigit():
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")

    valor = (dados.get("valor") or "").strip()
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = (dados.get("email") or "").strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inv\u00e1lido")

    cpf = (dados.get("cpf") or "").strip()
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inv\u00e1lido")

    cep = (dados.get("cep") or "").strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = (dados.get("data_nascimento") or "").strip()
    if data:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(p) for p in data.split("/"))
            try:
                datetime(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inv\u00e1lida")

    return erros


def formatar_moeda(valor):
    digitos = re.sub(r"\D", "", valor) or "0"
    reais, centavos = divmod(int(digitos), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def gerar_oficio(d, aba):
    v = lambda chave: (d.get(chave) or "").strip()

    programa = v("programa")

    linhas = [
        f"Interessada(o): {v('nome')} - {v('n_usp')}",
        f"E-mail: {v('email')}",
    ]

    if aba == "docentes":
        linhas.append("Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    else:
        linhas.append(f"Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - {v('tipo_auxilio')}")
        linhas.append(f"Programa: {programa} - {v('nivel')}")

    linhas += [
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v('nome_evento')}",
        f"Per\u00edodo: {v('periodo')}",
        f"Local: {v('cidade_evento')} - {v('estado_evento')} - {v('pais_evento')}",
    ]

    if v("link_evento"):
        linhas.append(f"Link do evento: {v('link_evento')}")

    linhas += [
        f"Apresenta\u00e7\u00e3o de trabalho: {v('apresentacao')}",
        f"Valor solicitado: {formatar_moeda(v('valor'))}",
        f"Detalhamento: {v('detalhamento')}",
        "",
        "Endere\u00e7o da(o) interessada(o)",
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
        f"Ag\u00eancia: {v('agencia')}",
        f"Conta: {v('conta')}",
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(corpo: dict):
    aba = "docentes" if corpo.get("aba") == "docentes" else "alunos"
    dados = corpo.get("dados") or {}
    dados = {k: (v if isinstance(v, str) else "") for k, v in dados.items()}

    erros = validar(dados, aba)
    if erros:
        return {"ok": False, "erros": erros}

    return {"ok": True, "oficio": gerar_oficio(dados, aba)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
