import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE = Path(__file__).parent

OBRIGATORIOS = [
    "nome_completo", "n_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep", "cidade",
    "estado", "cpf", "rg", "banco", "agencia", "conta",
]
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
CEP = re.compile(r"\d{5}-\d{3}")
DATA = re.compile(r"\d{2}/\d{2}/\d{4}")


def campo(dados, nome):
    return str(dados.get(nome) or "").strip()


def perfil_de(dados):
    perfil = campo(dados, "perfil").lower()
    if perfil in ("alunos", "docentes"):
        return perfil
    if campo(dados, "nivel") or campo(dados, "tipo_auxilio"):
        return "alunos"
    return "docentes"


def cpf_valido(cpf):
    digitos = [int(d) for d in re.sub(r"\D", "", cpf)]
    for n in (9, 10):
        if sum(digitos[i] * (n + 1 - i) for i in range(n)) * 10 % 11 % 10 != digitos[n]:
            return False
    return True


def data_valida(data):
    try:
        dia, mes, ano = (int(parte) for parte in data.split("/"))
        date(ano, mes, dia)
        return True
    except ValueError:
        return False


def validar(dados):
    obrigatorios = list(OBRIGATORIOS)
    if perfil_de(dados) == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    n_usp = campo(dados, "n_usp")
    agencia = campo(dados, "agencia")
    valor = campo(dados, "valor_solicitado")
    centavos = re.sub(r"\D", "", valor)
    email = campo(dados, "email")
    cpf = campo(dados, "cpf")
    cep = campo(dados, "cep")
    nascimento = campo(dados, "data_nascimento")
    cpf_formatado = bool(CPF.fullmatch(cpf))
    nascimento_formatado = bool(DATA.fullmatch(nascimento))

    erros = []
    if any(not campo(dados, nome) for nome in obrigatorios):
        erros.append("Preencha todos os campos")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")
    if valor and (not centavos or int(centavos) <= 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if email and not EMAIL.fullmatch(email):
        erros.append("E-mail inválido")
    if cpf and not cpf_formatado:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if cep and not CEP.fullmatch(cep):
        erros.append("CEP deve estar no formato 00000-000")
    if nascimento and not nascimento_formatado:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf and cpf_formatado and not cpf_valido(cpf):
        erros.append("CPF inválido")
    if nascimento and nascimento_formatado and not data_valida(nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def formatar_valor(valor):
    centavos = int(re.sub(r"\D", "", valor) or 0)
    reais, resto = divmod(centavos, 100)
    milhar = "{:,}".format(reais).replace(",", ".")
    return f"R$ {milhar},{resto:02d}"


def gerar_oficio(dados):
    def g(nome):
        return campo(dados, nome)

    alunos = perfil_de(dados) == "alunos"
    assunto = g("tipo_auxilio") if alunos else "Verba do programa"
    linhas = [
        f"Interessada(o): {g('nome_completo')} - {g('n_usp')}",
        f"E-mail: {g('email')}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
    ]
    if alunos:
        linhas.append(f"Programa: {g('programa')} - {g('nivel')}")
    else:
        linhas.append(f"Programa: {g('programa')}")
    linhas += [
        "",
        f"A CCP-{g('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {g('nome_evento')}",
        f"Período: {g('periodo_evento')}",
        f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}",
    ]
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {g('apresentacao_trabalho')}",
        f"Valor solicitado: {formatar_valor(g('valor_solicitado'))}",
        f"Detalhamento: {g('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{g('logradouro')}, {g('numero')}",
    ]
    if g("complemento"):
        linhas.append(f"Complemento: {g('complemento')}")
    linhas += [
        f"CEP: {g('cep')}",
        f"{g('bairro')}, {g('cidade')} - {g('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {g('data_nascimento')}",
        f"CPF: {g('cpf')}",
        f"RG / RNM: {g('rg')}",
        f"Banco: {g('banco')}",
        f"Agência: {g('agencia')}",
        f"Conta: {g('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
async def solicitar(request: Request):
    try:
        dados = await request.json()
    except Exception:
        dados = dict(await request.form())
    if not isinstance(dados, dict):
        dados = {}
    erros = validar(dados)
    if erros:
        return {"erros": erros, "oficio": None}
    return {"erros": [], "oficio": gerar_oficio(dados)}


app.mount("/", StaticFiles(directory=BASE, html=True), name="estaticos")
