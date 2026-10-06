import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

ROTULOS = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}
SO_NA_ABA_ALUNOS = ("NÍVEL", "TIPO DE AUXÍLIO")


def _variantes(rotulo):
    return (
        rotulo,
        re.sub(r"[^a-z0-9]+", "_", rotulo.lower()).strip("_"),
        rotulo.lower(),
    )


POR_VARIACAO = {
    variacao: rotulo for rotulo in ROTULOS for variacao in _variantes(rotulo)
}

app = FastAPI()


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def roteiro():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


@app.post("/solicitar")
async def solicitar(request: Request):
    dados = _normalizar(await _corpo(request))
    aba = "alunos" if any(campo in dados for campo in SO_NA_ABA_ALUNOS) else "docentes"
    erros = _validar(dados, aba)
    if erros:
        return JSONResponse({"erros": erros})
    return JSONResponse({"oficio": _oficio(dados, aba)})


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


async def _corpo(request: Request):
    try:
        if "" in request.headers.get("content-type", ""):
            return await request.()
        return dict(await request.form())
    except Exception:
        return {}


def _normalizar(bruto):
    if not isinstance(bruto, dict):
        return {}
    dados = {}
    for chave, valor in bruto.items():
        rotulo = POR_VARIACAO.get(str(chave))
        if rotulo:
            dados[rotulo] = valor if isinstance(valor, str) else str(valor)
    return dados


def _validar(dados, aba):
    erros = []
    obrigatorios = [
        rotulo
        for rotulo in ROTULOS
        if rotulo not in OPCIONAIS
        and not (aba == "docentes" and rotulo in SO_NA_ABA_ALUNOS)
    ]
    if any(not dados.get(rotulo, "").strip() for rotulo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = dados.get("N. USP", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("NÚMERO DA AGÊNCIA", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    texto_do_valor = dados.get("VALOR SOLICITADO (R$)", "").strip()
    valor = _valor(texto_do_valor)
    if texto_do_valor and (valor is None or valor <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("E-MAIL", "").strip()
    if email:
        partes = email.split("@")
        if len(partes) != 2 or not partes[0] or not partes[1]:
            erros.append("E-mail inválido")

    cpf = dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "").strip()
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = dados.get("CEP", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get("DATA DE NASCIMENTO", "").strip()
    if nascimento:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(nascimento):
            erros.append("Data de nascimento inválida")

    return erros


def _valor(texto):
    limpo = texto.strip()
    if limpo[:2].upper() == "R$":
        limpo = limpo[2:].strip()
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif limpo.count(".") > 1:
        limpo = limpo.replace(".", "")
    try:
        return float(limpo)
    except ValueError:
        return None


def _formatar_valor(valor):
    centavos = round(valor * 100)
    inteiro = f"{centavos // 100:,}".replace(",", ".")
    return "R$ " + inteiro + f",{centavos % 100:02d}"


def _cpf_valido(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    resto = sum(digito * peso for digito, peso in zip(digitos[:9], range(10, 1, -1))) % 11
    primeiro = 0 if resto < 2 else 11 - resto
    resto = sum(digito * peso for digito, peso in zip(digitos[:10], range(11, 1, -1))) % 11
    segundo = 0 if resto < 2 else 11 - resto
    return digitos[9] == primeiro and digitos[10] == segundo


def _data_valida(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _oficio(dados, aba):
    programa = dados["PROGRAMA"]
    if aba == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_do_programa = f"Programa: {programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {dados['TIPO DE AUXÍLIO']}"
        linha_do_programa = f"Programa: {programa} - {dados['NÍVEL']}"

    valor = _formatar_valor(_valor(dados["VALOR SOLICITADO (R$)"]))
    link = dados.get("LINK DO EVENTO, EXAME OU DEFESA", "").strip()
    complemento = dados.get("COMPLEMENTO", "").strip()

    linhas = [
        f"Interessada(o): {dados['NOME COMPLETO - SEM ABREVIAR']} - {dados['N. USP']}",
        f"E-mail: {dados['E-MAIL']}",
        f"Assunto: {assunto}",
        linha_do_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {dados['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {dados['CIDADE DO EVENTO, EXAME OU DEFESA']} - {dados['ESTADO DO EVENTO, EXAME OU DEFESA']} - {dados['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {dados['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {dados['DETALHAMENTO DO PEDIDO']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['LOGRADOURO']}, {dados['NÚMERO']}",
    ]
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {dados['CEP']}",
        f"{dados['BAIRRO']}, {dados['CIDADE']} - {dados['ESTADO']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['DATA DE NASCIMENTO']}",
        f"CPF: {dados['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"RG / RNM: {dados['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
        f"Banco: {dados['NOME DO BANCO']}",
        f"Agência: {dados['NÚMERO DA AGÊNCIA']}",
        f"Conta: {dados['NÚMERO DA CONTA']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)
