from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

ALUNOS_CAMPOS = [
    "nome_completo", "nusp", "programa", "nivel", "tipo_auxilio", "email",
    "nome_evento", "periodo_evento", "cidade_evento", "estado_evento",
    "pais_evento", "link_evento", "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "complemento", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

DOCENTES_CAMPOS = [c for c in ALUNOS_CAMPOS if c not in ("nivel", "tipo_auxilio")]

OBRIGATORIOS = [c for c in ALUNOS_CAMPOS if c not in ("link_evento", "complemento")]

R = {"nome_completo": "nome", "nusp": "nusp", "programa": "programa", "nivel": "nivel",
     "tipo_auxilio": "tipo_auxilio", "email": "email", "nome_evento": "nome_evento",
     "periodo_evento": "periodo", "cidade_evento": "cidade_evento",
     "estado_evento": "estado_evento", "pais_evento": "pais_evento",
     "link_evento": "link_evento", "valor": "valor", "detalhamento": "detalhamento",
     "apresentacao": "apresentacao", "data_nascimento": "data_nascimento",
     "logradouro": "logradouro", "numero": "numero", "complemento": "complemento",
     "bairro": "bairro", "cep": "cep", "cidade": "cidade", "estado": "estado",
     "cpf": "cpf", "rg": "rg", "banco": "banco", "agencia": "agencia", "conta": "conta"}

MENSAGENS = {
    "vazio": "Preencha todos os campos",
    "nusp": "N. USP deve conter apenas números",
    "agencia": "Número da agência deve conter apenas números",
    "valor": "Valor solicitado deve ser maior que 0",
    "email": "E-mail inválido",
    "cpf_formato": "CPF deve estar no formato 000.000.000-00",
    "cep_formato": "CEP deve estar no formato 00000-000",
    "data_formato": "Data de nascimento deve estar no formato dd/mm/aaaa",
    "cpf": "CPF inválido",
    "data": "Data de nascimento inválida",
}


def _so_digitos(v):
    return v.isdigit() if v else False


def _cpf_valido(v):
    d = [int(c) for c in v if c.isdigit()]
    if len(d) != 11:
        return False
    if d == [d[0]] * 11:
        return False
    s = sum(x * (10 - i) for i, x in enumerate(d[:9])) % 11
    dv1 = 0 if s < 2 else 11 - s
    s2 = sum(x * (11 - i) for i, x in enumerate(d[:10])) % 11
    dv2 = 0 if s2 < 2 else 11 - s2
    return dv1 == d[9] and dv2 == d[10]


def _data_valida(v):
    dia, mes, ano = int(v[:2]), int(v[3:5]), int(v[6:10])
    if mes < 1 or mes > 12:
        return False
    dias_mes = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dia <= dias_mes[mes - 1]


def _moeda(centavos):
    inteiro, fr = divmod(centavos, 100)
    inteiro = str(inteiro)
    partes = []
    while len(inteiro) > 3:
        partes.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    partes.insert(0, inteiro)
    return "R$ " + ".".join(partes) + "," + str(fr).zfill(2)


def _validar(aba, dados):
    campos = ALUNOS_CAMPOS if aba == "alunos" else DOCENTES_CAMPOS
    erros = []
    faltando = any(not str(dados.get(c, "")).strip() for c in campos if c in OBRIGATORIOS)
    if faltando:
        erros.append(MENSAGENS["vazio"])
    nusp = str(dados.get("nusp", "")).strip()
    if nusp and not _so_digitos(nusp):
        erros.append(MENSAGENS["nusp"])
    agencia = str(dados.get("agencia", "")).strip()
    if agencia and not _so_digitos(agencia):
        erros.append(MENSAGENS["agencia"])
    valor = str(dados.get("valor", "")).strip()
    if valor and not (valor.isdigit() and int(valor) > 0):
        erros.append(MENSAGENS["valor"])
    email = str(dados.get("email", "")).strip()
    if email and ("@" not in email or not email.split("@", 1)[1].strip()):
        erros.append(MENSAGENS["email"])
    cpf = str(dados.get("cpf", "")).strip()
    if cpf and len(cpf) == 14 and cpf[3] == "." and cpf[7] == "." and cpf[11] == "-" and _so_digitos(cpf.replace(".", "").replace("-", "")):
        if not _cpf_valido(cpf):
            erros.append(MENSAGENS["cpf"])
    elif cpf:
        erros.append(MENSAGENS["cpf_formato"])
    cep = str(dados.get("cep", "")).strip()
    if cep and not (len(cep) == 9 and cep[:5].isdigit() and cep[5] == "-" and cep[6:].isdigit()):
        erros.append(MENSAGENS["cep_formato"])
    data = str(dados.get("data_nascimento", "")).strip()
    if data:
        if len(data) == 10 and data[2] == "/" and data[5] == "/" and data[:2].isdigit() and data[3:5].isdigit() and data[6:10].isdigit():
            if not _data_valida(data):
                erros.append(MENSAGENS["data"])
        else:
            erros.append(MENSAGENS["data_formato"])
    return erros


def _oficio(aba, dados):
    programa = str(dados.get("programa", "")).strip()
    linhas = [
        f"Interessada(o): {dados.get('nome_completo', '')} - {dados.get('nusp', '')}",
        f"E-mail: {dados.get('email', '')}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {dados.get('tipo_auxilio', '')}")
        linhas.append(f"Programa: {programa} - {dados.get('nivel', '')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    linhas += [
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados.get('nome_evento', '')}",
        f"Período: {dados.get('periodo_evento', '')}",
        f"Local: {dados.get('cidade_evento', '')} - {dados.get('estado_evento', '')} - {dados.get('pais_evento', '')}",
    ]
    link = str(dados.get("link_evento", "")).strip()
    if link:
        linhas.append(f"Link do evento: {link}")
    valor_centavos = int(dados.get("valor", 0))
    linhas += [
        f"Apresentação de trabalho: {dados.get('apresentacao', '')}",
        f"Valor solicitado: {_moeda(valor_centavos)}",
        f"Detalhamento: {dados.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados.get('logradouro', '')}, {dados.get('numero', '')}",
    ]
    complemento = str(dados.get("complemento", "")).strip()
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {dados.get('cep', '')}",
        f"{dados.get('bairro', '')}, {dados.get('cidade', '')} - {dados.get('estado', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados.get('data_nascimento', '')}",
        f"CPF: {dados.get('cpf', '')}",
        f"RG / RNM: {dados.get('rg', '')}",
        f"Banco: {dados.get('banco', '')}",
        f"Agência: {dados.get('agencia', '')}",
        f"Conta: {dados.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


app = FastAPI()
app.mount("/assets", StaticFiles(directory=str(BASE / "assets")), name="assets")


@app.get("/")
def index():
    return FileResponse(str(BASE / "index.html"))


@app.post("/solicitacao")
def solicitacao(payload: dict):
    aba = payload.get("aba", "alunos")
    dados = payload.get("dados", {})
    erros = _validar(aba, dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _oficio(aba, dados)}
