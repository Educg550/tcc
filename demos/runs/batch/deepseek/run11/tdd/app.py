import datetime
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")


@app.get("/")
def pagina():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilo():
    return FileResponse(BASE / "style.css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js")


OBRIGATORIOS = [
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
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(digitos[n]) * (i + 1 - n) for n in range(i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[i]):
            return False
    return True


def validar(aba, campos):
    erros = []
    obrigatorios = list(OBRIGATORIOS)
    if aba == "ALUNOS":
        obrigatorios += ["NÍVEL", "TIPO DE AUXÍLIO"]

    valores = {k: str(campos.get(k, "") or "").strip() for k in obrigatorios}
    if any(not v for v in valores.values()):
        erros.append("Preencha todos os campos")

    if valores["N. USP"] and not re.fullmatch(r"[0-9]+", valores["N. USP"]):
        erros.append("N. USP deve conter apenas números")

    if valores["NÚMERO DA AGÊNCIA"] and not re.fullmatch(r"[0-9]+", valores["NÚMERO DA AGÊNCIA"]):
        erros.append("Número da agência deve conter apenas números")

    if valores["VALOR SOLICITADO (R$)"]:
        digitos = re.sub(r"\D", "", valores["VALOR SOLICITADO (R$)"])
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if valores["E-MAIL"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valores["E-MAIL"]):
        erros.append("E-mail inválido")

    cpf = valores["CPF (SEPARADOS POR PONTOS E TRAÇO)"]
    if cpf:
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = valores["CEP"]
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = valores["DATA DE NASCIMENTO"]
    if data:
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(p) for p in data.split("/"))
            try:
                datetime.date(ano, mes, dia)
            except ValueError:
                erros.append("Data de nascimento inválida")

    return erros


def formatar_moeda(valor):
    digitos = re.sub(r"\D", "", valor) or "0"
    centavos = int(digitos)
    reais = centavos // 100
    cent = centavos % 100
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{cent:02d}"


def gerar_oficio(aba, campos):
    g = campos.get
    if aba == "ALUNOS":
        assunto = g("TIPO DE AUXÍLIO", "")
        nivel = " - " + g("NÍVEL", "")
    else:
        assunto = "Verba do programa"
        nivel = ""

    link = g("LINK DO EVENTO, EXAME OU DEFESA", "")
    complemento = g("COMPLEMENTO", "")

    linhas = [
        f"Interessada(o): {g('NOME COMPLETO - SEM ABREVIAR', '')} - {g('N. USP', '')}",
        f"E-mail: {g('E-MAIL', '')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        f"Programa: {g('PROGRAMA', '')}{nivel}",
        "",
        f"A CCP-{g('PROGRAMA', '')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {g('NOME DO EVENTO / BANCA DE EXAME OU DEFESA', '')}",
        f"Período: {g('PERÍODO DO EVENTO, EXAME OU DEFESA', '')}",
        f"Local: {g('CIDADE DO EVENTO, EXAME OU DEFESA', '')} - {g('ESTADO DO EVENTO, EXAME OU DEFESA', '')} - {g('PAÍS DO EVENTO, EXAME OU DEFESA', '')}",
    ]
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {g('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', '')}",
        f"Valor solicitado: {formatar_moeda(g('VALOR SOLICITADO (R$)', ''))}",
        f"Detalhamento: {g('DETALHAMENTO DO PEDIDO', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{g('LOGRADOURO', '')}, {g('NÚMERO', '')}",
    ]
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {g('CEP', '')}",
        f"{g('BAIRRO', '')}, {g('CIDADE', '')} - {g('ESTADO', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {g('DATA DE NASCIMENTO', '')}",
        f"CPF: {g('CPF (SEPARADOS POR PONTOS E TRAÇO)', '')}",
        f"RG / RNM: {g('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', '')}",
        f"Banco: {g('NOME DO BANCO', '')}",
        f"Agência: {g('NÚMERO DA AGÊNCIA', '')}",
        f"Conta: {g('NÚMERO DA CONTA', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitacao")
def solicitar(dados: dict):
    aba = dados.get("aba", "ALUNOS")
    campos = dados.get("campos") or {}
    erros = validar(aba, campos)
    if erros:
        return {"erros": erros}
    return {"erros": [], "oficio": gerar_oficio(aba, campos)}
