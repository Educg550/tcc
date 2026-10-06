import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI()


class Solicitacao(BaseModel):
    aba: str
    campos: dict[str, str]


CAMPOS_OBRIGATORIOS = [
    "nome", "n_usp", "programa", "email", "evento", "periodo",
    "cidade_evento", "estado_evento", "pais_evento", "valor",
    "detalhamento", "apresentacao", "data_nascimento", "logradouro",
    "numero", "bairro", "cep", "cidade", "estado", "cpf", "rg",
    "banco", "agencia", "conta",
]


def _parse_valor(texto):
    limpo = texto.replace("R$", "").replace(" ", "").strip()
    if not limpo:
        return None
    limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _formatar_valor(texto):
    numero = _parse_valor(texto)
    if numero is None:
        return texto
    centavos = round(numero * 100)
    reais = centavos // 100
    resto = centavos % 100
    inteiro = f"{reais:,}".replace(",", ".")
    return f"R$ {inteiro},{resto:02d}"


def _cpf_valido(cpf):
    digitos = [int(c) for c in re.sub(r"\D", "", cpf)]
    if len(digitos) != 11:
        return False
    for n in (9, 10):
        soma = sum(digitos[i] * (n + 1 - i) for i in range(n))
        resto = soma % 11
        esperado = 0 if resto < 2 else 11 - resto
        if esperado != digitos[n]:
            return False
    return True


def _data_valida(data):
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", data)
    if not m:
        return False
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mes <= 12:
        return False
    bissexto = ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0)
    dias_mes = [31, 29 if bissexto else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= dia <= dias_mes[mes - 1]


def validar(campos, aba):
    erros = []

    obrigatorios = list(CAMPOS_OBRIGATORIOS)
    if aba == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not campos.get(c, "").strip() for c in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = campos.get("n_usp", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("agencia", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("valor", "").strip()
    if valor:
        numero = _parse_valor(valor)
        if numero is None or numero <= 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("email", "").strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        erros.append("E-mail inválido")

    cpf = campos.get("cpf", "").strip()
    cpf_formato_ok = bool(re.match(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", cpf))
    if cpf and not cpf_formato_ok:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = campos.get("cep", "").strip()
    if cep and not re.match(r"^\d{5}-\d{3}$", cep):
        erros.append("CEP deve estar no formato 00000-000")

    data = campos.get("data_nascimento", "").strip()
    data_formato_ok = bool(re.match(r"^\d{2}/\d{2}/\d{4}$", data))
    if data and not data_formato_ok:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_formato_ok and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    if data and data_formato_ok and not _data_valida(data):
        erros.append("Data de nascimento inválida")

    return erros


def gerar_oficio(campos, aba):
    programa = campos["programa"]
    linhas = [
        f"Interessada(o): {campos['nome']} - {campos['n_usp']}",
        f"E-mail: {campos['email']}",
    ]
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {campos['tipo_auxilio']}")
        linhas.append(f"Programa: {programa} - {campos['nivel']}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")

    linhas.append("")
    linhas.append(f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {campos['evento']}")
    linhas.append(f"Período: {campos['periodo']}")
    linhas.append(
        f"Local: {campos['cidade_evento']} - {campos['estado_evento']} - {campos['pais_evento']}"
    )
    if campos.get("link", "").strip():
        linhas.append(f"Link do evento: {campos['link']}")
    linhas.append(f"Apresentação de trabalho: {campos['apresentacao']}")
    linhas.append(f"Valor solicitado: {_formatar_valor(campos['valor'])}")
    linhas.append(f"Detalhamento: {campos['detalhamento']}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{campos['logradouro']}, {campos['numero']}")
    if campos.get("complemento", "").strip():
        linhas.append(f"Complemento: {campos['complemento']}")
    linhas.append(f"CEP: {campos['cep']}")
    linhas.append(f"{campos['bairro']}, {campos['cidade']} - {campos['estado']}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {campos['data_nascimento']}")
    linhas.append(f"CPF: {campos['cpf']}")
    linhas.append(f"RG / RNM: {campos['rg']}")
    linhas.append(f"Banco: {campos['banco']}")
    linhas.append(f"Agência: {campos['agencia']}")
    linhas.append(f"Conta: {campos['conta']}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")
    return "\n".join(linhas)


@app.post("/api/solicitar")
def solicitar(solicitacao: Solicitacao):
    erros = validar(solicitacao.campos, solicitacao.aba)
    if erros:
        return {"ok": False, "erros": erros}
    return {"ok": True, "oficio": gerar_oficio(solicitacao.campos, solicitacao.aba)}


app.mount("/assets", StaticFiles(directory="assets", check_dir=False), name="assets")


@app.get("/")
def raiz():
    return FileResponse("index.html")


@app.get("/style.css")
def estilo():
    return FileResponse("style.css")


@app.get("/app.js")
def script():
    return FileResponse("app.js")
