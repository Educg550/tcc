import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

OPCIONAIS = {"link_evento", "complemento"}
COMUNS = [
    "nome_completo", "n_usp", "programa", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
    "pais_evento", "valor_solicitado", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg_rnm", "nome_banco", "agencia", "numero_conta",
]
REQUERIDOS = {
    "alunos": (set(COMUNS) | {"nivel", "tipo_auxilio"}) - OPCIONAIS,
    "docentes": set(COMUNS) - OPCIONAIS,
}

app = FastAPI()


@app.post("/api/solicitar")
async def solicitar(request: Request):
    dados = await request.()
    tipo = dados.get("tipo")
    if tipo not in REQUERIDOS:
        tipo = "alunos"
    erros = _validar(dados, REQUERIDOS[tipo])
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _gerar_oficio(dados, tipo)}


def _texto(dados, nome):
    return str(dados.get(nome, "")).strip()


def _validar(dados, requeridos):
    erros = []
    if any(not _texto(dados, campo) for campo in requeridos):
        erros.append("Preencha todos os campos")

    n_usp = _texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = _texto(dados, "agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = _texto(dados, "valor_solicitado")
    centavos = re.sub(r"\D", "", valor)
    if valor and (not centavos or int(centavos) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = _texto(dados, "email")
    if email:
        local, _, dominio = email.partition("@")
        if not local or not dominio:
            erros.append("E-mail inválido")

    cpf = _texto(dados, "cpf")
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = _texto(dados, "cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = _texto(dados, "data_nascimento")
    data_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", data))
    if data and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data_no_formato:
        try:
            datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def _cpf_valido(cpf):
    n = [int(digito) for digito in cpf]
    d1 = (sum(n[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    d2 = (sum(n[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return n[9] == d1 and n[10] == d2


def _gerar_oficio(dados, tipo):
    linhas = [
        f"Interessada(o): {_texto(dados, 'nome_completo')} - {_texto(dados, 'n_usp')}",
        f"E-mail: {_texto(dados, 'email')}",
    ]
    if tipo == "alunos":
        linhas += [
            f"Assunto: Solicitação de Auxílio Financeiro - {_texto(dados, 'tipo_auxilio')}",
            f"Programa: {_texto(dados, 'programa')} - {_texto(dados, 'nivel')}",
        ]
    else:
        linhas += [
            "Assunto: Solicitação de Auxílio Financeiro - Verba do programa",
            f"Programa: {_texto(dados, 'programa')}",
        ]
    linhas += [
        "",
        f"A CCP-{_texto(dados, 'programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {_texto(dados, 'nome_evento')}",
        f"Período: {_texto(dados, 'periodo_evento')}",
        f"Local: {_texto(dados, 'cidade_evento')} - {_texto(dados, 'estado_evento')} - {_texto(dados, 'pais_evento')}",
    ]
    if _texto(dados, "link_evento"):
        linhas.append(f"Link do evento: {_texto(dados, 'link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {_texto(dados, 'apresentacao')}",
        f"Valor solicitado: {_texto(dados, 'valor_solicitado')}",
        f"Detalhamento: {_texto(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{_texto(dados, 'logradouro')}, {_texto(dados, 'numero')}",
    ]
    if _texto(dados, "complemento"):
        linhas.append(f"Complemento: {_texto(dados, 'complemento')}")
    linhas += [
        f"CEP: {_texto(dados, 'cep')}",
        f"{_texto(dados, 'bairro')}, {_texto(dados, 'cidade')} - {_texto(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {_texto(dados, 'data_nascimento')}",
        f"CPF: {_texto(dados, 'cpf')}",
        f"RG / RNM: {_texto(dados, 'rg_rnm')}",
        f"Banco: {_texto(dados, 'nome_banco')}",
        f"Agência: {_texto(dados, 'agencia')}",
        f"Conta: {_texto(dados, 'numero_conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
async def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
async def estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
async def script():
    return FileResponse(BASE / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")
