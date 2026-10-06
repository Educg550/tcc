import datetime
import re
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Helpers de validação/formatação


def valida_cpf(cpf: str) -> bool:
    """Valida os dígitos verificadores do CPF."""
    if not re.fullmatch(r"\d{11}", cpf):
        return False
    if cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dv1 = (soma * 10 % 11) % 10
    if int(cpf[9]) != dv1:
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dv2 = (soma * 10 % 11) % 10
    if int(cpf[10]) != dv2:
        return False
    return True


def valida_data(data: str) -> bool:
    """Valida uma data no formato dd/mm/aaaa (data existente)."""
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", data)
    if not m:
        return False
    try:
        d = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return False
    return True


def formata_moeda(centavos_str: str) -> str:
    """Formata dígitos como centavos em moeda brasileira."""
    centavos = centavos_str or "0"
    valor = int(centavos) / 100
    inteiro = int(valor)
    frac = int(round((valor - inteiro) * 100))
    s = f"{inteiro:,}".replace(",", ".")
    return f"R$ {s},{frac:02d}"


class Solicitacao(BaseModel):
    tipo: str  # "alunos" ou "docentes"
    dados: dict


def valida_dados(tipo: str, dados: dict) -> list:
    """Valida os dados e retorna a lista de mensagens de erro."""
    erros = []

    # Converte todos os valores para string
    def valor(campo: str) -> str:
        return str(dados.get(campo, "") or "").strip()

    # Campos obrigatórios
    campos_obrigatorios = [
        "nome", "nusp", "programa", "email",
        "evento", "periodo", "cidade_evento", "estado_evento", "pais_evento",
        "valor", "detalhamento", "apresentacao",
        "data_nascimento", "logradouro", "numero", "bairro", "cep",
        "cidade", "estado",
        "cpf", "rg", "banco", "agencia", "conta",
    ]
    if tipo == "alunos":
        campos_obrigatorios += ["nivel", "tipo_auxilio"]

    if any(not valor(c) for c in campos_obrigatorios):
        erros.append("Preencha todos os campos")

    # Validações específicas
    if valor("nusp") and not re.fullmatch(r"\d+", valor("nusp")):
        erros.append("N. USP deve conter apenas números")

    if valor("agencia") and not re.fullmatch(r"\d+", valor("agencia")):
        erros.append("Número da agência deve conter apenas números")

    if valor("valor"):
        valor_str = valor("valor")
        m = re.fullmatch(r"R\$ ([\d.]+),(\d{2})", valor_str)
        if m:
            centavos = int(m.group(1).replace(".", "") + m.group(2))
            if centavos <= 0:
                erros.append("Valor solicitado deve ser maior que 0")
        elif re.fullmatch(r"\d+", valor_str):
            if int(valor_str) <= 0:
                erros.append("Valor solicitado deve ser maior que 0")
        else:
            erros.append("Valor solicitado deve ser maior que 0")

    if valor("email"):
        email = valor("email")
        if "@" not in email or "@" in email.split("@")[-1] or "." not in email.split("@")[-1]:
            erros.append("E-mail inválido")

    if valor("cpf"):
        cpf = valor("cpf")
        if not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf):
            erros.append("CPF deve estar no formato 000.000.000-00")
        elif not valida_cpf(re.sub(r"\D", "", cpf)):
            erros.append("CPF inválido")

    if valor("cep") and not re.fullmatch(r"\d{5}-\d{3}", valor("cep")):
        erros.append("CEP deve estar no formato 00000-000")

    if valor("data_nascimento"):
        data = valor("data_nascimento")
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
            erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
        elif not valida_data(data):
            erros.append("Data de nascimento inválida")

    return erros


def gera_oficio(tipo: str, dados: dict) -> str:
    """Gera o ofício com os dados preenchidos."""
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    nome = str(dados.get("nome", "")).strip()
    nusp = str(dados.get("nusp", "")).strip()
    email = str(dados.get("email", "")).strip()
    programa = str(dados.get("programa", "")).strip()
    nivel = str(dados.get("nivel", "")).strip()
    tipo_auxilio = str(dados.get("tipo_auxilio", "")).strip()
    evento = str(dados.get("evento", "")).strip()
    periodo = str(dados.get("periodo", "")).strip()
    cidade = str(dados.get("cidade_evento", "")).strip()
    estado = str(dados.get("estado_evento", "")).strip()
    pais = str(dados.get("pais_evento", "")).strip()
    link = str(dados.get("link", "")).strip()
    apresentacao = str(dados.get("apresentacao", "")).strip()
    valor = formata_moeda(str(dados.get("valor", "")).replace("R$ ", "").replace(",", "").replace(".", "")) if str(dados.get("valor", "")).strip() else ""
    detalhamento = str(dados.get("detalhamento", "")).strip()
    data_nasc = str(dados.get("data_nascimento", "")).strip()
    logradouro = str(dados.get("logradouro", "")).strip()
    numero = str(dados.get("numero", "")).strip()
    complemento = str(dados.get("complemento", "")).strip()
    bairro = str(dados.get("bairro", "")).strip()
    cep = str(dados.get("cep", "")).strip()
    cidade_end = str(dados.get("cidade", "")).strip()
    estado_end = str(dados.get("estado", "")).strip()
    cpf = str(dados.get("cpf", "")).strip()
    rg = str(dados.get("rg", "")).strip()
    banco = str(dados.get("banco", "")).strip()
    agencia = str(dados.get("agencia", "")).strip()
    conta = str(dados.get("conta", "")).strip()

    if tipo == "alunos":
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {tipo_auxilio}"
        programa_linha = f"Programa: {programa} - {nivel}"
    else:
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa_linha = f"Programa: {programa}"

    linhas = [
        f"Interessada(o): {nome} - {nusp}",
        f"E-mail: {email}",
        assunto,
        programa_linha,
        "",
        f"A CCP-{programa} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {evento}",
        f"Período: {periodo}",
        f"Local: {cidade} - {estado} - {pais}",
    ]
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas.extend([
        f"Apresentação de trabalho: {apresentacao}",
        f"Valor solicitado: {valor}",
        f"Detalhamento: {detalhamento}",
        "",
        "Endereço da(o) interessada(o)",
        f"{logradouro}, {numero}",
    ])
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.extend([
        f"CEP: {cep}",
        f"{bairro}, {cidade_end} - {estado_end}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {data_nasc}",
        f"CPF: {cpf}",
        f"RG / RNM: {rg}",
        f"Banco: {banco}",
        f"Agência: {agencia}",
        f"Conta: {conta}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ])
    return "\n".join(linhas)


@app.post("/api/solicitar")
async def solicitar(s: Solicitacao):
    erros = valida_dados(s.tipo, s.dados)
    if erros:
        return JSONResponse({"ok": False, "erros": erros})
    oficio = gera_oficio(s.tipo, s.dados)
    return JSONResponse({"ok": True, "oficio": oficio})


# Serve os arquivos estáticos (frontend) na raiz
app.mount("/", StaticFiles(directory="static", html=True), name="static")
