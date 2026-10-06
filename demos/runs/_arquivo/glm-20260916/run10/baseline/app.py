import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

NOME = "NOME COMPLETO - SEM ABREVIAR"
NUSP = "N. USP"
PROGRAMA = "PROGRAMA"
NIVEL = "NÍVEL"
TIPO_AUXILIO = "TIPO DE AUXÍLIO"
EMAIL = "E-MAIL"
EVENTO = "NOME DO EVENTO / BANCA DE EXAME OU DEFESA"
PERIODO = "PERÍODO DO EVENTO, EXAME OU DEFESA"
CIDADE_EVENTO = "CIDADE DO EVENTO, EXAME OU DEFESA"
ESTADO_EVENTO = "ESTADO DO EVENTO, EXAME OU DEFESA"
PAIS_EVENTO = "PAÍS DO EVENTO, EXAME OU DEFESA"
LINK = "LINK DO EVENTO, EXAME OU DEFESA"
VALOR = "VALOR SOLICITADO (R$)"
DETALHAMENTO = "DETALHAMENTO DO PEDIDO"
APRESENTACAO = "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?"
DATA_NASCIMENTO = "DATA DE NASCIMENTO"
LOGRADOURO = "LOGRADOURO"
NUMERO = "NÚMERO"
COMPLEMENTO = "COMPLEMENTO"
BAIRRO = "BAIRRO"
CEP = "CEP"
CIDADE = "CIDADE"
ESTADO = "ESTADO"
CPF = "CPF (SEPARADOS POR PONTOS E TRAÇO)"
RG_RNM = "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)"
BANCO = "NOME DO BANCO"
AGENCIA = "NÚMERO DA AGÊNCIA"
CONTA = "NÚMERO DA CONTA"

ROTULOS = [
    NOME, NUSP, PROGRAMA, NIVEL, TIPO_AUXILIO, EMAIL, EVENTO, PERIODO,
    CIDADE_EVENTO, ESTADO_EVENTO, PAIS_EVENTO, LINK, VALOR, DETALHAMENTO,
    APRESENTACAO, DATA_NASCIMENTO, LOGRADOURO, NUMERO, COMPLEMENTO, BAIRRO,
    CEP, CIDADE, ESTADO, CPF, RG_RNM, BANCO, AGENCIA, CONTA,
]
OPCIONAIS = {LINK, COMPLEMENTO}

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")


@app.post("/solicitacao")
def validar_solicitacao(dados: dict) -> dict:
    formulario = str(dados.get("formulario", "alunos")).strip().lower()
    if formulario != "docentes":
        formulario = "alunos"
    campos = {rotulo: _campo(dados, rotulo) for rotulo in ROTULOS}
    erros = _erros(campos, formulario)
    if erros:
        return {"valido": False, "erros": erros}
    return {"valido": True, "oficio": _oficio(campos, formulario)}


@app.get("/")
def pagina() -> FileResponse:
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def estilo() -> FileResponse:
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def script() -> FileResponse:
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets", check_dir=False), name="assets")


def _campo(dados: dict, rotulo: str) -> str:
    valor = dados.get(rotulo, "")
    if valor is None:
        return ""
    if not isinstance(valor, str):
        valor = str(valor)
    return valor.strip()


def _erros(c: dict, formulario: str) -> list:
    obrigatorios = [rotulo for rotulo in ROTULOS if rotulo not in OPCIONAIS]
    if formulario == "docentes":
        obrigatorios = [rotulo for rotulo in obrigatorios if rotulo not in (NIVEL, TIPO_AUXILIO)]

    erros = []
    if any(not c[rotulo] for rotulo in obrigatorios):
        erros.append("Preencha todos os campos")

    if c[NUSP] and not c[NUSP].isdigit():
        erros.append("N. USP deve conter apenas números")

    if c[AGENCIA] and not c[AGENCIA].isdigit():
        erros.append("Número da agência deve conter apenas números")

    if c[VALOR] and not _valor_positivo(c[VALOR]):
        erros.append("Valor solicitado deve ser maior que 0")

    if c[EMAIL] and not re.fullmatch(r"[^@\s]+@[^@\s]+", c[EMAIL]):
        erros.append("E-mail inválido")

    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", c[CPF]))
    if c[CPF] and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    if c[CEP] and not re.fullmatch(r"\d{5}-\d{3}", c[CEP]):
        erros.append("CEP deve estar no formato 00000-000")

    data_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", c[DATA_NASCIMENTO]))
    if c[DATA_NASCIMENTO] and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not _cpf_valido(c[CPF]):
        erros.append("CPF inválido")

    if data_no_formato and not _data_existe(c[DATA_NASCIMENTO]):
        erros.append("Data de nascimento inválida")

    return erros


def _valor_positivo(valor: str) -> bool:
    numero = valor.replace("R$", "").strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})*,\d{2}", numero):
        return int(re.sub(r"\D", "", numero)) > 0
    if re.fullmatch(r"\d+", numero):
        return int(numero) > 0
    return False


def _cpf_valido(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in re.sub(r"\D", "", cpf)]
    return digitos[9] == _digito_verificador(digitos[:9], 10) and digitos[10] == _digito_verificador(digitos[:10], 11)


def _digito_verificador(digitos: list, peso_inicial: int) -> int:
    soma = sum(digito * peso for digito, peso in zip(digitos, range(peso_inicial, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def _data_existe(data: str) -> bool:
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _oficio(c: dict, formulario: str) -> str:
    if formulario == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa = c[PROGRAMA]
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {c[TIPO_AUXILIO]}"
        programa = f"{c[PROGRAMA]} - {c[NIVEL]}"

    linhas = [
        f"Interessada(o): {c[NOME]} - {c[NUSP]}",
        f"E-mail: {c[EMAIL]}",
        f"Assunto: {assunto}",
        f"Programa: {programa}",
        "",
        f"A CCP-{c[PROGRAMA]} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c[EVENTO]}",
        f"Período: {c[PERIODO]}",
        f"Local: {c[CIDADE_EVENTO]} - {c[ESTADO_EVENTO]} - {c[PAIS_EVENTO]}",
    ]
    if c[LINK]:
        linhas.append(f"Link do evento: {c[LINK]}")
    linhas.extend([
        f"Apresentação de trabalho: {c[APRESENTACAO]}",
        f"Valor solicitado: {_moeda(int(re.sub(r'\D', '', c[VALOR])))}",
        f"Detalhamento: {c[DETALHAMENTO]}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c[LOGRADOURO]}, {c[NUMERO]}",
    ])
    if c[COMPLEMENTO]:
        linhas.append(f"Complemento: {c[COMPLEMENTO]}")
    linhas.extend([
        f"CEP: {c[CEP]}",
        f"{c[BAIRRO]}, {c[CIDADE]} - {c[ESTADO]}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c[DATA_NASCIMENTO]}",
        f"CPF: {c[CPF]}",
        f"RG / RNM: {c[RG_RNM]}",
        f"Banco: {c[BANCO]}",
        f"Agência: {c[AGENCIA]}",
        f"Conta: {c[CONTA]}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


def _moeda(centavos: int) -> str:
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"
