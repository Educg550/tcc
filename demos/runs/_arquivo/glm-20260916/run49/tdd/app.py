import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

CAMPOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "link_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao_trabalho",
    "data_nascimento",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg_rnm",
    "nome_banco",
    "numero_agencia",
    "numero_conta",
]

OPCIONAIS = {"link_evento", "complemento"}
SO_NA_ABA_ALUNOS = {"nivel", "tipo_auxilio"}


def _cpf_valido(cpf: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", cpf)]
    dv1 = sum(d[i] * (10 - i) for i in range(9)) * 10 % 11
    if dv1 != d[9]:
        return False
    dv2 = sum(d[i] * (11 - i) for i in range(10)) * 10 % 11
    return dv2 == d[10]


def _formatar_moeda(centavos: str) -> str:
    valor = int(centavos)
    reais, centavos = divmod(valor, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{centavos:02d}"


def _montar_oficio(docentes: bool, c: dict) -> str:
    if docentes:
        assunto = "Verba do programa"
        linha_programa = f"Programa: {c['programa']}"
    else:
        assunto = c["tipo_auxilio"]
        linha_programa = f"Programa: {c['programa']} - {c['nivel']}"
    linhas = [
        f"Interessada(o): {c['nome_completo']} - {c['n_usp']}",
        f"E-mail: {c['email']}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{c['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c['nome_evento']}",
        f"Período: {c['periodo_evento']}",
        f"Local: {c['cidade_evento']} - {c['estado_evento']} - {c['pais_evento']}",
    ]
    if c["link_evento"].strip():
        linhas.append(f"Link do evento: {c['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {c['apresentacao_trabalho']}",
        f"Valor solicitado: {_formatar_moeda(c['valor_solicitado'])}",
        f"Detalhamento: {c['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c['logradouro']}, {c['numero']}",
    ]
    if c["complemento"].strip():
        linhas.append(f"Complemento: {c['complemento']}")
    linhas += [
        f"CEP: {c['cep']}",
        f"{c['bairro']}, {c['cidade']} - {c['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c['data_nascimento']}",
        f"CPF: {c['cpf']}",
        f"RG / RNM: {c['rg_rnm']}",
        f"Banco: {c['nome_banco']}",
        f"Agência: {c['numero_agencia']}",
        f"Conta: {c['numero_conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


def _validar(dados: dict) -> list:
    docentes = dados.get("aba") == "docentes"
    c = {nome: str(dados.get(nome) or "") for nome in CAMPOS}
    erros = []
    obrigatorios = [
        nome
        for nome in CAMPOS
        if nome not in OPCIONAIS and not (docentes and nome in SO_NA_ABA_ALUNOS)
    ]
    if any(not c[nome].strip() for nome in obrigatorios):
        erros.append("Preencha todos os campos")
    if c["n_usp"] and not re.fullmatch(r"[0-9]+", c["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if c["numero_agencia"] and not re.fullmatch(r"[0-9]+", c["numero_agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if c["valor_solicitado"] and not (
        re.fullmatch(r"[0-9]+", c["valor_solicitado"]) and int(c["valor_solicitado"]) > 0
    ):
        erros.append("Valor solicitado deve ser maior que 0")
    if c["email"]:
        _, _, dominio = c["email"].partition("@")
        if not dominio or "." not in dominio:
            erros.append("E-mail inválido")
    cpf_ok = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", c["cpf"]))
    if c["cpf"] and not cpf_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if c["cep"] and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", c["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    data_ok = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", c["data_nascimento"]))
    if c["data_nascimento"] and not data_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_ok and not _cpf_valido(c["cpf"]):
        erros.append("CPF inválido")
    if data_ok:
        try:
            datetime.strptime(c["data_nascimento"], "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")
    return erros


app = FastAPI()


@app.post("/solicitacao")
async def solicitacao(request: Request) -> dict:
    try:
        dados = await request.()
    except Exception:
        dados = dict(await request.form())
    erros = _validar(dados)
    if erros:
        return {"valido": False, "erros": erros, "oficio": ""}
    docentes = dados.get("aba") == "docentes"
    campos = {nome: str(dados.get(nome) or "") for nome in CAMPOS}
    return {"valido": True, "erros": [], "oficio": _montar_oficio(docentes, campos)}


@app.get("/")
def pagina() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html", media_type="text/html")


app.mount("/", StaticFiles(directory=BASE_DIR), name="estaticos")
