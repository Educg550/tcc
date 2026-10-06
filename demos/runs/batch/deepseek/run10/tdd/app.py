from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent

app = FastAPI()


@app.get("/")
def raiz():
    return FileResponse(BASE / "index.html", media_type="text/html")


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    dados = await request.json()
    erros = validar(dados)
    if erros:
        return JSONResponse({"erros": erros, "oficio": ""})
    return JSONResponse({"erros": [], "oficio": gerar_oficio(dados)})


app.mount("/", StaticFiles(directory=BASE, html=True), name="static")


OBRIGATORIOS = [
    "nome_completo",
    "n_usp",
    "programa",
    "email",
    "nome_evento",
    "periodo",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao_trabalho",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "nome_banco",
    "agencia",
    "conta",
]


def _cpf_valido(cpf):
    digitos = "".join(c for c in cpf if c.isdigit())
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(digitos[tamanho]):
            return False
    return True


def _data_valida(data):
    try:
        dia, mes, ano = int(data[0:2]), int(data[3:5]), int(data[6:10])
    except ValueError:
        return False
    if mes < 1 or mes > 12 or dia < 1:
        return False
    dias = [31, 29 if (ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)) else 28,
            31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return dia <= dias[mes - 1]


def validar(dados):
    erros = []
    aba = dados.get("aba", "alunos")
    campos = list(OBRIGATORIOS)
    if aba == "alunos":
        campos += ["nivel", "tipo_auxilio"]

    if any(not str(dados.get(c, "")).strip() for c in campos):
        erros.append("Preencha todos os campos")

    n_usp = str(dados.get("n_usp", ""))
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = str(dados.get("agencia", ""))
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = str(dados.get("valor_solicitado", ""))
    if valor:
        digitos = "".join(c for c in valor if c.isdigit())
        if not digitos or int(digitos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = str(dados.get("email", ""))
    if email:
        partes = email.split("@")
        if len(partes) != 2 or not partes[0] or "." not in partes[1] or not partes[1]:
            erros.append("E-mail inválido")

    cpf = str(dados.get("cpf", ""))
    if cpf:
        import re
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = str(dados.get("cep", ""))
    if cep:
        import re
        if not re.fullmatch(r"\d{5}-\d{3}", cep):
            erros.append("CEP deve estar no formato 00000-000")

    data = str(dados.get("data_nascimento", ""))
    if data:
        import re
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados):
    aba = dados.get("aba", "alunos")
    if aba == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {dados['programa']}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {dados['tipo_auxilio']}"
        programa = f"Programa: {dados['programa']} - {dados['nivel']}"

    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        assunto,
        programa,
        "",
        f"A CCP-{dados['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if str(dados.get("link_evento", "")).strip():
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao_trabalho']}",
        f"Valor solicitado: {dados['valor_solicitado']}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if str(dados.get("complemento", "")).strip():
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg']}",
        f"Banco: {dados['nome_banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)
