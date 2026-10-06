import re
from datetime import date

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def index():
    return FileResponse("index.html", media_type="text/html")


@app.get("/style.css")
def style():
    return FileResponse("style.css", media_type="text/css")


@app.get("/app.js")
def app_js():
    return FileResponse("app.js", media_type="application/javascript")


CAMPOS_BASE = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
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


def cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False

    def dv(digs):
        soma = sum(int(d) * peso for d, peso in zip(digs, range(len(digs) + 1, 1, -1)))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    d1 = dv(digitos[:9])
    d2 = dv(digitos[:9] + d1)
    return digitos[9:] == d1 + d2


def validar(dados, aba):
    obrigatorios = list(CAMPOS_BASE)
    if aba == "alunos":
        obrigatorios = obrigatorios + ["NÍVEL", "TIPO DE AUXÍLIO"]

    erros = []
    faltando = False
    for campo in obrigatorios:
        valor = dados.get(campo)
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            faltando = True
    if faltando:
        erros.append("Preencha todos os campos")

    n_usp = dados.get("N. USP")
    if n_usp and not re.fullmatch(r"\d+", str(n_usp)):
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("NÚMERO DA AGÊNCIA")
    if agencia and not re.fullmatch(r"\d+", str(agencia)):
        erros.append("Número da agência deve conter apenas números")

    valor_solicitado = dados.get("VALOR SOLICITADO (R$)")
    if valor_solicitado is not None and valor_solicitado != "":
        try:
            numero = float(valor_solicitado)
        except (TypeError, ValueError):
            numero = -1
        if numero <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("E-MAIL")
    if email:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            erros.append("E-mail inválido")

    cpf = dados.get("CPF (SEPARADOS POR PONTOS E TRAÇO)")
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = dados.get("CEP")
    if cep:
        if not re.fullmatch(r"\d{5}-\d{3}", cep):
            erros.append("CEP deve estar no formato 00000-000")

    data_nasc = dados.get("DATA DE NASCIMENTO")
    if data_nasc:
        m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data_nasc)
        if not m:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def formata_valor(centavos):
    centavos = int(float(centavos))
    reais = centavos // 100
    resto = centavos % 100
    reais_str = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_str},{resto:02d}"


def gerar_oficio(d, aba):
    if aba == "alunos":
        assunto = f"Solicitação de Auxílio Financeiro - {d['TIPO DE AUXÍLIO']}"
        programa_linha = f"Programa: {d['PROGRAMA']} - {d['NÍVEL']}"
    else:
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = f"Programa: {d['PROGRAMA']}"

    linhas = [
        f"Interessada(o): {d['NOME COMPLETO - SEM ABREVIAR']} - {d['N. USP']}",
        f"E-mail: {d['E-MAIL']}",
        f"Assunto: {assunto}",
        programa_linha,
        "",
        f"A CCP-{d['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {d['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {d['CIDADE DO EVENTO, EXAME OU DEFESA']} - {d['ESTADO DO EVENTO, EXAME OU DEFESA']} - {d['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]

    link = d.get("LINK DO EVENTO, EXAME OU DEFESA") or ""
    if link:
        linhas.append(f"Link do evento: {link}")

    linhas.append(f"Apresentação de trabalho: {d['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}")
    linhas.append(f"Valor solicitado: {formata_valor(d['VALOR SOLICITADO (R$)'])}")
    linhas.append(f"Detalhamento: {d['DETALHAMENTO DO PEDIDO']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{d['LOGRADOURO']}, {d['NÚMERO']}")

    complemento = d.get("COMPLEMENTO") or ""
    if complemento:
        linhas.append(f"Complemento: {complemento}")

    linhas.append(f"CEP: {d['CEP']}")
    linhas.append(f"{d['BAIRRO']}, {d['CIDADE']} - {d['ESTADO']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {d['DATA DE NASCIMENTO']}")
    linhas.append(f"CPF: {d['CPF (SEPARADOS POR PONTOS E TRAÇO)']}")
    linhas.append(f"RG / RNM: {d['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}")
    linhas.append(f"Banco: {d['NOME DO BANCO']}")
    linhas.append(f"Agência: {d['NÚMERO DA AGÊNCIA']}")
    linhas.append(f"Conta: {d['NÚMERO DA CONTA']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


def processar(dados, aba):
    erros = validar(dados, aba)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados, aba)}


@app.post("/alunos")
def alunos(dados: dict = Body(...)):
    return processar(dados, "alunos")


@app.post("/docentes")
def docentes(dados: dict = Body(...)):
    return processar(dados, "docentes")
