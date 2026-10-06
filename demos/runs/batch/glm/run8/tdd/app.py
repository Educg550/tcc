import datetime
import io
import os
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade", "estado", "pais", "valor", "detalhamento", "apresentacao",
    "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade_endereco", "estado_endereco", "cpf", "rg", "banco",
    "agencia", "conta",
]

CAMPOS_ALUNOS = ["nivel", "tipo_auxilio"]

ERRO_CAMPOS = "Preencha todos os campos"
ERRO_N_USP = "N. USP deve conter apenas números"
ERRO_AGENCIA = "Número da agência deve conter apenas números"
ERRO_VALOR = "Valor solicitado deve ser maior que 0"
ERRO_EMAIL = "E-mail inválido"
ERRO_CPF_FORMATO = "CPF deve estar no formato 000.000.000-00"
ERRO_CEP = "CEP deve estar no formato 00000-000"
ERRO_CPF = "CPF inválido"
ERRO_DATA_FORMATO = "Data de nascimento deve estar no formato dd/mm/aaaa"
ERRO_DATA = "Data de nascimento inválida"


class Solicitacao(BaseModel):
    aba: str = ""
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade: str = ""
    estado: str = ""
    pais: str = ""
    link: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade_endereco: str = ""
    estado_endereco: str = ""
    cpf: str = ""
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


def email_valido(email):
    if "@" not in email:
        return False
    usuario, dominio = email.split("@", 1)
    if not usuario or not dominio or "." not in dominio.split(".")[-1]:
        return False
    return True


def formatar_moeda(digitos):
    d = re.sub(r"\D", "", digitos)
    if not d:
        return ""
    centavos = int(d)
    reais, cent = divmod(centavos, 100)
    return f"R$ {reais:,d}.{cent:02d}".replace(",", ".")


def valor_valido(valor):
    return bool(re.fullmatch(r"[0-9]+", valor)) and int(valor) > 0


def cpf_formato_valido(cpf):
    return bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))


def cpf_verificadores_validos(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    pesos = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = sum(int(d) * p for d, p in zip(digitos[:9], pesos))
    d1 = (d1 * 10) % 11 % 10
    pesos2 = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    d2 = sum(int(d) * p for d, p in zip(digitos[:10], pesos2))
    d2 = (d2 * 10) % 11 % 10
    return int(digitos[9]) == d1 and int(digitos[10]) == d2


def data_formato_valido(data):
    return bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", data))


def data_valida(data):
    try:
        dia, mes, ano = map(int, data.split("/"))
        datetime.date(ano, mes, dia)
    except ValueError:
        return False
    return True


def validar(s):
    erros = []
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if s.aba == "alunos":
        obrigatorios += CAMPOS_ALUNOS
    if any(getattr(s, c).strip() == "" for c in obrigatorios):
        erros.append(ERRO_CAMPOS)
    if s.n_usp and not re.fullmatch(r"\d+", s.n_usp.strip()):
        erros.append(ERRO_N_USP)
    if s.agencia and not re.fullmatch(r"\d+", s.agencia.strip()):
        erros.append(ERRO_AGENCIA)
    if s.valor and not valor_valido(s.valor.strip()):
        erros.append(ERRO_VALOR)
    if s.email and not email_valido(s.email.strip()):
        erros.append(ERRO_EMAIL)
    if s.cpf and not cpf_formato_valido(s.cpf.strip()):
        erros.append(ERRO_CPF_FORMATO)
    elif s.cpf and not cpf_verificadores_validos(s.cpf.strip()):
        erros.append(ERRO_CPF)
    if s.cep and not re.fullmatch(r"\d{5}-\d{3}", s.cep.strip()):
        erros.append(ERRO_CEP)
    if s.nascimento:
        if not data_formato_valido(s.nascimento.strip()):
            erros.append(ERRO_DATA_FORMATO)
        elif not data_valida(s.nascimento.strip()):
            erros.append(ERRO_DATA)
    return erros


def gerar_oficio(s, valor_formatado):
    linhas = []
    linhas.append(f"Interessada(o): {s.nome} - {s.n_usp}")
    linhas.append(f"E-mail: {s.email}")
    if s.aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    linhas.append("")
    linhas.append(
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.evento}")
    linhas.append(f"Período: {s.periodo}")
    linhas.append(f"Local: {s.cidade} - {s.estado} - {s.pais}")
    if s.link:
        linhas.append(f"Link do evento: {s.link}")
    linhas.append(f"Apresentação de trabalho: {s.apresentacao}")
    linhas.append(f"Valor solicitado: {valor_formatado}")
    linhas.append(f"Detalhamento: {s.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.logradouro}, {s.numero}")
    if s.complemento:
        linhas.append(f"Complemento: {s.complemento}")
    linhas.append(f"CEP: {s.cep}")
    linhas.append(f"{s.bairro}, {s.cidade_endereco} - {s.estado_endereco}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.nascimento}")
    linhas.append(f"CPF: {s.cpf}")
    linhas.append(f"RG / RNM: {s.rg}")
    linhas.append(f"Banco: {s.banco}")
    linhas.append(f"Agência: {s.agencia}")
    linhas.append(f"Conta: {s.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


def limpar(s, erros):
    if ERRO_CAMPOS in erros or ERRO_EMAIL in erros:
        s.email = ""
    if ERRO_CAMPOS in erros:
        s.n_usp = ""
        s.programa = ""
        s.evento = ""
        s.periodo = ""
        s.cidade = ""
        s.estado = ""
        s.pais = ""
        s.detalhamento = ""
        s.apresentacao = ""
        s.logradouro = ""
        s.numero = ""
        s.bairro = ""
        s.cidade_endereco = ""
        s.estado_endereco = ""
        s.rg = ""
        s.banco = ""
        s.conta = ""
    if ERRO_VALOR in erros:
        s.valor = ""
    if ERRO_CPF_FORMATO in erros or ERRO_CPF in erros:
        s.cpf = ""
    if ERRO_CEP in erros:
        s.cep = ""
    if ERRO_DATA_FORMATO in erros or ERRO_DATA in erros:
        s.nascimento = ""
    if s.aba == "alunos" and ERRO_CAMPOS in erros:
        s.nivel = ""
        s.tipo_auxilio = ""


@app.get("/")
def index():
    return FileResponse("index.html")


@app.get("/style.css")
def css():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def js():
    return FileResponse("app.js", media_type="text/javascript")


@app.post("/solicitar")
def solicitar(solicitacao: Solicitacao):
    s = solicitacao
    erros = validar(s)
    valor_formatado = formatar_moeda(s.valor) if valor_valido(s.valor) and int(s.valor) > 0 else ""
    if erros:
        limpar(s, erros)
        return {"valido": False, "erros": erros, "aba": s.aba, "dados": s.model_dump()}
    oficio = gerar_oficio(s, valor_formatado)
    return {"valido": True, "erros": [], "aba": s.aba, "oficio": oficio, "dados": s.model_dump()}
