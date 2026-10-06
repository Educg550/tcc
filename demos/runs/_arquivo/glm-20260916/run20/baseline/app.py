import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent


class Solicitacao(BaseModel):
    aba: str = "alunos"
    nome: str = ""
    nusp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    evento: str = ""
    periodo: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor: str = ""
    detalhamento: str = ""
    apresentacao: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg_rnm: str = ""
    nome_banco: str = ""
    agencia: str = ""
    conta: str = ""


app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


@app.post("/solicitar")
def solicitar(dados: Solicitacao):
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados)}


def validar(s: Solicitacao) -> list[str]:
    erros: list[str] = []
    obrigatorios = [
        s.nome, s.nusp, s.programa, s.email, s.evento, s.periodo,
        s.cidade_evento, s.estado_evento, s.pais_evento, s.valor,
        s.detalhamento, s.apresentacao, s.data_nascimento, s.logradouro,
        s.numero, s.bairro, s.cep, s.cidade, s.estado, s.cpf, s.rg_rnm,
        s.nome_banco, s.agencia, s.conta,
    ]
    if s.aba == "alunos":
        obrigatorios.extend([s.nivel, s.tipo_auxilio])
    if any(campo.strip() == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.nusp and not s.nusp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if s.agencia and not s.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if s.valor:
        centavos = re.sub(r"\D", "", s.valor)
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if s.email:
        usuario, _, dominio = s.email.partition("@")
        if not usuario or not dominio:
            erros.append("E-mail inválido")

    cpf_no_formato = True
    if s.cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", s.cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
        cpf_no_formato = False
    if s.cep and not re.fullmatch(r"\d{5}-\d{3}", s.cep):
        erros.append("CEP deve estar no formato 00000-000")
    data_no_formato = True
    if s.data_nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s.data_nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        data_no_formato = False

    if s.cpf and cpf_no_formato and not cpf_valido(s.cpf):
        erros.append("CPF inválido")
    if s.data_nascimento and data_no_formato:
        try:
            datetime.strptime(s.data_nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


def cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    resto = sum(d * p for d, p in zip(digitos[:9], range(10, 1, -1))) % 11
    dv1 = 0 if resto < 2 else 11 - resto
    resto = sum(d * p for d, p in zip(digitos[:10], range(11, 1, -1))) % 11
    dv2 = 0 if resto < 2 else 11 - resto
    return digitos[9] == dv1 and digitos[10] == dv2


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r"\D", "", valor))
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def gerar_oficio(s: Solicitacao) -> str:
    if s.aba == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}"
        programa = f"Programa: {s.programa} - {s.nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {s.programa}"
    linhas = [
        f"Interessada(o): {s.nome} - {s.nusp}",
        f"E-mail: {s.email}",
        assunto,
        programa,
        "",
        f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {s.evento}",
        f"Período: {s.periodo}",
        f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}",
    ]
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.extend([
        f"Apresentação de trabalho: {s.apresentacao}",
        f"Valor solicitado: {formatar_moeda(s.valor)}",
        f"Detalhamento: {s.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{s.logradouro}, {s.numero}",
    ])
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas.extend([
        f"CEP: {s.cep}",
        f"{s.bairro}, {s.cidade} - {s.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {s.data_nascimento}",
        f"CPF: {s.cpf}",
        f"RG / RNM: {s.rg_rnm}",
        f"Banco: {s.nome_banco}",
        f"Agência: {s.agencia}",
        f"Conta: {s.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.get("/")
def index():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
