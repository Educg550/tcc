import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).resolve().parent

app = FastAPI()


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html", media_type="text/html; charset=utf-8")


@app.get("/style.css")
def estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css; charset=utf-8")


@app.get("/app.js")
def script():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")

CAMPOS_OBRIGATORIOS = [
    "aba",
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "data_nascimento",
    "logradouro",
    "numero",
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
CAMPOS_DE_ALUNOS = ["nivel", "tipo_auxilio"]

FORMATO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
FORMATO_CEP = re.compile(r"\d{5}-\d{3}")
FORMATO_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")


def texto(dados, chave):
    valor = dados.get(chave)
    return "" if valor is None else str(valor).strip()


def valor_em_centavos(valor):
    numero = valor.replace("R$", "").strip()
    if "," in numero:
        inteiro, _, centavos = numero.partition(",")
        inteiro = inteiro.replace(".", "")
        if not (inteiro.isdigit() and len(centavos) == 2 and centavos.isdigit()):
            return None
        return int(inteiro) * 100 + int(centavos)
    if not numero.isdigit():
        return None
    return int(numero)


def formatar_valor(centavos):
    inteiro, resto = divmod(centavos, 100)
    return "R$ " + f"{inteiro:,}".replace(",", ".") + f",{resto:02d}"


def digito_verificador(digitos):
    soma = sum(digito * peso for digito, peso in zip(digitos, range(len(digitos) + 1, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf):
    digitos = [int(caractere) for caractere in re.sub(r"\D", "", cpf)]
    return (
        digitos[9] == digito_verificador(digitos[:9])
        and digitos[10] == digito_verificador(digitos[:10])
    )


def data_valida(valor):
    try:
        datetime.strptime(valor, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def validar(dados):
    erros = []
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if texto(dados, "aba") == "alunos":
        obrigatorios += CAMPOS_DE_ALUNOS
    if any(texto(dados, campo) == "" for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "numero_agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "valor_solicitado")
    centavos = valor_em_centavos(valor) if valor else None
    if valor and (centavos is None or centavos <= 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "email")
    if email and ("@" not in email or not email.rsplit("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf = texto(dados, "cpf")
    if cpf and not FORMATO_CPF.fullmatch(cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = texto(dados, "cep")
    if cep and not FORMATO_CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "data_nascimento")
    if nascimento and not FORMATO_DATA.fullmatch(nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros, centavos


def construir_oficio(dados, centavos):
    programa = texto(dados, "programa")
    if texto(dados, "aba") == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {programa}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {texto(dados, 'tipo_auxilio')}"
        linha_programa = f"Programa: {programa} - {texto(dados, 'nivel')}"
    apresentacao = texto(dados, "apresentacao") or "Pôster"

    linhas = [
        f"Interessada(o): {texto(dados, 'nome_completo')} - {texto(dados, 'n_usp')}",
        f"E-mail: {texto(dados, 'email')}",
        assunto,
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {texto(dados, 'nome_evento')}",
        f"Período: {texto(dados, 'periodo_evento')}",
        f"Local: {texto(dados, 'cidade_evento')} - {texto(dados, 'estado_evento')} - {texto(dados, 'pais_evento')}",
    ]
    link = texto(dados, "link_evento")
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {apresentacao}",
        f"Valor solicitado: {formatar_valor(centavos)}",
        f"Detalhamento: {texto(dados, 'detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{texto(dados, 'logradouro')}, {texto(dados, 'numero')}",
    ]
    complemento = texto(dados, "complemento")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {texto(dados, 'cep')}",
        f"{texto(dados, 'bairro')}, {texto(dados, 'cidade')} - {texto(dados, 'estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {texto(dados, 'data_nascimento')}",
        f"CPF: {texto(dados, 'cpf')}",
        f"RG / RNM: {texto(dados, 'rg_rnm')}",
        f"Banco: {texto(dados, 'nome_banco')}",
        f"Agência: {texto(dados, 'numero_agencia')}",
        f"Conta: {texto(dados, 'numero_conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    dados = await request.()
    erros, centavos = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": construir_oficio(dados, centavos)}
