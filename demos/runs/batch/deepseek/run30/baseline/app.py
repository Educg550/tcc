from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import calendar
import re

app = FastAPI()


class Solicitacao(BaseModel):
    tipo: str = "aluno"
    nome: str = ""
    n_usp: str = ""
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
    rg: str = ""
    banco: str = ""
    agencia: str = ""
    conta: str = ""


def cpf_valido(cpf):
    n = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(n) != 11:
        return False
    for i in (9, 10):
        soma = sum(n[j] * (i + 1 - j) for j in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != n[i]:
            return False
    return True


def data_valida(texto):
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", texto)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mes <= 12:
        return False
    try:
        ultimo = calendar.monthrange(ano, mes)[1]
    except ValueError:
        return False
    return 1 <= dia <= ultimo


def formata_valor(bruto):
    d = re.sub(r"\D", "", bruto) or "0"
    d = d.zfill(3)
    inteiro = d[:-2].lstrip("0") or "0"
    centavos = d[-2:]
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    return f"R$ {inteiro},{centavos}"


def gerar_oficio(s: Solicitacao):
    linhas = []
    linhas.append(f"Interessada(o): {s.nome} - {s.n_usp}")
    linhas.append(f"E-mail: {s.email}")
    if s.tipo == "aluno":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {s.tipo_auxilio}")
        linhas.append(f"Programa: {s.programa} - {s.nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {s.programa}")
    linhas.append("")
    linhas.append(f"A CCP-{s.programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {s.evento}")
    linhas.append(f"Período: {s.periodo}")
    linhas.append(f"Local: {s.cidade_evento} - {s.estado_evento} - {s.pais_evento}")
    if s.link_evento.strip():
        linhas.append(f"Link do evento: {s.link_evento}")
    linhas.append(f"Apresentação de trabalho: {s.apresentacao}")
    linhas.append(f"Valor solicitado: {formata_valor(s.valor)}")
    linhas.append(f"Detalhamento: {s.detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{s.logradouro}, {s.numero}")
    if s.complemento.strip():
        linhas.append(f"Complemento: {s.complemento}")
    linhas.append(f"CEP: {s.cep}")
    linhas.append(f"{s.bairro}, {s.cidade} - {s.estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {s.data_nascimento}")
    linhas.append(f"CPF: {s.cpf}")
    linhas.append(f"RG / RNM: {s.rg}")
    linhas.append(f"Banco: {s.banco}")
    linhas.append(f"Agência: {s.agencia}")
    linhas.append(f"Conta: {s.conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(s: Solicitacao):
    erros = []

    obrigatorios = [
        "nome", "n_usp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "data_nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta",
    ]
    if s.tipo == "aluno":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not getattr(s, campo).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if s.n_usp.strip() and not s.n_usp.strip().isdigit():
        erros.append("N. USP deve conter apenas números")

    if s.agencia.strip() and not s.agencia.strip().isdigit():
        erros.append("Número da agência deve conter apenas números")

    if s.valor.strip():
        digitos = re.sub(r"\D", "", s.valor)
        if not digitos or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if s.email.strip():
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s.email.strip()):
            erros.append("E-mail inválido")

    cpf = s.cpf.strip()
    if cpf:
        if not re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    if s.cep.strip() and not re.match(r"^\d{5}-\d{3}$", s.cep.strip()):
        erros.append("CEP deve estar no formato 00000-000")

    data = s.data_nascimento.strip()
    if data:
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(data):
            erros.append("Data de nascimento inválida")

    if erros:
        return {"ok": False, "erros": erros}

    return {"ok": True, "oficio": gerar_oficio(s)}


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
