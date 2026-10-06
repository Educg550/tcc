from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import re

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")


def _cpf_valido(cpf: str) -> bool:
    if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        return False
    digits = re.sub(r"\D", "", cpf)
    soma = 0
    for i in range(9):
        soma += int(digits[i]) * (10 - i)
    r = (soma * 10) % 11
    if r == 10:
        r = 0
    if r != int(digits[9]):
        return False
    soma = 0
    for i in range(10):
        soma += int(digits[i]) * (11 - i)
    r = (soma * 10) % 11
    if r == 10:
        r = 0
    if r != int(digits[10]):
        return False
    return True


def _data_valida(data: str) -> bool:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return False
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if mo < 1 or mo > 12:
        return False
    dias = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return 1 <= d <= dias[mo - 1]


def _formato_valor(v):
    if isinstance(v, str):
        try:
            v = int(v)
        except ValueError:
            return v
    if not isinstance(v, int):
        return str(v)
    return f"R$ {v // 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@app.get("/")
def index():
    return HTMLResponse((BASE_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/solicitacao")
def solicitacao(dados: dict):
    aba = dados.get("aba", "alunos")
    erros = []

    campos_obrigatorios = [
        "nome", "nusp", "programa", "email", "nome_evento", "periodo",
        "cidade_evento", "estado_evento", "pais_evento", "valor", "detalhamento",
        "apresenta", "nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado", "cpf", "rg", "banco", "agencia", "conta"
    ]
    if aba == "alunos":
        campos_obrigatorios += ["nivel", "tipo_auxilio"]

    for campo in campos_obrigatorios:
        val = dados.get(campo)
        if val is None or (isinstance(val, str) and val.strip() == "") or val == 0:
            erros.append("Preencha todos os campos")
            break
    else:
        pass

    nusp = dados.get("nusp", "")
    if nusp and not re.fullmatch(r"\d+", nusp):
        erros.append("N. USP deve conter apenas números")

    agencia = dados.get("agencia", "")
    if agencia and not re.fullmatch(r"\d+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = dados.get("valor")
    if valor is not None:
        try:
            v = int(valor)
            if v <= 0:
                erros.append("Valor solicitado deve ser maior que 0")
        except (ValueError, TypeError):
            pass

    email = dados.get("email", "")
    if email and "@" not in email:
        erros.append("E-mail inválido")
    elif email and "@" in email:
        parts = email.split("@")
        if len(parts) != 2 or not parts[1] or "." not in parts[1]:
            erros.append("E-mail inválido")

    cpf = dados.get("cpf", "")
    if cpf and not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif cpf and not _cpf_valido(cpf):
        erros.append("CPF inválido")

    cep = dados.get("cep", "")
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = dados.get("nascimento", "")
    if nascimento and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif nascimento and not _data_valida(nascimento):
        erros.append("Data de nascimento inválida")

    if erros:
        return {"erros": erros}

    nome = dados.get("nome", "")
    nusp = dados.get("nusp", "")
    programa = dados.get("programa", "")
    email = dados.get("email", "")
    nome_evento = dados.get("nome_evento", "")
    periodo = dados.get("periodo", "")
    cidade_evento = dados.get("cidade_evento", "")
    estado_evento = dados.get("estado_evento", "")
    pais_evento = dados.get("pais_evento", "")
    link_evento = dados.get("link_evento", "")
    valor = dados.get("valor", 0)
    detalhamento = dados.get("detalhamento", "")
    apresenta = dados.get("apresenta", "")
    nascimento = dados.get("nascimento", "")
    logradouro = dados.get("logradouro", "")
    numero = dados.get("numero", "")
    complemento = dados.get("complemento", "")
    bairro = dados.get("bairro", "")
    cidade = dados.get("cidade", "")
    estado = dados.get("estado", "")
    cpf = dados.get("cpf", "")
    rg = dados.get("rg", "")
    banco = dados.get("banco", "")
    agencia = dados.get("agencia", "")
    conta = dados.get("conta", "")

    nivel = dados.get("nivel", "")
    tipo_auxilio = dados.get("tipo_auxilio", "")

    valor_fmt = _formato_valor(valor)

    linhas = []
    linhas.append(f"Interessada(o): {nome} - {nusp}")
    linhas.append(f"E-mail: {email}")
    if aba == "alunos":
        linhas.append(f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}")
        linhas.append(f"Programa: {programa} - {nivel}")
    else:
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {programa}")
    linhas.append("")
    linhas.append("A CCP-" + programa + " aprovou na data de hoje, a solicitação de auxílio financeiro para a")
    linhas.append("interessada(o) acima, conforme segue:")
    linhas.append("")
    linhas.append("Dados do evento")
    linhas.append(f"Evento: {nome_evento}")
    linhas.append(f"Período: {periodo}")
    linhas.append(f"Local: {cidade_evento} - {estado_evento} - {pais_evento}")
    if link_evento:
        linhas.append(f"Link do evento: {link_evento}")
    linhas.append(f"Apresentação de trabalho: {apresenta}")
    linhas.append(f"Valor solicitado: {valor_fmt}")
    linhas.append(f"Detalhamento: {detalhamento}")
    linhas.append("")
    linhas.append("Endereço da(o) interessada(o)")
    linhas.append(f"{logradouro}, {numero}")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.append(f"CEP: {cep}")
    linhas.append(f"{bairro}, {cidade} - {estado}")
    linhas.append("")
    linhas.append("Dados para pagamento")
    linhas.append(f"Data de nascimento: {nascimento}")
    linhas.append(f"CPF: {cpf}")
    linhas.append(f"RG / RNM: {rg}")
    linhas.append(f"Banco: {banco}")
    linhas.append(f"Agência: {agencia}")
    linhas.append(f"Conta: {conta}")
    linhas.append("")
    linhas.append("Encaminhe-se ao Serviço Financeiro para providências.")

    oficio = "\n".join(linhas)
    return {"oficio": oficio}
