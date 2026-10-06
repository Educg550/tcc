import datetime
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS = [
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
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
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

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}
SOMENTE_ALUNOS = {"NÍVEL", "TIPO DE AUXÍLIO"}


@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse("app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.post("/solicitacao")
def solicitacao(requisicao: dict):
    aba = str(requisicao.get("aba", "ALUNOS")).upper()
    dados = {campo: str(requisicao.get("dados", requisicao).get(campo) or "") for campo in CAMPOS}
    erros = validar(aba, dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(aba, dados)}


def validar(aba, dados):
    erros = []
    obrigatorios = [
        campo
        for campo in CAMPOS
        if campo not in OPCIONAIS and (aba != "DOCENTES" or campo not in SOMENTE_ALUNOS)
    ]
    if any(not dados[campo].strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados["N. USP"].strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados["NÚMERO DA AGÊNCIA"].strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    if dados["VALOR SOLICITADO (R$)"].strip() and centavos(dados["VALOR SOLICITADO (R$)"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados["E-MAIL"].strip()
    if email:
        partes = email.split("@")
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append("E-mail inválido")

    cpf = dados["CPF (SEPARADOS POR PONTOS E TRAÇO)"].strip()
    if cpf:
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            if not cpf_valido(cpf):
                erros.append("CPF inválido")
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")

    cep = dados["CEP"].strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados["DATA DE NASCIMENTO"].strip()
    if nascimento:
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            try:
                datetime.date(int(nascimento[6:]), int(nascimento[3:5]), int(nascimento[:2]))
            except ValueError:
                erros.append("Data de nascimento inválida")
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    return erros


def gerar_oficio(aba, dados):
    def campo(nome):
        return dados[nome].strip()

    linhas = [
        f"Interessada(o): {campo('NOME COMPLETO - SEM ABREVIAR')} - {campo('N. USP')}",
        f"E-mail: {campo('E-MAIL')}",
    ]
    if aba == "DOCENTES":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {campo('PROGRAMA')}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {campo('TIPO DE AUXÍLIO')}")
        linhas.append(f"Programa: {campo('PROGRAMA')} - {campo('NÍVEL')}")
    linhas.extend([
        "",
        f"A CCP-{campo('PROGRAMA')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campo('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {campo('PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        f"Local: {campo('CIDADE DO EVENTO, EXAME OU DEFESA')} - {campo('ESTADO DO EVENTO, EXAME OU DEFESA')} - {campo('PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ])
    link = campo("LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas.extend([
        f"Apresentação de trabalho: {campo('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
        f"Valor solicitado: {formatar_moeda(campo('VALOR SOLICITADO (R$)'))}",
        f"Detalhamento: {campo('DETALHAMENTO DO PEDIDO')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('LOGRADOURO')}, {campo('NÚMERO')}",
    ])
    complemento = campo("COMPLEMENTO")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.extend([
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
    ])
    return "\n".join(linhas)


def centavos(texto):
    digitos = re.sub(r"\D", "", texto)
    return int(digitos) if digitos else 0


def formatar_moeda(texto):
    numero = f"{centavos(texto) / 100:,.2f}"
    return "R$ " + numero.replace(",", "@").replace(".", ",").replace("@", ".")


def cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        return False
    return int(digitos[9]) == digito(digitos[:9], 10) and int(digitos[10]) == digito(digitos[:10], 11)


def digito(parte, peso_inicial):
    soma = sum(int(caractere) * peso for caractere, peso in zip(parte, range(peso_inicial, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto
