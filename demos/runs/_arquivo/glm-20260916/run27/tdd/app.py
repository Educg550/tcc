import re
from datetime import datetime
from pathlib import Path

from fastapi import Body, FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI()

OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao_trabalho",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg_rnm",
    "nome_banco",
    "agencia",
    "conta",
]


def texto(dados, chave):
    valor = dados.get(chave, "")
    return valor.strip() if isinstance(valor, str) else ""


def so_digitos(valor):
    return re.fullmatch(r"[0-9]+", valor) is not None


def valor_maior_que_zero(valor):
    numero = valor.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(numero) > 0
    except ValueError:
        return False


def email_valido(email):
    partes = email.split("@")
    return len(partes) == 2 and partes[0] != "" and partes[1] != ""


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    soma1 = sum(a * b for a, b in zip(digitos[:9], range(10, 1, -1)))
    digito1 = (soma1 * 10) % 11 % 10
    soma2 = sum(a * b for a, b in zip(digitos[:10], range(11, 1, -1)))
    digito2 = (soma2 * 10) % 11 % 10
    return digitos[9] == digito1 and digitos[10] == digito2


def data_valida(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def avaliar(dados):
    chaves = set(OBRIGATORIOS) | {"link_evento", "complemento"}
    if dados.get("aba") == "alunos":
        chaves |= {"nivel", "tipo_auxilio"}
    v = {chave: texto(dados, chave) for chave in chaves}
    obrigatorios = list(OBRIGATORIOS)
    if dados.get("aba") == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    erros = []
    if any(not v[chave] for chave in obrigatorios):
        erros.append("Preencha todos os campos")
    if v["n_usp"] and not so_digitos(v["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if v["agencia"] and not so_digitos(v["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if v["valor_solicitado"] and not valor_maior_que_zero(v["valor_solicitado"]):
        erros.append("Valor solicitado deve ser maior que 0")
    if v["email"] and not email_valido(v["email"]):
        erros.append("E-mail inválido")
    if v["cpf"] and not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", v["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif v["cpf"] and not cpf_valido(v["cpf"]):
        erros.append("CPF inválido")
    if v["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", v["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if v["data_nascimento"] and not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", v["data_nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif v["data_nascimento"] and not data_valida(v["data_nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros, v


def redigir_oficio(aba, v):
    linhas = [
        f"Interessada(o): {v['nome_completo']} - {v['n_usp']}",
        f"E-mail: {v['email']}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {v['tipo_auxilio']}")
        linhas.append(f"Programa: {v['programa']} - {v['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {v['programa']}")
    linhas += [
        "",
        f"A CCP-{v['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {v['nome_evento']}",
        f"Período: {v['periodo_evento']}",
        f"Local: {v['cidade_evento']} - {v['estado_evento']} - {v['pais_evento']}",
    ]
    if v["link_evento"]:
        linhas.append(f"Link do evento: {v['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {v['apresentacao_trabalho']}",
        f"Valor solicitado: {v['valor_solicitado']}",
        f"Detalhamento: {v['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{v['logradouro']}, {v['numero']}",
    ]
    if v["complemento"]:
        linhas.append(f"Complemento: {v['complemento']}")
    linhas += [
        f"CEP: {v['cep']}",
        f"{v['bairro']}, {v['cidade']} - {v['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {v['data_nascimento']}",
        f"CPF: {v['cpf']}",
        f"RG / RNM: {v['rg_rnm']}",
        f"Banco: {v['nome_banco']}",
        f"Agência: {v['agencia']}",
        f"Conta: {v['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
async def receber_solicitacao(response: Response, dados: dict = Body(...)):
    erros, valores = avaliar(dados)
    if erros:
        response.status_code = 400
        return {"erros": erros}
    return {"oficio": redigir_oficio(dados.get("aba"), valores)}


@app.get("/")
async def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
async def folha_de_estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
async def roteiro():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets", check_dir=False), name="assets")
