import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent

app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
    dados: dict[str, str]


CAMPOS_COMUNS = [
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


def campo(dados: dict[str, str], rotulo: str) -> str:
    return dados.get(rotulo, "").strip()


def valor_e_positivo(texto: str) -> bool:
    numeros = re.sub(r"[^0-9,]", "", texto).replace(".", "").replace(",", ".")
    try:
        return float(numeros) > 0
    except ValueError:
        return False


def email_valido(texto: str) -> bool:
    partes = texto.split("@")
    return len(partes) == 2 and bool(partes[0]) and bool(partes[1])


def cpf_valido(texto: str) -> bool:
    digitos = [int(d) for d in re.sub(r"[^0-9]", "", texto)]
    for etapa in (9, 10):
        soma = sum(d * (etapa + 1 - i) for i, d in enumerate(digitos[:etapa]))
        if digitos[etapa] != (soma * 10) % 11 % 10:
            return False
    return True


def data_valida(texto: str) -> bool:
    try:
        datetime.date(int(texto[6:10]), int(texto[3:5]), int(texto[0:2]))
    except ValueError:
        return False
    return True


def montar_oficio(aba: str, d: dict[str, str]) -> str:
    if aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {d['TIPO DE AUXÍLIO']}"
        programa = f"Programa: {d['PROGRAMA']} - {d['NÍVEL']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {d['PROGRAMA']}"
    linhas = [
        f"Interessada(o): {d['NOME COMPLETO - SEM ABREVIAR']} - {d['N. USP']}",
        f"E-mail: {d['E-MAIL']}",
        assunto,
        programa,
        "",
        f"A CCP-{d['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {d['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {d['CIDADE DO EVENTO, EXAME OU DEFESA']} - {d['ESTADO DO EVENTO, EXAME OU DEFESA']} - {d['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]
    if d["LINK DO EVENTO, EXAME OU DEFESA"]:
        linhas.append(f"Link do evento: {d['LINK DO EVENTO, EXAME OU DEFESA']}")
    linhas += [
        f"Apresentação de trabalho: {d['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {d['VALOR SOLICITADO (R$)']}",
        f"Detalhamento: {d['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d['LOGRADOURO']}, {d['NÚMERO']}",
    ]
    if d["COMPLEMENTO"]:
        linhas.append(f"Complemento: {d['COMPLEMENTO']}")
    linhas += [
        f"CEP: {d['CEP']}",
        f"{d['BAIRRO']}, {d['CIDADE']} - {d['ESTADO']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d['DATA DE NASCIMENTO']}",
        f"CPF: {d['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"RG / RNM: {d['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"Banco: {d['NOME DO BANCO']}",
        f"Agência: {d['NÚMERO DA AGÊNCIA']}",
        f"Conta: {d['NÚMERO DA CONTA']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    dados = solicitacao.dados
    obrigatorios = set(CAMPOS_COMUNS)
    if solicitacao.aba == "alunos":
        obrigatorios |= {"NÍVEL", "TIPO DE AUXÍLIO"}
    erros = []
    if any(not campo(dados, rotulo) for rotulo in obrigatorios):
        erros.append("Preencha todos os campos")
    n_usp = campo(dados, "N. USP")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")
    agencia = campo(dados, "NÚMERO DA AGÊNCIA")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")
    valor = campo(dados, "VALOR SOLICITADO (R$)")
    if valor and not valor_e_positivo(valor):
        erros.append("Valor solicitado deve ser maior que 0")
    email = campo(dados, "E-MAIL")
    if email and not email_valido(email):
        erros.append("E-mail inválido")
    cpf = campo(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf and not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")
    cep = campo(dados, "CEP")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = campo(dados, "DATA DE NASCIMENTO")
    if nascimento and not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")
    resposta = {"erros": erros}
    if not erros:
        resposta["oficio"] = montar_oficio(
            solicitacao.aba,
            {rotulo: campo(dados, rotulo) for rotulo in CAMPOS_COMUNS + ["NÍVEL", "TIPO DE AUXÍLIO"]},
        )
    return resposta


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
