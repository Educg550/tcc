import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=str(BASE_DIR / "assets")), name="assets")


def ler_arquivo(nome):
    return (BASE_DIR / nome).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def indice():
    return ler_arquivo("index.html")


@app.get("/style.css")
def estilo():
    return HTMLResponse(ler_arquivo("style.css"), media_type="text/css")


@app.get("/app.js")
def script():
    return HTMLResponse(ler_arquivo("app.js"), media_type="application/javascript")


def so_digitos(texto):
    return bool(re.fullmatch(r"\d+", texto))


def email_valido(texto):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s.]+\.[^@\s]+", texto))


def cpf_valido(texto):
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto):
        return False
    digitos = [int(c) for c in re.sub(r"\D", "", texto)]
    for tamanho in (9, 10):
        soma = sum(digitos[i] * (tamanho - i) for i in range(tamanho))
        resto = (soma * 10) % 11
        digitos.append(0 if resto == 10 else resto)
    return digitos[9] == digitos[10] if digitos[9] == digitos[10] else digitos[10] == digitos[11]


def data_valida(texto):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", texto)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    dias_mes = [31, 29 if (ano % 4 == 0 and ano % 100 != 0) or ano % 400 == 0 else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= mes <= 12 and 1 <= dia <= dias_mes[mes - 1]


def formatar_valor(texto):
    centavos = int(re.sub(r"\D", "", texto))
    inteiro, decimais = divmod(centavos, 100)
    parte = f"{inteiro:,}".replace(",", ".")
    return f"R$ {parte},{decimais:02d}"


OBRIGATORIOS = [
    "nome_completo", "nusp", "programa", "nivel", "tipo_auxilio",
    "email", "nome_evento", "periodo", "cidade_evento", "estado_evento",
    "pais_evento", "valor_solicitado", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]


@app.post("/api/solicitacao")
def solicitar(pedido: dict):
    aba = pedido.get("aba", "alunos")
    dados = {campo: (pedido.get(campo) or "").strip() for campo in set(OBRIGATORIOS) | {"complemento", "link"}}

    obrigatorios = [c for c in OBRIGATORIOS if aba == "docentes" and c in ("nivel", "tipo_auxilio")] and \
        [c for c in OBRIGATORIOS if c not in ("nivel", "tipo_auxilio")] or OBRIGATORIOS

    erros = []
    if any(not dados[c] for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if dados["nusp"] and not so_digitos(dados["nusp"]):
        erros.append("N. USP deve conter apenas números")
    if dados["agencia"] and not so_digitos(dados["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if dados["valor_solicitado"]:
        digitos = re.sub(r"\D", "", dados["valor_solicitado"])
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if dados["email"] and "@" not in dados["email"]:
        erros.append("E-mail inválido")
    if dados["cpf"] and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", dados["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif dados["cpf"] and not cpf_valido(dados["cpf"]):
        erros.append("CPF inválido")
    if dados["cep"] and not re.fullmatch(r"\d{5}-\d{3}", dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if dados["data_nascimento"] and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados["data_nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif dados["data_nascimento"] and not data_valida(dados["data_nascimento"]):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['nusp']}",
        f"E-mail: {dados['email']}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}")
        linhas.append(f"Programa: {dados['programa']} - {dados['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {dados['programa']}")

    linhas += [
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link"]:
        linhas.append(f"Link do evento: {dados['link']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {formatar_valor(dados['valor_solicitado'])}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return {"ok": True, "oficio": "\n".join(linhas)}
