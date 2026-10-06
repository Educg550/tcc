import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


class Solicitacao(BaseModel):
    NOME_COMPLETO: str = ""
    NUSP: str = ""
    PROGRAMA: str = ""
    NIVEL: str = ""
    TIPO_AUXILIO: str = ""
    EMAIL: str = ""
    NOME_EVENTO: str = ""
    PERIODO_EVENTO: str = ""
    CIDADE_EVENTO: str = ""
    ESTADO_EVENTO: str = ""
    PAIS_EVENTO: str = ""
    LINK_EVENTO: str = ""
    VALOR_SOLICITADO: str = ""
    DETALHAMENTO: str = ""
    APRESENTA_TRABALHO: str = ""
    DATA_NASCIMENTO: str = ""
    LOGRADOURO: str = ""
    NUMERO: str = ""
    COMPLEMENTO: str = ""
    BAIRRO: str = ""
    CEP: str = ""
    CIDADE: str = ""
    ESTADO: str = ""
    CPF: str = ""
    RG: str = ""
    BANCO: str = ""
    AGENCIA: str = ""
    CONTA: str = ""


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CAMPOS_OBRIGATORIOS = {
    "NOME_COMPLETO": "NOME COMPLETO - SEM ABREVIAR",
    "NUSP": "N. USP",
    "PROGRAMA": "PROGRAMA",
    "EMAIL": "E-MAIL",
    "NOME_EVENTO": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERIODO_EVENTO": "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE_EVENTO": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO_EVENTO": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAIS_EVENTO": "PAÍS DO EVENTO, EXAME OU DEFESA",
    "VALOR_SOLICITADO": "VALOR SOLICITADO (R$)",
    "DETALHAMENTO": "DETALHAMENTO DO PEDIDO",
    "APRESENTA_TRABALHO": "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA_NASCIMENTO": "DATA DE NASCIMENTO",
    "LOGRADOURO": "LOGRADOURO",
    "NUMERO": "NÚMERO",
    "BAIRRO": "BAIRRO",
    "CEP": "CEP",
    "CIDADE": "CIDADE",
    "ESTADO": "ESTADO",
    "CPF": "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG": "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "BANCO": "NOME DO BANCO",
    "AGENCIA": "NÚMERO DA AGÊNCIA",
    "CONTA": "NÚMERO DA CONTA",
}


def cpf_valido(cpf):
    digitos = [int(c) for c in cpf]
    soma = sum(digitos[i] * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    if d1 == 10:
        d1 = 0
    if d1 != digitos[9]:
        return False
    soma = sum(digitos[i] * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    if d2 == 10:
        d2 = 0
    return d2 == digitos[10]


def data_valida(data):
    dia, mes, ano = int(data[0:2]), int(data[3:5]), int(data[6:10])
    if mes < 1 or mes > 12:
        return False
    dias_mes = [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if mes == 2:
        bissexto = ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)
        max_dia = 29 if bissexto else 28
    else:
        max_dia = dias_mes[mes - 1]
    return 1 <= dia <= max_dia


def formatar_valor(valor):
    digitos = re.sub(r"\D", "", valor)
    if not digitos:
        return valor
    centavos = int(digitos)
    inteiro = centavos // 100
    fracao = centavos % 100
    milhar = f"{inteiro:,}".replace(",", ".")
    return f"R$ {milhar},{fracao:02d}"


def validar(s, aba):
    erros = []
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "ALUNOS":
        obrigatorios += ["NIVEL", "TIPO_AUXILIO"]
    faltando = [c for c in obrigatorios if not getattr(s, c).strip()]
    if faltando:
        erros.append("Preencha todos os campos")
    if s.NUSP and not s.NUSP.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.AGENCIA and not s.AGENCIA.isdigit():
        erros.append("Número da agência deve conter apenas números")
    digitos = re.sub(r"\D", "", s.VALOR_SOLICITADO)
    if digitos:
        if int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if s.EMAIL and "@" in s.EMAIL:
        local, _, dominio = s.EMAIL.rpartition("@")
        if not local or "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
            erros.append("E-mail inválido")
    elif s.EMAIL:
        erros.append("E-mail inválido")
    m_cpf = re.fullmatch(r"(\d{3})\.(\d{3})\.(\d{3})-(\d{2})", s.CPF)
    if m_cpf:
        if not cpf_valido(s.CPF.replace(".", "").replace("-", "")):
            erros.append("CPF inválido")
    elif s.CPF:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if s.CEP and not re.fullmatch(r"\d{5}-\d{3}", s.CEP):
        erros.append("CEP deve estar no formato 00000-000")
    m_data = re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.DATA_NASCIMENTO)
    if m_data:
        if not data_valida(s.DATA_NASCIMENTO):
            erros.append("Data de nascimento inválida")
    elif s.DATA_NASCIMENTO:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    return erros


def linha(rotulo, valor):
    return f"{rotulo}: {valor}\n"


def gerar_oficio(s, aba):
    if aba == "DOCENTES":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
    else:
        assunto = "Solicitação de Auxílio Financeiro - " + s.TIPO_AUXILIO
    if aba == "DOCENTES":
        programa = "Programa: " + s.PROGRAMA
    else:
        programa = "Programa: " + s.PROGRAMA + " - " + s.NIVEL

    linhas = [
        "Interessada(o): " + s.NOME_COMPLETO + " - " + s.NUSP,
        "E-mail: " + s.EMAIL,
        "Assunto: " + assunto,
        programa,
        "",
        "A CCP-" + s.PROGRAMA + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        "Evento: " + s.NOME_EVENTO,
        "Período: " + s.PERIODO_EVENTO,
        "Local: " + s.CIDADE_EVENTO + " - " + s.ESTADO_EVENTO + " - " + s.PAIS_EVENTO,
    ]
    if s.LINK_EVENTO.strip():
        linhas.append("Link do evento: " + s.LINK_EVENTO)
    linhas += [
        "Apresentação de trabalho: " + s.APRESENTA_TRABALHO,
        "Valor solicitado: " + formatar_valor(s.VALOR_SOLICITADO),
        "Detalhamento: " + s.DETALHAMENTO,
        "",
        "Endereço da(o) interessada(o)",
        s.LOGRADOURO + ", " + s.NUMERO,
    ]
    if s.COMPLEMENTO.strip():
        linhas.append("Complemento: " + s.COMPLEMENTO)
    linhas += [
        "CEP: " + s.CEP,
        s.BAIRRO + ", " + s.CIDADE + " - " + s.ESTADO,
        "",
        "Dados para pagamento",
        "Data de nascimento: " + s.DATA_NASCIMENTO,
        "CPF: " + s.CPF,
        "RG / RNM: " + s.RG,
        "Banco: " + s.BANCO,
        "Agência: " + s.AGENCIA,
        "Conta: " + s.CONTA,
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitacao(s: Solicitacao, aba: str = "ALUNOS"):
    erros = validar(s, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(s, aba)}


@app.get("/")
def index():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory=".", html=True), name="static")
