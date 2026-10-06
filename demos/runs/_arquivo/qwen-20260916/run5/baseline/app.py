import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

CAMPOS_OBRIGATORIOS = [
    "nome", "nusp", "programa", "email", "nome_evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
]

CAMPOS_OBRIGATORIOS_ALUNOS = ["nivel", "tipo_auxilio"]

RE_DIGITOS = re.compile(r"\d+")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
RE_CEP = re.compile(r"^\d{5}-\d{3}$")
RE_DATA = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _mesmo(cpf):
    """Todos os dígitos iguais são casos especiais que passam na conta mas não são CPFs reais."""
    d = re.sub(r"\D", "", cpf)
    return len(set(d)) <= 1


def _cpf_valido(cpf):
    d = re.sub(r"\D", "", cpf)
    if _mesmo(d):
        return False
    base = d[:9]

    def digito(parcial, peso):
        soma = sum(int(a) * peso for a, peso in zip(parcial, range(peso, 1, -1)))
        return (soma * 10) % 11 % 10

    dv1 = digito(base, 10)
    dv2 = digito(base + str(dv1), 11)
    return d[9:] == str(dv1) + str(dv2)


def _data_valida(data):
    m = RE_DATA.match(data)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mes <= 12:
        return False
    dias = [31, 29 if _bissexto(ano) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dia <= dias[mes - 1]


def _bissexto(ano):
    return ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)


def valida(dados):
    erros = []
    aba = dados.get("aba", "alunos")
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += CAMPOS_OBRIGATORIOS_ALUNOS
    if any(not dados.get(c, "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    if dados.get("nusp") and not RE_DIGITOS.fullmatch(dados["nusp"]):
        erros.append("N. USP deve conter apenas números")

    if dados.get("agencia") and not RE_DIGITOS.fullmatch(dados["agencia"]):
        erros.append("Número da agência deve conter apenas números")

    valor_limpo = dados.get("valor", "").replace("R$", "").replace(".", "").replace(",", ".").strip()
    if valor_limpo:
        try:
            valor = float(valor_limpo)
            if valor <= 0 or valor != int(valor):
                erros.append("Valor solicitado deve ser maior que 0")
        except ValueError:
            erros.append("Valor solicitado deve ser maior que 0")

    if dados.get("email") and not RE_EMAIL.match(dados["email"]):
        erros.append("E-mail inválido")

    cpf = dados.get("cpf", "").strip()
    if cpf:
        if not RE_CPF.match(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not _cpf_valido(cpf):
            erros.append("CPF inválido")

    if dados.get("cep") and not RE_CEP.match(dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")

    data = dados.get("nascimento", "").strip()
    if data:
        if not RE_DATA.match(data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not _data_valida(data):
            erros.append("Data de nascimento inválida")

    return erros


def _valor_formatado(bruto):
    digitos = re.sub(r"\D", "", bruto)
    if not digitos:
        return "R$ 0,00"
    cents = int(digitos) if _eh_centavos(bruto) else int(round(float(bruto.replace("R$", "").replace(".", "").replace(",", ".")) * 100))
    inteiro, fracao = divmod(cents, 100)
    s = f"{inteiro:,}".replace(",", ".")
    return f"R$ {s},{fracao:02d}"


def _eh_centavos(bruto):
    return "R$" not in bruto and "," not in bruto and "." not in bruto


def gera_oficio(dados):
    def g(chave):
        return dados.get(chave, "").strip()

    linhas = []
    linhas.append(f"Interessada(o): {g('nome')} - {g('nusp')}")
    linhas.append(f"E-mail: {g('email')}")
    if g("aba") == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {g('programa')}")
    else:
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {g('tipo_auxilio')}")
        linhas.append(f"Programa: {g('programa')} - {g('nivel')}")
    linhas.append("")
    linhas.append("A CCP-" + g("programa") + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {g('nome_evento')}")
    linhas.append(f"Período: {g('periodo')}")
    linhas.append(f"Local: {g('cidade_evento')} - {g('estado_evento')} - {g('pais_evento')}")
    if g("link_evento"):
        linhas.append(f"Link do evento: {g('link_evento')}")
    linhas.append(f"Apresentação de trabalho: {g('apresentacao')}")
    linhas.append(f"Valor solicitado: {_valor_formatado(g('valor'))}")
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


@app.post("/solicitacao")
async def solicitacao(request):
    form = await request.form()
    dados = {chave: valores[0] if valores else "" for chave, valores in form.to_dict(flat=False).items()}
    erros = valida(dados)
    if erros:
        return JSONResponse({"erro": True, "erros": erros})
    return {"erro": False, "oficio": gera_oficio(dados)}


RAIZ = Path(__file__).resolve().parent
app.mount("/", StaticFiles(directory=str(RAIZ), html=True), name="static")
