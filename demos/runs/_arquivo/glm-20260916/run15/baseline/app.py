import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

app = FastAPI(title="Auxílio Financeiro — Pós-Graduação IME-USP")

CAMPOS_SOLICITANTE = {
    "alunos": [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "NÍVEL",
        "TIPO DE AUXÍLIO",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    ],
    "docentes": [
        "NOME COMPLETO - SEM ABREVIAR",
        "N. USP",
        "PROGRAMA",
        "E-MAIL",
        "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
        "PERÍODO DO EVENTO, EXAME OU DEFESA",
        "CIDADE DO EVENTO, EXAME OU DEFESA",
        "ESTADO DO EVENTO, EXAME OU DEFESA",
        "PAÍS DO EVENTO, EXAME OU DEFESA",
        "LINK DO EVENTO, EXAME OU DEFESA",
        "VALOR SOLICITADO (R$)",
        "DETALHAMENTO DO PEDIDO",
        "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    ],
}
CAMPOS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]
CAMPOS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]
OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}


def email_valido(email):
    local, arroba, dominio = email.partition("@")
    return bool(arroba and local and dominio)


def cpf_com_verificadores_conferentes(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    digito1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    digito2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return digito1 == digitos[9] and digito2 == digitos[10]


def data_existe(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def validar(aba, campos):
    obrigatorios = CAMPOS_SOLICITANTE[aba] + CAMPOS_ENDERECO + CAMPOS_PAGAMENTO
    valores = {campo: (campos.get(campo) or "").strip() for campo in obrigatorios}
    erros = []
    if any(not valores[campo] for campo in obrigatorios if campo not in OPCIONAIS):
        erros.append("Preencha todos os campos")
    if valores["N. USP"] and not re.fullmatch(r"[0-9]+", valores["N. USP"]):
        erros.append("N. USP deve conter apenas números")
    agencia = valores["NÚMERO DA AGÊNCIA"]
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")
    valor = valores["VALOR SOLICITADO (R$)"]
    if valor and not (re.fullmatch(r"[0-9]+", valor) and int(valor) > 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if valores["E-MAIL"] and not email_valido(valores["E-MAIL"]):
        erros.append("E-mail inválido")
    cpf = valores["CPF (SEPARADOS POR PONTOS E TRAÇO)"]
    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if valores["CEP"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", valores["CEP"]):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = valores["DATA DE NASCIMENTO"]
    data_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento))
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_no_formato and not cpf_com_verificadores_conferentes(cpf):
        erros.append("CPF inválido")
    if data_no_formato and not data_existe(nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def formatar_moeda(centavos):
    inteiro, resto = divmod(int(centavos), 100)
    return "R$ " + f"{inteiro:,}".replace(",", ".") + f",{resto:02d}"


def gerar_oficio(aba, campos):
    def campo(nome):
        return (campos.get(nome) or "").strip()

    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {campo('TIPO DE AUXÍLIO')}"
        programa = f"{campo('PROGRAMA')} - {campo('NÍVEL')}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = campo("PROGRAMA")

    linhas = [
        f"Interessada(o): {campo('NOME COMPLETO - SEM ABREVIAR')} - {campo('N. USP')}",
        f"E-mail: {campo('E-MAIL')}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{campo('PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campo('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {campo('PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {campo('CIDADE DO EVENTO, EXAME OU DEFESA')} - {campo('ESTADO DO EVENTO, EXAME OU DEFESA')} - {campo('PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ]
    if campo("LINK DO EVENTO, EXAME OU DEFESA"):
        linhas.append(f"Link do evento: {campo('LINK DO EVENTO, EXAME OU DEFESA')}")
    linhas += [
        f"Apresentação de trabalho: {campo('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {formatar_moeda(campo('VALOR SOLICITADO (R$)'))}",
        f"Detalhamento: {campo('DETALHAMENTO DO PEDIDO')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('LOGRADOURO')}, {campo('NÚMERO')}",
    ]
    if campo("COMPLEMENTO"):
        linhas.append(f"Complemento: {campo('COMPLEMENTO')}")
    linhas += [
        f"CEP: {campo('CEP')}",
        f"{campo('BAIRRO')}, {campo('CIDADE')} - {campo('ESTADO')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {campo('DATA DE NASCIMENTO')}",
        f"CPF: {campo('CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"RG / RNM: {campo('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
        f"Banco: {campo('NOME DO BANCO')}",
        f"Agência: {campo('NÚMERO DA AGÊNCIA')}",
        f"Conta: {campo('NÚMERO DA CONTA')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(dados: dict):
    aba = dados.get("aba")
    if aba not in CAMPOS_SOLICITANTE:
        return JSONResponse(status_code=400, content={"valido": False, "erros": ["Aba desconhecida"]})
    campos = {
        str(chave): ("" if valor is None else str(valor))
        for chave, valor in (dados.get("campos") or {}).items()
    }
    erros = validar(aba, campos)
    if erros:
        return {"valido": False, "erros": erros}
    return {"valido": True, "oficio": gerar_oficio(aba, campos)}


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
def javascript():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
