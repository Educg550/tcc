import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS_ALUNOS = [
    "nome_completo", "numusp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
    "pais_evento", "link_evento", "valor_solicitado", "detalhamento",
    "apresenta_trabalho", "data_nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidade", "estado", "cpf", "rg_rnm",
    "nome_banco", "numero_agencia", "numero_conta",
]
CAMPOS_DOCENTES = [c for c in CAMPOS_ALUNOS if c not in ("nivel", "tipo_auxilio")]
OBRIGATORIOS_ALUNOS = [c for c in CAMPOS_ALUNOS if c not in ("link_evento", "complemento")]
OBRIGATORIOS_DOCENTES = [c for c in CAMPOS_DOCENTES if c not in ("link_evento", "complemento")]

RE_NUM = re.compile(r"^[0-9]+$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")
RE_CEP = re.compile(r"^[0-9]{5}-[0-9]{3}$")
RE_DATA = re.compile(r"^([0-9]{2})/([0-9]{2})/([0-9]{4})$")
RE_VALOR = re.compile(r"^R\$ ?([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})$")


def _cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    pesos = range(10, 1, -1)
    d1 = sum(int(c) * p for c, p in zip(cpf[:9], pesos)) % 11
    d1 = 0 if d1 < 2 else 11 - d1
    pesos2 = range(11, 1, -1)
    d2 = sum(int(c) * p for c, p in zip(cpf[:10], pesos2)) % 11
    d2 = 0 if d2 < 2 else 11 - d2
    return d1 == int(cpf[9]) and d2 == int(cpf[10])


def _data_valida(data: str) -> bool:
    m = RE_DATA.match(data)
    if not m:
        return False
    dia, mes, ano = (int(g) for g in m.groups())
    if not 1 <= mes <= 12:
        return False
    dias_no_mes = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
                   31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dia <= dias_no_mes[mes - 1]


def _valor_para_reais(valor: str) -> str:
    m = RE_VALOR.match(valor)
    if not m:
        return valor
    return m.group(1).replace(".", ",").replace(",", ".", 1)


def _erros(dados: dict, obrigatorios: list) -> list:
    erros = []
    if any(not str(dados.get(c, "")).strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")
    if dados.get("numusp") and not RE_NUM.match(dados["numusp"]):
        erros.append("N. USP deve conter apenas n\u00fameros")
    if dados.get("numero_agencia") and not RE_NUM.match(dados["numero_agencia"]):
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")
    if dados.get("valor_solicitado"):
        m = RE_VALOR.match(dados["valor_solicitado"])
        if not m or int(m.group(1).replace(".", "").replace(",", "")) == 0:
            erros.append("Valor solicitado deve ser maior que 0")
    if dados.get("email") and "@" not in dados["email"].strip():
        erros.append("E-mail inv\u00e1lido")
    elif dados.get("email"):
        sobra = dados["email"].strip().rsplit("@", 1)[1]
        if not sobra or "." not in sobra or sobra.startswith(".") or sobra.endswith("."):
            erros.append("E-mail inv\u00e1lido")
    cpf_marcas = re.sub(r"[^0-9]", "", dados.get("cpf", ""))
    if dados.get("cpf") and not re.match(r"^[0-9]{3}\.?[0-9]{3}\.?[0-9]{3}-?[0-9]{2}$", dados["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif dados.get("cpf") and not _cpf_valido(cpf_marcas):
        erros.append("CPF inv\u00e1lido")
    if dados.get("cep") and not RE_CEP.match(dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    data = dados.get("data_nascimento", "")
    if data and not RE_DATA.match(data):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif data and not _data_valida(data):
        erros.append("Data de nascimento inv\u00e1lida")
    return erros


def _oficio(d: dict, docentes: bool) -> str:
    valor = _valor_para_reais(d.get("valor_solicitado", ""))
    linhas = [
        f"Interessada(o): {d['nome_completo']} - {d['numusp']}",
        f"E-mail: {d['email']}",
        f"Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - "
        + ("Verba do programa" if docentes else d["tipo_auxilio"]),
        f"Programa: {d['programa']}" + ("" if docentes else f" - {d['nivel']}"),
        "",
        f"A CCP-{d['programa']} aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio "
        "financeiro para a interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['nome_evento']}",
        f"Per\u00edodo: {d['periodo_evento']}",
        f"Local: {d['cidade_evento']} - {d['estado_evento']} - {d['pais_evento']}",
    ]
    if d.get("link_evento"):
        linhas.append(f"Link do evento: {d['link_evento']}")
    linhas += [
        f"Apresenta\u00e7\u00e3o de trabalho: {d['apresenta_trabalho']}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {d['detalhamento']}",
        "",
        "Endere\u00e7o da(o) interessada(o)",
        f"{d['logradouro']}, {d['numero']}",
    ]
    if d.get("complemento"):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas += [
        f"CEP: {d['cep']}",
        f"{d['bairro']}, {d['cidade']} - {d['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d['data_nascimento']}",
        f"CPF: {d['cpf']}",
        f"RG / RNM: {d['rg_rnm']}",
        f"Banco: {d['nome_banco']}",
        f"Ag\u00eancia: {d['numero_agencia']}",
        f"Conta: {d['numero_conta']}",
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitacao(payload: dict):
    aba = payload.get("aba", "alunos")
    dados = payload.get("dados", {})
    dados = {c: str(dados.get(c, "")).strip() for c in (CAMPOS_DOCENTES if aba == "docentes" else CAMPOS_ALUNOS)}
    obrigatorios = OBRIGATORIOS_DOCENTES if aba == "docentes" else OBRIGATORIOS_ALUNOS
    erros = _erros(dados, obrigatorios)
    if erros:
        return {"ok": False, "erros": erros, "oficio": ""}
    return {"ok": True, "erros": [], "oficio": _oficio(dados, aba == "docentes")}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
