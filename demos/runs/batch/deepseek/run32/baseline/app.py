from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
import re
import datetime

app = FastAPI()


def cpf_valido(cpf):
    nums = [int(c) for c in cpf if c.isdigit()]
    if len(nums) != 11 or len(set(nums)) == 1:
        return False
    for i in range(9, 11):
        soma = sum(nums[j] * (i + 1 - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != nums[i]:
            return False
    return True


def data_valida(s):
    try:
        datetime.datetime.strptime(s, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def montar_oficio(dados):
    def g(k):
        return (dados.get(k) or "").strip()

    aba = dados.get("aba", "alunos")
    linhas = []
    linhas.append(f"Interessada(o): {g('nome')} - {g('nusp')}")
    linhas.append(f"E-mail: {g('email')}")
    if aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {g('programa')}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {g('tipo')}")
        linhas.append(f"Programa: {g('programa')} - {g('nivel')}")
    linhas.append("")
    linhas.append(
        f"A CCP-{g('programa')} aprovou na data de hoje, a solicitação de auxílio financeiro para a"
    )
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {g('evento')}")
    linhas.append(f"Período: {g('periodo')}")
    linhas.append(
        f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}"
    )
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas.append(f"Apresentação de trabalho: {g('apresentacao')}")
    linhas.append(f"Valor solicitado: {g('valor')}")
    linhas.append(f"Detalhamento: {g('detalhamento')}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{g('logradouro')}, {g('numero')}")
    if g("complemento"):
        linhas.append(f"Complemento: {g('complemento')}")
    linhas.append(f"CEP: {g('cep')}")
    linhas.append(f"{g('bairro')}, {g('cidade')} - {g('estado')}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {g('nascimento')}")
    linhas.append(f"CPF: {g('cpf')}")
    linhas.append(f"RG / RNM: {g('rg')}")
    linhas.append(f"Banco: {g('banco')}")
    linhas.append(f"Agência: {g('agencia')}")
    linhas.append(f"Conta: {g('conta')}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/solicitar")
def solicitar(dados: dict = Body(...)):
    aba = dados.get("aba", "alunos")

    def g(k):
        return (dados.get(k) or "").strip()

    obrigatorios = [
        "nome", "nusp", "programa", "email", "evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor",
        "detalhamento", "apresentacao", "nascimento", "logradouro",
        "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
        "banco", "agencia", "conta",
    ]
    if aba != "docentes":
        obrigatorios += ["nivel", "tipo"]

    erros = []
    if any(not g(campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    if g("nusp") and not re.fullmatch(r"\d+", g("nusp")):
        erros.append("N. USP deve conter apenas números")

    if g("agencia") and not re.fullmatch(r"\d+", g("agencia")):
        erros.append("Número da agência deve conter apenas números")

    if g("valor"):
        digitos = re.sub(r"\D", "", g("valor"))
        if not digitos or int(digitos) <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    if g("email") and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", g("email")):
        erros.append("E-mail inválido")

    cpf = g("cpf")
    cpf_formato = bool(cpf) and bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    cep = g("cep")
    nasc = g("nascimento")
    data_formato = bool(nasc) and bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nasc))

    if cpf and not cpf_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")
    if nasc and not data_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")
    if data_formato and not data_valida(nasc):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"erros": erros, "oficio": None}

    return {"erros": [], "oficio": montar_oficio(dados)}


app.mount("/", StaticFiles(directory=".", html=True), name="static")
