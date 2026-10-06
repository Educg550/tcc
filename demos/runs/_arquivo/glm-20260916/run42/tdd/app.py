import re
import unicodedata
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent
app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


def _chave(rotulo):
    texto = unicodedata.normalize("NFKD", rotulo)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


NOME = _chave("NOME COMPLETO - SEM ABREVIAR")
NUSP = _chave("N. USP")
PROGRAMA = _chave("PROGRAMA")
NIVEL = _chave("NÍVEL")
TIPO = _chave("TIPO DE AUXÍLIO")
EMAIL = _chave("E-MAIL")
EVENTO = _chave("NOME DO EVENTO / BANCA DE EXAME OU DEFESA")
PERIODO = _chave("PERÍODO DO EVENTO, EXAME OU DEFESA")
CIDADE_EVENTO = _chave("CIDADE DO EVENTO, EXAME OU DEFESA")
ESTADO_EVENTO = _chave("ESTADO DO EVENTO, EXAME OU DEFESA")
PAIS_EVENTO = _chave("PAÍS DO EVENTO, EXAME OU DEFESA")
LINK = _chave("LINK DO EVENTO, EXAME OU DEFESA")
VALOR = _chave("VALOR SOLICITADO (R$)")
DETALHAMENTO = _chave("DETALHAMENTO DO PEDIDO")
APRESENTACAO = _chave("IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?")
NASCIMENTO = _chave("DATA DE NASCIMENTO")
LOGRADOURO = _chave("LOGRADOURO")
NUMERO = _chave("NÚMERO")
COMPLEMENTO = _chave("COMPLEMENTO")
BAIRRO = _chave("BAIRRO")
CEP = _chave("CEP")
CIDADE = _chave("CIDADE")
ESTADO = _chave("ESTADO")
CPF = _chave("CPF (SEPARADOS POR PONTOS E TRAÇO)")
RG = _chave("RG / RNM (SEPARADOS POR PONTOS E TRAÇO)")
BANCO = _chave("NOME DO BANCO")
AGENCIA = _chave("NÚMERO DA AGÊNCIA")
CONTA = _chave("NÚMERO DA CONTA")

OBRIGATORIOS = [
    NOME, NUSP, PROGRAMA, EMAIL, EVENTO, PERIODO, CIDADE_EVENTO,
    ESTADO_EVENTO, PAIS_EVENTO, VALOR, DETALHAMENTO, APRESENTACAO,
    NASCIMENTO, LOGRADOURO, NUMERO, BAIRRO, CEP, CIDADE, ESTADO,
    CPF, RG, BANCO, AGENCIA, CONTA,
]


def _centavos(texto):
    texto = (texto or "").strip()
    formatado = re.fullmatch(r"R\$\s*([0-9.]+),([0-9]{2})", texto)
    if formatado:
        return int(formatado.group(1).replace(".", "")) * 100 + int(formatado.group(2))
    if re.fullmatch(r"[0-9]+", texto):
        return int(texto)
    return None


def _moeda(centavos):
    reais, resto = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{resto:02d}"


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"[^0-9]", "", cpf)]
    dv1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    dv2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return digitos[9] == dv1 and digitos[10] == dv2


def _validar(dados):
    erros = []
    if any(not dados.get(campo) for campo in OBRIGATORIOS):
        erros.append("Preencha todos os campos")

    nusp = dados.get(NUSP, "")
    if nusp and not re.fullmatch(r"[0-9]+", nusp):
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get(AGENCIA, "")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    centavos = _centavos(dados.get(VALOR, ""))
    if centavos is None or centavos <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get(EMAIL, "")
    partes = email.split("@")
    if len(partes) != 2 or not partes[0] or not partes[1]:
        erros.append("E-mail inválido")

    cpf = dados.get(CPF, "")
    if cpf:
        if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = dados.get(CEP, "")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get(NASCIMENTO, "")
    if nascimento:
        if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            try:
                datetime.strptime(nascimento, "%d/%m/%Y")
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def _oficio(dados):
    docentes = not (dados.get(NIVEL) and dados.get(TIPO))
    assunto = "Verba do programa" if docentes else dados[TIPO]
    if docentes:
        programa = f"Programa: {dados[PROGRAMA]}"
    else:
        programa = f"Programa: {dados[PROGRAMA]} - {dados[NIVEL]}"
    linhas = [
        f"Interessada(o): {dados[NOME]} - {dados[NUSP]}",
        f"E-mail: {dados[EMAIL]}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        programa,
        "",
        "A CCP-" + dados[PROGRAMA] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados[EVENTO]}",
        f"Período: {dados[PERIODO]}",
        f"Local: {dados[CIDADE_EVENTO]} - {dados[ESTADO_EVENTO]} - {dados[PAIS_EVENTO]}",
    ]
    if dados.get(LINK):
        linhas.append(f"Link do evento: {dados[LINK]}")
    linhas.extend([
        f"Apresentação de trabalho: {dados[APRESENTACAO]}",
        f"Valor solicitado: {_moeda(_centavos(dados[VALOR]))}",
        f"Detalhamento: {dados[DETALHAMENTO]}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados[LOGRADOURO]}, {dados[NUMERO]}",
    ])
    if dados.get(COMPLEMENTO):
        linhas.append(f"Complemento: {dados[COMPLEMENTO]}")
    linhas.extend([
        f"CEP: {dados[CEP]}",
        f"{dados[BAIRRO]}, {dados[CIDADE]} - {dados[ESTADO]}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados[NASCIMENTO]}",
        f"CPF: {dados[CPF]}",
        f"RG / RNM: {dados[RG]}",
        f"Banco: {dados[BANCO]}",
        f"Agência: {dados[AGENCIA]}",
        f"Conta: {dados[CONTA]}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.post("/solicitacao")
async def solicitacao(request: Request):
    try:
        bruto = await request.()
    except Exception:
        bruto = dict(await request.form())
    if not isinstance(bruto, dict):
        bruto = {}
    dados = {_chave(str(chave)): str(valor).strip() for chave, valor in bruto.items()}
    erros = _validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={"ok": False, "erros": erros})
    return {"ok": True, "oficio": _oficio(dados)}


@app.get("/")
async def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
async def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
async def roteiro():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
