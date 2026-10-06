import re
from datetime import date

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

CAMPOS_COMUNS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


@app.get("/")
def pagina_inicial():
    return FileResponse("index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")


def _cpf_valido(cpf):
    digitos = [int(c) for c in cpf if c.isdigit()]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        verificador = (soma * 10) % 11 % 10
        if verificador != digitos[posicao]:
            return False
    return True


def _valor_em_centavos(valor):
    digitos = re.sub(r"\D", "", valor)
    return int(digitos) if digitos else 0


def _formatar_valor(valor):
    centavos = _valor_em_centavos(valor)
    reais = centavos // 100
    return f"R$ {reais:,}".replace(",", ".") + f",{centavos % 100:02d}"


def _validar(dados):
    campos = list(CAMPOS_COMUNS)
    if dados.get("aba") == "alunos":
        campos += ["nivel", "tipo_auxilio"]

    def valor_de(campo):
        return (dados.get(campo) or "").strip()

    erros = []

    if any(not valor_de(campo) for campo in campos):
        erros.append("Preencha todos os campos")

    n_usp = valor_de("n_usp")
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = valor_de("agencia")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = valor_de("valor")
    if valor and _valor_em_centavos(valor) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")

    email = valor_de("email")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = valor_de("cpf")
    cpf_no_formato = False
    if cpf:
        if re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf):
            cpf_no_formato = True
        else:
            erros.append("CPF deve estar no formato 000.000.000-00")

    cep = valor_de("cep")
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = valor_de("data_nascimento")
    nascimento_no_formato = False
    if nascimento:
        if re.match(r"^\d{2}/\d{2}/\d{4}$", nascimento):
            nascimento_no_formato = True
        else:
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf_no_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if nascimento_no_formato:
        try:
            date(int(nascimento[6:10]), int(nascimento[3:5]), int(nascimento[0:2]))
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def _gerar_oficio(dados):
    def valor_de(campo):
        return (dados.get(campo) or "").strip()

    aba = dados.get("aba")
    programa = valor_de("programa")

    linhas = [
        f"Interessada(o): {valor_de('nome')} - {valor_de('n_usp')}",
        f"E-mail: {valor_de('email')}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {valor_de('tipo_auxilio')}")
        linhas.append(f"Programa: {programa} - {valor_de('nivel')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")

    linhas += [
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {valor_de('evento')}",
        f"Período: {valor_de('periodo')}",
        f"Local: {valor_de('cidade_evento')} - {valor_de('estado_evento')} - {valor_de('pais_evento')}",
    ]
    if valor_de("link_evento"):
        linhas.append(f"Link do evento: {valor_de('link_evento')}")
    linhas += [
        f"Apresentação de trabalho: {valor_de('apresentacao')}",
        f"Valor solicitado: {_formatar_valor(valor_de('valor'))}",
        f"Detalhamento: {valor_de('detalhamento')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{valor_de('logradouro')}, {valor_de('numero')}",
    ]
    if valor_de("complemento"):
        linhas.append(f"Complemento: {valor_de('complemento')}")
    linhas += [
        f"CEP: {valor_de('cep')}",
        f"{valor_de('bairro')}, {valor_de('cidade')} - {valor_de('estado')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {valor_de('data_nascimento')}",
        f"CPF: {valor_de('cpf')}",
        f"RG / RNM: {valor_de('rg')}",
        f"Banco: {valor_de('banco')}",
        f"Agência: {valor_de('agencia')}",
        f"Conta: {valor_de('conta')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/submit")
def enviar(dados: dict):
    if dados.get("aba") not in ("alunos", "docentes"):
        return {"ok": False, "erros": ["Solicitação inválida"]}
    erros = _validar(dados)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": _gerar_oficio(dados)}
