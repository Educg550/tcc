import os
import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")

CAMPOS_ALUNOS = [
    "nome", "nusp", "programa", "nivel", "tipoAuxilio", "email",
    "nomeEvento", "periodo", "cidade", "estado", "pais", "link", "valor",
    "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidadeSolicitante", "estadoSolicitante",
    "cpf", "rg", "banco", "agencia", "conta",
]

CAMPOS_DOCENTES = [
    "nome", "nusp", "programa", "email",
    "nomeEvento", "periodo", "cidade", "estado", "pais", "link", "valor",
    "detalhamento", "apresentacao", "nascimento", "logradouro", "numero",
    "complemento", "bairro", "cep", "cidadeSolicitante", "estadoSolicitante",
    "cpf", "rg", "banco", "agencia", "conta",
]

LABELS = {
    "nome": "NOME COMPLETO - SEM ABREVIAR",
    "nusp": "N. USP",
    "programa": "PROGRAMA",
    "nivel": "N\u00cdVEL",
    "tipoAuxilio": "TIPO DE AUX\u00cdLIO",
    "email": "E-MAIL",
    "nomeEvento": "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "periodo": "PER\u00cdODO DO EVENTO, EXAME OU DEFESA",
    "cidade": "CIDADE DO EVENTO, EXAME OU DEFESA",
    "estado": "ESTADO DO EVENTO, EXAME OU DEFESA",
    "pais": "PA\u00cdS DO EVENTO, EXAME OU DEFESA",
    "link": "LINK DO EVENTO, EXAME OU DEFESA",
    "valor": "VALOR SOLICITADO (R$)",
    "detalhamento": "DETALHAMENTO DO PEDIDO",
    "apresentacao": "IR\u00c1 APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "nascimento": "DATA DE NASCIMENTO",
    "logradouro": "LOGRADOURO",
    "numero": "N\u00daMERO",
    "complemento": "COMPLEMENTO",
    "bairro": "BAIRRO",
    "cep": "CEP",
    "cidadeSolicitante": "CIDADE",
    "estadoSolicitante": "ESTADO",
    "cpf": "CPF (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "rg": "RG / RNM (SEPARADOS POR PONTOS E TRA\u00c7O)",
    "banco": "NOME DO BANCO",
    "agencia": "N\u00daMERO DA AG\u00caNCIA",
    "conta": "N\u00daMERO DA CONTA",
}

OPCIONAIS = {"link", "complemento"}


def _cpf_valido(cpf):
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    for i in (9, 10):
        soma = sum(digitos[j] * (i - j) for j in range(i - 1))
        dv = (soma * 10) % 11
        if dv == 10:
            dv = 0
        if dv != digitos[i - 1]:
            return False
    return True


def _data_valida(data):
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        return False
    dia, mes, ano = (int(data[0:2]), int(data[3:5]), int(data[6:10]))
    if not 1 <= mes <= 12:
        return False
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _email_valido(email):
    return "@" in email and email.split("@", 1)[1].find(".") > 0


def _moeda(digitos):
    if not digitos:
        return "R$ 0,00"
    d = int(digitos)
    inteiro, cent = divmod(d, 100)
    grupo, inteiro = inteiro % 1000, inteiro // 1000
    partes = []
    while grupo >= 1000:
        partes.append("%03d" % (grupo % 1000))
        grupo //= 1000
    partes.append("%d" % grupo)
    return "R$ " + ".".join(reversed(partes)) + "," + "%02d" % cent


def _validar(tipo, dados):
    erros = []
    campos = CAMPOS_ALUNOS if tipo == "alunos" else CAMPOS_DOCENTES
    valores = {c: (dados.get(c) or "").strip() for c in campos}
    for c in campos:
        if c not in OPCIONAIS and not valores[c]:
            erros.append("Preencha todos os campos")
            break
    if any(not valores[c] for c in campos if c not in OPCIONAIS):
        return erros
    if valores["nusp"] and not valores["nusp"].isdigit():
        erros.append("N. USP deve conter apenas n\u00fameros")
    if valores["agencia"] and not valores["agencia"].isdigit():
        erros.append("N\u00famero da ag\u00eancia deve conter apenas n\u00fameros")
    v = valores["valor"]
    digitos = re.sub(r"\D", "", v)
    try:
        valor_int = int(digitos) if digitos else 0
    except ValueError:
        valor_int = 0
    if valor_int <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if valores["email"] and not _email_valido(valores["email"]):
        erros.append("E-mail inv\u00e1lido")
    if valores["cpf"]:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", valores["cpf"]):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(valores["cpf"]):
            erros.append("CPF inv\u00e1lido")
    if valores["cep"] and not re.fullmatch(r"\d{5}-\d{3}", valores["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if valores["nascimento"]:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", valores["nascimento"]):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(valores["nascimento"]):
            erros.append("Data de nascimento inv\u00e1lida")
    return erros


def _oficio(tipo, dados, digitos):
    get = lambda k: (dados.get(k) or "").strip()
    nivel = get("nivel")
    tipo_aux = get("tipoAuxilio")
    programa = get("programa")
    if tipo == "alunos":
        assunto = f"Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - {tipo_aux}"
        programa_linha = f"Programa: {programa} - {nivel}"
    else:
        assunto = "Assunto: Solicita\u00e7\u00e3o de Aux\u00edlio Financeiro - Verba do programa"
        programa_linha = f"Programa: {programa}"
    link = get("link")
    complemento = get("complemento")
    linhas = [
        f"Interessada(o): {get('nome')} - {get('nusp')}",
        f"E-mail: {get('email')}",
        assunto,
        programa_linha,
        "",
        "A CCP-" + programa + " aprovou na data de hoje, a solicita\u00e7\u00e3o de aux\u00edlio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {get('nomeEvento')}",
        f"Per\u00edodo: {get('periodo')}",
        f"Local: {get('cidade')} - {get('estado')} - {get('pais')}",
    ]
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresenta\u00e7\u00e3o de trabalho: {get('apresentacao')}",
        f"Valor solicitado: {_moeda(digitos)}",
        f"Detalhamento: {get('detalhamento')}",
        "",
        "Endere\u00e7o da(o) interessada(o)",
        f"{get('logradouro')}, {get('numero')}",
    ]
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {get('cep')}",
        f"{get('bairro')}, {get('cidadeSolicitante')} - {get('estadoSolicitante')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {get('nascimento')}",
        f"CPF: {get('cpf')}",
        f"RG / RNM: {get('rg')}",
        f"Banco: {get('banco')}",
        f"Ag\u00eancia: {get('agencia')}",
        f"Conta: {get('conta')}",
        "",
        "Encaminhe-se ao Servi\u00e7o Financeiro para provid\u00eancias.",
    ]
    return "\n".join(linhas)


@app.get("/")
def index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/style.css")
def style():
    return FileResponse(os.path.join(BASE_DIR, "style.css"), media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(os.path.join(BASE_DIR, "app.js"), media_type="text/javascript")


@app.post("/solicitacao")
def solicitacao(payload: dict):
    tipo = payload.get("tipo") or "alunos"
    campos = CAMPOS_ALUNOS if tipo == "alunos" else CAMPOS_DOCENTES
    dados = {c: (payload.get(c) or "") for c in campos}
    erros = _validar(tipo, dados)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    digitos = re.sub(r"\D", "", dados["valor"])
    oficio = _oficio(tipo, dados, digitos)
    return JSONResponse({"ok": True, "oficio": oficio})
