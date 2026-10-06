import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

RAIZ = Path(__file__).parent

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}
SO_NA_ABA_ALUNOS = ("NÍVEL", "TIPO DE AUXÍLIO")

CAMPOS = [
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

app = FastAPI()


@app.get("/")
def pagina_inicial():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def roteiro():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    dados = await request.()
    erros = validar(dados)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(dados)}


def texto(dados, campo):
    valor = dados.get(campo)
    return "" if valor is None else str(valor).strip()


def valor_numero(texto_valor):
    normalizado = (
        texto_valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    )
    try:
        return float(normalizado)
    except ValueError:
        return 0.0


def formatar_moeda(numero):
    com_milhar = f"{numero:,.2f}"
    return "R$ " + com_milhar.replace(",", "@").replace(".", ",").replace("@", ".")


def cpf_conferem_dv(cpf):
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    resto = sum(digitos[i] * (10 - i) for i in range(9)) % 11
    if digitos[9] != (0 if resto < 2 else 11 - resto):
        return False
    resto = sum(digitos[i] * (11 - i) for i in range(10)) % 11
    return digitos[10] == (0 if resto < 2 else 11 - resto)


def data_existe(texto_data):
    try:
        datetime.strptime(texto_data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def validar(dados):
    perfil = texto(dados, "PERFIL").upper()
    erros = []

    obrigatorios = [
        campo
        for campo in CAMPOS
        if campo not in OPCIONAIS
        and not (perfil == "DOCENTES" and campo in SO_NA_ABA_ALUNOS)
    ]
    if any(not texto(dados, campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = texto(dados, "N. USP")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = texto(dados, "NÚMERO DA AGÊNCIA")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = texto(dados, "VALOR SOLICITADO (R$)")
    if valor and valor_numero(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = texto(dados, "E-MAIL")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = texto(dados, "CPF (SEPARADOS POR PONTOS E TRAÇO)")
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = texto(dados, "CEP")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = texto(dados, "DATA DE NASCIMENTO")
    data_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_no_formato and not cpf_conferem_dv(cpf):
        erros.append("CPF inválido")
    if nascimento and data_no_formato and not data_existe(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados):
    def g(campo):
        return texto(dados, campo)

    perfil = g("PERFIL").upper()
    programa = g("PROGRAMA")
    if perfil == "DOCENTES":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {programa}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {g('TIPO DE AUXÍLIO')}"
        linha_programa = f"Programa: {programa} - {g('NÍVEL')}"

    valor = formatar_moeda(valor_numero(g("VALOR SOLICITADO (R$)")))

    linhas = [
        f"Interessada(o): {g('NOME COMPLETO - SEM ABREVIAR')} - {g('N. USP')}",
        f"E-mail: {g('E-MAIL')}",
        assunto,
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {g('NOME DO EVENTO / BANCA DE EXAME OU DEFESA')}",
        f"Período: {g('PERÍODO DO EVENTO, EXAME OU DEFESA')}",
        "Local: "
        f"{g('CIDADE DO EVENTO, EXAME OU DEFESA')} - "
        f"{g('ESTADO DO EVENTO, EXAME OU DEFESA')} - "
        f"{g('PAÍS DO EVENTO, EXAME OU DEFESA')}",
    ]
    link = g("LINK DO EVENTO, EXAME OU DEFESA")
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas.extend(
        [
            f"Apresentação de trabalho: {g('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?')}",
            f"Valor solicitado: {valor}",
            f"Detalhamento: {g('DETALHAMENTO DO PEDIDO')}",
            "",
            "Endereço da(o) interessada(o)",
            f"{g('LOGRADOURO')}, {g('NÚMERO')}",
        ]
    )
    complemento = g("COMPLEMENTO")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.extend(
        [
            f"CEP: {g('CEP')}",
            f"{g('BAIRRO')}, {g('CIDADE')} - {g('ESTADO')}",
            "",
            "Dados para pagamento",
            f"Data de nascimento: {g('DATA DE NASCIMENTO')}",
            f"CPF: {g('CPF (SEPARADOS POR PONTOS E TRAÇO)')}",
            f"RG / RNM: {g('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)')}",
            f"Banco: {g('NOME DO BANCO')}",
            f"Agência: {g('NÚMERO DA AGÊNCIA')}",
            f"Conta: {g('NÚMERO DA CONTA')}",
            "",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ]
    )
    return "\n".join(linhas)
