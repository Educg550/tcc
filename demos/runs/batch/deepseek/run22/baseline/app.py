import re
from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    for i in (9, 10):
        soma = sum(digitos[j] * ((i + 1) - j) for j in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[i]:
            return False
    return True


def data_valida(texto):
    dia, mes, ano = (int(p) for p in texto.split("/"))
    try:
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def validar(aba, dados):
    erros = []

    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not dados.get(campo, "").strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados.get("n_usp", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("agencia", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = dados.get("valor", "").strip()
    if valor:
        digitos = re.sub(r"\D", "", valor)
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("email", "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = dados.get("cpf", "").strip()
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = dados.get("cep", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get("data_nascimento", "").strip()
    data_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_no_formato and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(aba, dados):
    linhas = [
        f"Interessada(o): {dados.get('nome', '')} - {dados.get('n_usp', '')}",
        f"E-mail: {dados.get('email', '')}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados.get('tipo_auxilio', '')}")
        linhas.append(f"Programa: {dados.get('programa', '')} - {dados.get('nivel', '')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados.get('programa', '')}")

    linhas += [
        "",
        f"A CCP-{dados.get('programa', '')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.get('evento', '')}",
        f"Período: {dados.get('periodo', '')}",
        f"Local: {dados.get('cidade_evento', '')} - {dados.get('estado_evento', '')} - {dados.get('pais_evento', '')}",
    ]

    link = dados.get("link", "").strip()
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {dados.get('apresentacao', '')}",
        f"Valor solicitado: {dados.get('valor', '')}",
        f"Detalhamento: {dados.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
    ]

    complemento = dados.get("complemento", "").strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {dados.get('cep', '')}",
        f"{dados.get('bairro', '')}, {dados.get('cidade', '')} - {dados.get('estado', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.get('data_nascimento', '')}",
        f"CPF: {dados.get('cpf', '')}",
        f"RG / RNM: {dados.get('rg', '')}",
        f"Banco: {dados.get('banco', '')}",
        f"Agência: {dados.get('agencia', '')}",
        f"Conta: {dados.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


def normalizar(dados):
    return {chave: ("" if valor is None else str(valor)) for chave, valor in dados.items()}


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


@app.post("/api/solicitar")
async def solicitar(request: Request):
    if request.headers.get("content-type", "").startswith("application/json"):
        corpo = await request.json()
        aba = corpo.get("aba", "alunos")
        dados = normalizar(corpo.get("dados", {}))
    else:
        formulario = await request.form()
        aba = formulario.get("aba", "alunos")
        dados = normalizar({c: v for c, v in formulario.items() if c != "aba"})

    erros = validar(aba, dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(aba, dados)}
