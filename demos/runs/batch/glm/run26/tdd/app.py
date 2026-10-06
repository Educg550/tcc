from datetime import date
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()


class Solicitacao(BaseModel):
    nome: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
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
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""
    aba: str = "alunos"


CAMPOS_OBRIGATORIOS_COMUNS = (
    "nome", "n_usp", "programa", "email", "nome_evento", "periodo_evento",
    "cidade_evento", "estado_evento", "pais_evento", "valor_solicitado",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro", "numero",
    "bairro", "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
)

CAMPOS_OBRIGATORIOS_ALUNOS = CAMPOS_OBRIGATORIOS_COMUNS + ("nivel", "tipo_auxilio")


def formatar_moeda(digitos):
    digitos = re.sub(r"\D", "", digitos or "")
    if not digitos:
        return "R$ 0,00"
    centavos = int(digitos)
    reais, cent = divmod(centavos, 100)
    texto = f"{reais:,}".replace(",", ".")
    return f"R$ {texto},{cent:02d}"


def cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    soma = sum(int(d) * peso for d, peso in zip(digitos[:9], range(10, 1, -1)))
    d1 = (soma * 10) % 11 % 10
    soma = sum(int(d) * peso for d, peso in zip(digitos[:10], range(11, 1, -1)))
    d2 = (soma * 10) % 11 % 10
    return digitos[9] == str(d1) and digitos[10] == str(d2)


def data_existe(data):
    dia, mes, ano = (int(p) for p in data.split("/"))
    try:
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def validar(d):
    erros = []
    aba = d.aba
    if aba not in ("alunos", "docentes"):
        return ["Aba inválida"]

    campos = CAMPOS_OBRIGATORIOS_ALUNOS if aba == "alunos" else CAMPOS_OBRIGATORIOS_COMUNS
    if any(not getattr(d, c).strip() for c in campos):
        erros.append("Preencha todos os campos")

    if d.n_usp and not d.n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if d.agencia and not d.agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = re.sub(r"\D", "", d.valor_solicitado)
    if valor and (not valor.isdigit() or int(valor) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = d.email.strip()
    if email and ("@" not in email or not email.split("@")[-1].strip()):
        erros.append("E-mail inválido")

    cpf = d.cpf.strip()
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = d.cep.strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = d.data_nascimento.strip()
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_existe(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d):
    if d.aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {d.programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {d.tipo_auxilio}"
        programa = f"Programa: {d.programa} - {d.nivel}"

    linhas = [
        f"Interessada(o): {d.nome} - {d.n_usp}",
        f"E-mail: {d.email}",
        f"Assunto: {assunto}",
        programa,
        "",
        "A CCP-" + d.programa + " aprovou na data de hoje, " + date.today().strftime("%d/%m/%Y") + ", a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.nome_evento}",
        f"Período: {d.periodo_evento}",
        f"Local: {d.cidade_evento} - {d.estado_evento} - {d.pais_evento}",
    ]
    if d.link_evento.strip():
        linhas.append(f"Link do evento: {d.link_evento}")
    linhas += [
        f"Apresentação de trabalho: {d.apresentacao}",
        "Valor solicitado: " + formatar_moeda(d.valor_solicitado),
        f"Detalhamento: {d.detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.logradouro}, {d.numero}",
    ]
    if d.complemento.strip():
        linhas.append(f"Complemento: {d.complemento}")
    linhas += [
        f"CEP: {d.cep}",
        f"{d.bairro}, {d.cidade} - {d.estado}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.data_nascimento}",
        f"CPF: {d.cpf}",
        f"RG / RNM: {d.rg}",
        f"Banco: {d.banco}",
        f"Agência: {d.agencia}",
        f"Conta: {d.conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(s: Solicitacao):
    erros = validar(s)
    if erros:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "aba": s.aba, "erros": erros, "oficio": "\n".join(erros)},
        )
    return {
        "ok": True,
        "aba": s.aba,
        "erros": erros,
        "oficio": gerar_oficio(s),
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")
