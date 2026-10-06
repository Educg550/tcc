import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


CAMPOS_OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "nome_evento", "periodo",
    "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade_end",
    "estado_end", "cpf", "rg", "banco", "agencia", "conta",
)


def formatar_valor(valor):
    """Os dígitos recebidos são os centavos; formata como moeda brasileira."""
    centavos = int(re.sub(r"\D", "", valor))
    reais, centesimos = divmod(centavos, 100)
    milhar = format(reais, ",").replace(",", ".")
    return f"R$ {milhar},{centesimos:02d}"


def cpf_valido(cpf):
    numeros = [int(caractere) for caractere in re.sub(r"\D", "", cpf)]
    if len(set(numeros)) == 1:
        return False
    for digito in (9, 10):
        soma = sum(numeros[indice] * (digito + 1 - indice) for indice in range(digito))
        if soma * 10 % 11 % 10 != numeros[digito]:
            return False
    return True


def data_existe(data):
    dia, mes, ano = (int(parte) for parte in data.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(dados, aba):
    erros = []
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_de_auxilio"]
    if any(dados.get(campo, "").strip() == "" for campo in obrigatorios):
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
        if not digitos.isdigit() or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("email", "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = dados.get("cpf", "").strip()
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = dados.get("cep", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get("data_nascimento", "").strip()
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_existe(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(dados, aba):
    if aba == "docentes":
        assunto = "Verba do programa"
        programa = f"Programa: {dados['programa']}"
    else:
        assunto = dados["tipo_de_auxilio"]
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"

    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        programa,
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade']} - {dados['estado']} - {dados['pais']}",
    ]
    if dados.get("link", "").strip():
        linhas.append(f"Link do evento: {dados['link']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {formatar_valor(dados['valor'])}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados.get("complemento", "").strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade_end']} - {dados['estado_end']}",
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
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitacao(request: Request):
    formulario = await request.form()
    dados = {campo: str(valor) for campo, valor in formulario.items()}
    aba = "docentes" if dados.get("aba") == "docentes" else "alunos"
    erros = validar(dados, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": montar_oficio(dados, aba)}
