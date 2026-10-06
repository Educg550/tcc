import os
import re
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

if os.path.isdir("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def pagina():
    return FileResponse("static/index.html")


CAMPOS = (
    "aba",
    "nome_completo",
    "n_usp",
    "programa",
    "nivel",
    "tipo_de_auxilio",
    "email",
    "nome_do_evento",
    "periodo_do_evento",
    "cidade_do_evento",
    "estado_do_evento",
    "pais_do_evento",
    "link_do_evento",
    "valor_solicitado",
    "detalhamento_do_pedido",
    "ira_apresentar_trabalho",
    "data_de_nascimento",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg_rnm",
    "nome_do_banco",
    "numero_da_agencia",
    "numero_da_conta",
)
OPCIONAIS = {"link_do_evento", "complemento"}
EXCLUSIVOS_DE_ALUNOS = {"nivel", "tipo_de_auxilio"}
CPF_FORMATO = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
CEP_FORMATO = re.compile(r"\d{5}-\d{3}")
DATA_FORMATO = re.compile(r"\d{2}/\d{2}/\d{4}")


def so_digitos(texto):
    return all("0" <= caractere <= "9" for caractere in texto)


def email_valido(email):
    partes = email.split("@")
    return len(partes) == 2 and partes[0] != "" and partes[1] != ""


def cpf_valido(cpf):
    numeros = cpf.replace(".", "").replace("-", "")
    primeiro = sum(int(digito) * peso for digito, peso in zip(numeros[:9], range(10, 1, -1)))
    segundo = sum(int(digito) * peso for digito, peso in zip(numeros[:10], range(11, 1, -1)))
    digito1 = primeiro * 10 % 11 % 10
    digito2 = segundo * 10 % 11 % 10
    return numeros[9] == str(digito1) and numeros[10] == str(digito2)


def data_existente(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def formatar_moeda(digitos):
    reais, centavos = divmod(int(digitos), 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def validar(dados):
    erros = []
    if dados["aba"] == "docentes":
        obrigatorios = [
            campo
            for campo in CAMPOS
            if campo not in OPCIONAIS and campo not in EXCLUSIVOS_DE_ALUNOS
        ]
    else:
        obrigatorios = [campo for campo in CAMPOS if campo not in OPCIONAIS]
    if any(not dados[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if dados["n_usp"] and not so_digitos(dados["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if dados["numero_da_agencia"] and not so_digitos(dados["numero_da_agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if dados["valor_solicitado"] and not (
        so_digitos(dados["valor_solicitado"]) and int(dados["valor_solicitado"]) > 0
    ):
        erros.append("Valor solicitado deve ser maior que 0")
    if dados["email"] and not email_valido(dados["email"]):
        erros.append("E-mail inválido")
    if dados["cpf"]:
        if not CPF_FORMATO.fullmatch(dados["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(dados["cpf"]):
            erros.append("CPF inválido")
    if dados["cep"] and not CEP_FORMATO.fullmatch(dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if dados["data_de_nascimento"]:
        if not DATA_FORMATO.fullmatch(dados["data_de_nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_existente(dados["data_de_nascimento"]):
            erros.append("Data de nascimento inválida")
    return erros


def redigir(dados):
    if dados["aba"] == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_de_auxilio']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"
    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        (
            f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de "
            "auxílio financeiro para a interessada(o) acima, conforme segue:"
        ),
        "",
        "Dados do evento",
        f"Evento: {dados['nome_do_evento']}",
        f"Período: {dados['periodo_do_evento']}",
        f"Local: {dados['cidade_do_evento']} - {dados['estado_do_evento']} - {dados['pais_do_evento']}",
    ]
    if dados["link_do_evento"]:
        linhas.append(f"Link do evento: {dados['link_do_evento']}")
    linhas.extend(
        [
            f"Apresentação de trabalho: {dados['ira_apresentar_trabalho']}",
            f"Valor solicitado: {formatar_moeda(dados['valor_solicitado'])}",
            f"Detalhamento: {dados['detalhamento_do_pedido']}",
            "",
            "Endereço da(o) interessada(o)",
            f"{dados['logradouro']}, {dados['numero']}",
        ]
    )
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas.extend(
        [
            f"CEP: {dados['cep']}",
            f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
            "",
            "Dados para pagamento",
            f"Data de nascimento: {dados['data_de_nascimento']}",
            f"CPF: {dados['cpf']}",
            f"RG / RNM: {dados['rg_rnm']}",
            f"Banco: {dados['nome_do_banco']}",
            f"Agência: {dados['numero_da_agencia']}",
            f"Conta: {dados['numero_da_conta']}",
            "",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ]
    )
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(entrada: Request):
    formulario = await entrada.form()
    dados = {campo: str(formulario.get(campo, "") or "") for campo in CAMPOS}
    erros = validar(dados)
    if erros:
        return PlainTextResponse("\n".join(erros), status_code=400)
    return PlainTextResponse(redigir(dados))
