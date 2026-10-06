import calendar
import re
from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=BASE / "assets"), name="assets")

CAMPOS_OBRIGATORIOS = (
    "nome", "nusp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
    "apresentacao", "nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta",
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CPF_RE = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
CEP_RE = re.compile(r"^\d{5}-\d{3}$")
DATA_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def centavos_de(texto):
    digitos = re.sub(r"\D", "", texto or "")
    return int(digitos) if digitos else 0


def formatar_moeda(centavos):
    reais = f"{centavos / 100:,.2f}"
    return "R$ " + reais.replace(",", "X").replace(".", ",").replace("X", ".")


def cpf_valido(cpf):
    numeros = [int(c) for c in cpf if c.isdigit()]
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False
    for i in (9, 10):
        soma = sum(numeros[j] * ((i + 1) - j) for j in range(i))
        digito = (soma * 10) % 11
        digito = 0 if digito == 10 else digito
        if digito != numeros[i]:
            return False
    return True


def data_valida(texto):
    dia, mes, ano = (int(grupo) for grupo in DATA_RE.match(texto).groups())
    if dia < 1 or mes < 1 or mes > 12:
        return False
    return dia <= calendar.monthrange(ano, mes)[1]


def validar(dados, aba):
    valores = {chave: (dados.get(chave) or "").strip() for chave in dados}
    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]

    erros = []
    if any(not valores.get(chave) for chave in obrigatorios):
        erros.append("Preencha todos os campos")

    nusp = valores.get("nusp", "")
    if nusp and not nusp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = valores.get("agencia", "")
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    centavos = 0
    valor = valores.get("valor", "")
    if valor:
        centavos = centavos_de(valor)
        if centavos <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = valores.get("email", "")
    if email and not EMAIL_RE.match(email):
        erros.append("E-mail inválido")

    cpf = valores.get("cpf", "")
    if cpf:
        if not CPF_RE.match(cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not cpf_valido(cpf):
            erros.append("CPF inválido")

    cep = valores.get("cep", "")
    if cep and not CEP_RE.match(cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = valores.get("nascimento", "")
    if nascimento:
        if not DATA_RE.match(nascimento):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not data_valida(nascimento):
            erros.append("Data de nascimento inválida")

    return erros, valores, centavos


def gerar_oficio(d, aba, valor_formatado):
    linhas = [
        f"Interessada(o): {d.get('nome', '')} - {d.get('nusp', '')}",
        f"E-mail: {d.get('email', '')}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {d.get('tipo_auxilio', '')}")
        linhas.append(f"Programa: {d.get('programa', '')} - {d.get('nivel', '')}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {d.get('programa', '')}")

    linhas += [
        "",
        f"A CCP-{d.get('programa', '')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {d.get('evento', '')}",
        f"Período: {d.get('periodo', '')}",
        f"Local: {d.get('cidade_evento', '')} - {d.get('estado_evento', '')} - {d.get('pais_evento', '')}",
    ]
    if d.get("link"):
        linhas.append(f"Link do evento: {d['link']}")
    linhas += [
        f"Apresentação de trabalho: {d.get('apresentacao', '')}",
        f"Valor solicitado: {valor_formatado}",
        f"Detalhamento: {d.get('detalhamento', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{d.get('logradouro', '')}, {d.get('numero', '')}",
    ]
    if d.get("complemento"):
        linhas.append(f"Complemento: {d['complemento']}")
    linhas += [
        f"CEP: {d.get('cep', '')}",
        f"{d.get('bairro', '')}, {d.get('cidade', '')} - {d.get('estado', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {d.get('nascimento', '')}",
        f"CPF: {d.get('cpf', '')}",
        f"RG / RNM: {d.get('rg', '')}",
        f"Banco: {d.get('banco', '')}",
        f"Agência: {d.get('agencia', '')}",
        f"Conta: {d.get('conta', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(BASE / "style.css", media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(BASE / "app.js", media_type="application/javascript")


@app.post("/solicitar")
def solicitar(dados: dict = Body(...)):
    aba = dados.get("aba", "alunos")
    erros, valores, centavos = validar(dados, aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(valores, aba, formatar_moeda(centavos))}
