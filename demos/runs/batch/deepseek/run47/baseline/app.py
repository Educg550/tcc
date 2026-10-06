import re
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

OBRIGATORIOS = {
    "alunos": [
        "nome",
        "n_usp",
        "programa",
        "nivel",
        "tipo_auxilio",
        "email",
        "evento",
        "periodo",
        "cidade_evento",
        "estado_evento",
        "pais_evento",
        "valor",
        "detalhamento",
        "apresentacao",
        "data_nascimento",
        "logradouro",
        "numero",
        "bairro",
        "cep",
        "cidade",
        "estado",
        "cpf",
        "rg",
        "banco",
        "agencia",
        "conta",
    ],
    "docentes": [
        "nome",
        "n_usp",
        "programa",
        "email",
        "evento",
        "periodo",
        "cidade_evento",
        "estado_evento",
        "pais_evento",
        "valor",
        "detalhamento",
        "apresentacao",
        "data_nascimento",
        "logradouro",
        "numero",
        "bairro",
        "cep",
        "cidade",
        "estado",
        "cpf",
        "rg",
        "banco",
        "agencia",
        "conta",
    ],
}


def cpf_valido(cpf):
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != digitos[posicao]:
            return False
    return True


def data_valida(data):
    dia, mes, ano = (int(parte) for parte in data.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def formata_moeda(valor):
    digitos = re.sub(r"\D", "", valor) or "0"
    centavos = int(digitos)
    reais = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {reais},{centavos % 100:02d}"


def validar(aba, campos):
    def valor(chave):
        return (campos.get(chave) or "").strip()

    erros = []

    if any(not valor(chave) for chave in OBRIGATORIOS[aba]):
        erros.append("Preencha todos os campos")

    if valor("n_usp") and not re.fullmatch(r"\d+", valor("n_usp")):
        erros.append("N. USP deve conter apenas números")

    if valor("agencia") and not re.fullmatch(r"\d+", valor("agencia")):
        erros.append("Número da agência deve conter apenas números")

    if valor("valor") and not re.search(r"[1-9]", re.sub(r"\D", "", valor("valor"))):
        erros.append("Valor solicitado deve ser maior que 0")

    email = valor("email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = valor("cpf")
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = valor("cep")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = valor("data_nascimento")
    nascimento_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if nascimento_no_formato and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    return erros


def montar_oficio(aba, campos):
    def valor(chave):
        return (campos.get(chave) or "").strip()

    linhas = [
        f"Interessada(o): {valor('nome')} - {valor('n_usp')}",
        f"E-mail: {valor('email')}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {valor('tipo_auxilio')}")
        linhas.append(f"Programa: {valor('programa')} - {valor('nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {valor('programa')}")

    linhas += [
        "",
        f"A CCP-{valor('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {valor('evento')}",
        f"Período: {valor('periodo')}",
        f"Local: {valor('cidade_evento')} - {valor('estado_evento')} - {valor('pais_evento')}",
    ]
    if valor("link_evento"):
        linhas.append(f"Link do evento: {valor('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {valor('apresentacao')}",
        f"Valor solicitado: {formata_moeda(valor('valor'))}",
        f"Detalhamento: {valor('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{valor('logradouro')}, {valor('numero')}",
    ]
    if valor("complemento"):
        linhas.append(f"Complemento: {valor('complemento')}")
    linhas += [
        f"CEP: {valor('cep')}",
        f"{valor('bairro')}, {valor('cidade')} - {valor('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {valor('data_nascimento')}",
        f"CPF: {valor('cpf')}",
        f"RG / RNM: {valor('rg')}",
        f"Banco: {valor('banco')}",
        f"Agência: {valor('agencia')}",
        f"Conta: {valor('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(payload: dict = Body(...)):
    aba = payload.get("aba")
    if aba not in OBRIGATORIOS:
        aba = "alunos"

    campos = {chave: str(valor).strip() for chave, valor in (payload.get("campos") or {}).items()}

    erros = validar(aba, campos)
    if erros:
        return {"erros": erros}
    return {"oficio": montar_oficio(aba, campos)}


app.mount("/", StaticFiles(directory=Path(__file__).parent, html=True), name="estaticos")
