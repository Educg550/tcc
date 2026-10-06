import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")

OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email",
    "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
    "valor", "detalhamento", "apresentacao",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade", "estado",
    "cpf", "rg_rnm", "banco", "agencia", "conta",
]


def digitos(texto):
    return re.sub(r"\D", "", str(texto or ""))


def so_digitos(texto):
    return bool(texto) and texto.isdigit()


def cpf_valido(d):
    if len(set(d)) == 1:
        return False
    for i in (9, 10):
        soma = sum(int(d[n]) * (i + 1 - n) for n in range(i))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if esperado != int(d[i]):
            return False
    return True


def data_existe(d):
    try:
        date(int(d[4:8]), int(d[2:4]), int(d[0:2]))
    except ValueError:
        return False
    return True


def formatar_moeda(centavos):
    reais, cent = divmod(centavos, 100)
    return "R$ " + f"{reais:,}".replace(",", ".") + f",{cent:02d}"


def formatar_cpf(texto):
    d = digitos(texto)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def formatar_cep(texto):
    d = digitos(texto)
    return f"{d[:5]}-{d[5:8]}"


def formatar_data(texto):
    d = digitos(texto)
    return f"{d[:2]}/{d[2:4]}/{d[4:8]}"


def validar(dados, alunos):
    def campo(nome):
        return str(dados.get(nome) or "").strip()

    erros = []
    obrigatorios = OBRIGATORIOS + (["nivel", "tipo_auxilio"] if alunos else [])
    if any(not campo(nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campo("n_usp")
    if n_usp and not so_digitos(n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = campo("agencia")
    if agencia and not so_digitos(agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = campo("valor")
    if valor:
        d = digitos(valor)
        if not d or int(d) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = campo("email")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = campo("cpf")
    if cpf:
        d = digitos(cpf)
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}", cpf) or len(d) != 11:
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(d):
            erros.append("CPF inválido")

    cep = campo("cep")
    if cep:
        d = digitos(cep)
        if not re.fullmatch(r"\d{5}-\d{3}|\d{8}", cep) or len(d) != 8:
            erros.append("CEP deve estar no formato 00000-000")

    nascimento = campo("data_nascimento")
    if nascimento:
        d = digitos(nascimento)
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}|\d{8}", nascimento) or len(d) != 8:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_existe(d):
            erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(dados, alunos):
    def campo(nome):
        return str(dados.get(nome) or "").strip()

    programa = campo("programa")
    if alunos:
        assunto = campo("tipo_auxilio")
        linha_programa = f"Programa: {programa} - {campo('nivel')}"
    else:
        assunto = "Verba do programa"
        linha_programa = f"Programa: {programa}"

    linhas = [
        f"Interessada(o): {campo('nome')} - {campo('n_usp')}",
        f"E-mail: {campo('email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        linha_programa,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {campo('evento')}",
        f"Período: {campo('periodo')}",
        f"Local: {campo('cidade_evento')} - {campo('estado_evento')} - {campo('pais_evento')}",
    ]

    if campo("link_evento"):
        linhas.append(f"Link do evento: {campo('link_evento')}")

    linhas += [
        f"Apresentação de trabalho: {campo('apresentacao')}",
        f"Valor solicitado: {formatar_moeda(int(digitos(campo('valor'))))}",
        f"Detalhamento: {campo('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{campo('logradouro')}, {campo('numero')}",
    ]

    if campo("complemento"):
        linhas.append(f"Complemento: {campo('complemento')}")

    linhas += [
        f"CEP: {formatar_cep(campo('cep'))}",
        f"{campo('bairro')}, {campo('cidade')} - {campo('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {formatar_data(campo('data_nascimento'))}",
        f"CPF: {formatar_cpf(campo('cpf'))}",
        f"RG / RNM: {campo('rg_rnm')}",
        f"Banco: {campo('banco')}",
        f"Agência: {campo('agencia')}",
        f"Conta: {campo('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]

    return "\n".join(linhas)


@app.get("/")
def pagina_inicial():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def estilos():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


@app.post("/solicitacao/{aba}")
def solicitar(aba: str, dados: dict):
    alunos = aba == "alunos"
    erros = validar(dados, alunos)
    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})
    return {"oficio": gerar_oficio(dados, alunos)}
