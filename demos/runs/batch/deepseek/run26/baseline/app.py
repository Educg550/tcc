import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


class Solicitacao(BaseModel):
    aba: str = "alunos"
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


def _vazio(valor):
    return not (valor or "").strip()


def _em_centavos(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return None
    return int(digitos)


def _moeda(centavos):
    reais, cent = divmod(centavos or 0, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def _email_ok(email):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def _cpf_formato_ok(cpf):
    return re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf) is not None


def _cpf_digitos_ok(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    for i in (9, 10):
        soma = sum(nums[j] * ((i + 1) - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != nums[i]:
            return False
    return True


def _data_formato_ok(data):
    return re.fullmatch(r"\d{2}/\d{2}/\d{4}", data) is not None


def _data_ok(data):
    dia, mes, ano = data.split("/")
    try:
        date(int(ano), int(mes), int(dia))
    except ValueError:
        return False
    return True


def validar(dados):
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if dados.get("aba") == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(_vazio(dados.get(c)) for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = (dados.get("n_usp") or "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = (dados.get("agencia") or "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = (dados.get("valor") or "").strip()
    if valor and (_em_centavos(valor) or 0) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = (dados.get("email") or "").strip()
    if email and not _email_ok(email):
        erros.append("E-mail inválido")

    cpf = (dados.get("cpf") or "").strip()
    cpf_formato = bool(cpf) and _cpf_formato_ok(cpf)
    if cpf and not cpf_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = (dados.get("cep") or "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = (dados.get("data_nascimento") or "").strip()
    data_formato = bool(nascimento) and _data_formato_ok(nascimento)
    if nascimento and not data_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_formato and not _cpf_digitos_ok(cpf):
        erros.append("CPF inválido")

    if data_formato and not _data_ok(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(d):
    programa = (d.get("programa") or "").strip()
    alunos = d.get("aba") == "alunos"

    linhas = [
        f"Interessada(o): {(d.get('nome') or '').strip()} - {(d.get('n_usp') or '').strip()}",
        f"E-mail: {(d.get('email') or '').strip()}",
    ]
    if alunos:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d.get('tipo_auxilio')}")
        linhas.append(f"Programa: {programa} - {d.get('nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")

    linhas += [
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {(d.get('evento') or '').strip()}",
        f"Período: {(d.get('periodo') or '').strip()}",
        f"Local: {(d.get('cidade_evento') or '').strip()} - {(d.get('estado_evento') or '').strip()} - {(d.get('pais_evento') or '').strip()}",
    ]

    link = (d.get("link_evento") or "").strip()
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas += [
        f"Apresentação de trabalho: {d.get('apresentacao')}",
        f"Valor solicitado: {_moeda(_em_centavos(d.get('valor')) or 0)}",
        f"Detalhamento: {(d.get('detalhamento') or '').strip()}",
        "",
        "Endereço da(o) interessada(o)",
        f"{(d.get('logradouro') or '').strip()}, {(d.get('numero') or '').strip()}",
    ]

    complemento = (d.get("complemento") or "").strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas += [
        f"CEP: {(d.get('cep') or '').strip()}",
        f"{(d.get('bairro') or '').strip()}, {(d.get('cidade') or '').strip()} - {(d.get('estado') or '').strip()}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {(d.get('data_nascimento') or '').strip()}",
        f"CPF: {(d.get('cpf') or '').strip()}",
        f"RG / RNM: {(d.get('rg') or '').strip()}",
        f"Banco: {(d.get('banco') or '').strip()}",
        f"Agência: {(d.get('agencia') or '').strip()}",
        f"Conta: {(d.get('conta') or '').strip()}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(pedido: Solicitacao):
    dados = pedido.model_dump()
    erros = validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(dados)}


@app.get("/")
def index():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


app.mount("/assets", StaticFiles(directory="assets"), name="assets")
