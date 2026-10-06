"""Backend da solicitação de auxílio financeiro da Pós-Graduação do IME-USP."""
import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

FORMATO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
FORMATO_CEP = re.compile(r"\d{5}-\d{3}")
FORMATO_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")

OBRIGATORIOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

SO_ALUNOS = ["NÍVEL", "TIPO DE AUXÍLIO"]


def centavos(texto):
    digitos = "".join(caractere for caractere in texto if caractere.isdigit())
    return int(digitos) if digitos else 0


def digitos_cpf_conferem(cpf):
    numeros = [int(caractere) for caractere in cpf if caractere.isdigit()]
    for quantidade in (9, 10):
        pesos = range(quantidade + 1, 1, -1)
        soma = sum(numero * peso for numero, peso in zip(numeros[:quantidade], pesos))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != numeros[quantidade]:
            return False
    return True


def data_existente(texto):
    try:
        date(int(texto[6:10]), int(texto[3:5]), int(texto[0:2]))
    except ValueError:
        return False
    return True


def validar(campos, aba):
    erros = []
    obrigatorios = OBRIGATORIOS + (SO_ALUNOS if aba == "alunos" else [])
    if any(not campos.get(rotulo, "").strip() for rotulo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campos.get("N. USP", "")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("NÚMERO DA AGÊNCIA", "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("VALOR SOLICITADO (R$)", "")
    if valor and (re.search(r"[^\dR$., ]", valor) or centavos(valor) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("E-MAIL", "")
    if email and not FORMATO_EMAIL.fullmatch(email):
        erros.append("E-mail inválido")

    cpf = campos.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "")
    cpf_no_formato = FORMATO_CPF.fullmatch(cpf) is not None
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = campos.get("CEP", "")
    if cep and not FORMATO_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campos.get("DATA DE NASCIMENTO", "")
    data_no_formato = FORMATO_DATA.fullmatch(nascimento) is not None
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not digitos_cpf_conferem(cpf):
        erros.append("CPF inválido")

    if data_no_formato and not data_existente(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def formatar_moeda(valor):
    reais, resto = divmod(centavos(valor), 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def gerar_oficio(campos, aba):
    if aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {campos['PROGRAMA']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {campos['TIPO DE AUXÍLIO']}"
        programa = f"Programa: {campos['PROGRAMA']} - {campos['NÍVEL']}"
    linhas = [
        f"Interessada(o): {campos['NOME COMPLETO - SEM ABREVIAR']} - {campos['N. USP']}",
        f"E-mail: {campos['E-MAIL']}",
        assunto,
        programa,
        "",
        f"A CCP-{campos['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campos['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {campos['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {campos['CIDADE DO EVENTO, EXAME OU DEFESA']} - {campos['ESTADO DO EVENTO, EXAME OU DEFESA']} - {campos['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]
    if campos.get("LINK DO EVENTO, EXAME OU DEFESA", "").strip():
        linhas.append(f"Link do evento: {campos['LINK DO EVENTO, EXAME OU DEFESA']}")
    linhas += [
        f"Apresentação de trabalho: {campos['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {formatar_moeda(campos['VALOR SOLICITADO (R$)'])}",
        f"Detalhamento: {campos['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campos['LOGRADOURO']}, {campos['NÚMERO']}",
    ]
    if campos.get("COMPLEMENTO", "").strip():
        linhas.append(f"Complemento: {campos['COMPLEMENTO']}")
    linhas += [
        f"CEP: {campos['CEP']}",
        f"{campos['BAIRRO']}, {campos['CIDADE']} - {campos['ESTADO']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {campos['DATA DE NASCIMENTO']}",
        f"CPF: {campos['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"RG / RNM: {campos['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"Banco: {campos['NOME DO BANCO']}",
        f"Agência: {campos['NÚMERO DA AGÊNCIA']}",
        f"Conta: {campos['NÚMERO DA CONTA']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


app = FastAPI()


@app.post("/api/solicitar")
def solicitar(requisicao: dict):
    aba = "docentes" if requisicao.get("aba") == "docentes" else "alunos"
    campos = requisicao.get("campos", {})
    erros = validar(campos, aba)
    if erros:
        return {"erros": erros}
    return {"erros": [], "oficio": gerar_oficio(campos, aba)}


@app.get("/")
def raiz():
    return FileResponse(RAIZ / "index.html")


@app.get("/index.html")
def indice():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def roteiro():
    return FileResponse(RAIZ / "app.js", media_type="application/javascript")


if (RAIZ / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
