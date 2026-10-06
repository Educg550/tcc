import re

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

RE_OBRIGATORIOS = [
    "nome", "nusp", "programa", "email", "nomeEvento", "periodoEvento",
    "cidadeEvento", "estadoEvento", "paisEvento", "valor", "detalhamento",
    "apresentacao", "dataNascimento", "logradouro", "numero", "bairro",
    "cep", "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]


def cpf_valido(cpf: str) -> bool:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for i, pos in ((9, 10), (10, 11)):
        total = sum(int(digitos[j]) * (pos - j) for j in range(i))
        if int(digitos[i]) != (11 - (total % 11)) % 11:
            return False
    return True


def valida(dados: dict) -> list:
    erros = []
    tipo = dados.get("tipo", "alunos")
    obrigatorios = RE_OBRIGATORIOS
    if tipo == "alunos":
        obrigatorios = ["nivel", "tipoAuxilio"] + list(obrigatorios)
    if any(not str(dados.get(campo, "")).strip() for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = dados.get("nusp", "")
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("agencia", "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = dados.get("valor", "")
    if valor and not (valor.isdigit() and int(valor) > 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = dados.get("email", "")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = dados.get("cpf", "")
    if cpf:
        if re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            if not cpf_valido(cpf):
                erros.append("CPF inválido")
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")

    cep = dados.get("cep", "")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = dados.get("dataNascimento", "")
    if data:
        m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
        if not m:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        else:
            dia, mes, ano = (int(g) for g in m.groups())
            dias_no_mes = [31, 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if not (1 <= mes <= 12 and 1 <= dia <= dias_no_mes[mes - 1]):
                erros.append("Data de nascimento inválida")

    return erros


def gera_oficio(dados: dict) -> str:
    tipo = dados.get("tipo", "alunos")
    valor = int(dados["valor"])
    valor_txt = "R$ " + f"{valor // 100}.{valor % 100:02d}".replace(",", ".")
    partes = valor_txt[3:].split(".")
    inteiro, centavos = int(partes[0]), partes[1]
    txt = str(inteiro)
    milhar = ""
    while len(txt) > 3:
        milhar = "." + txt[-3:] + milhar
        txt = txt[:-3]
    valor_fmt = f"R$ {txt}{milhar},{centavos}"

    if tipo == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipoAuxilio']}"
        programa_linha = f"Programa: {dados['programa']} - {dados['nivel']}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = f"Programa: {dados['programa']}"

    linhas = [
        f"Interessada(o): {dados['nome']} - {dados['nusp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa_linha,
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nomeEvento']}",
        f"Período: {dados['periodoEvento']}",
        f"Local: {dados['cidadeEvento']} - {dados['estadoEvento']} - {dados['paisEvento']}",
    ]
    if dados.get("linkEvento", "").strip():
        linhas.append(f"Link do evento: {dados['linkEvento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao']}",
        f"Valor solicitado: {valor_fmt}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados.get("complemento", "").strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['dataNascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/solicitar")
async def solicitar(dados: dict):
    erros = valida(dados)
    if erros:
        return JSONResponse({"errors": erros})
    return {"errors": [], "oficio": gera_oficio(dados)}


@app.get("/")
async def raiz():
    return FileResponse("index.html")


app.mount("/", StaticFiles(directory=".", html=True), name="static")
