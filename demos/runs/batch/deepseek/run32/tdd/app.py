import os
import re
from datetime import date

from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")

app.mount("/assets", StaticFiles(directory=os.path.join(BASE, "assets")), name="assets")

NOMES = {
    "nome_completo": ("nome_completo", "nomeCompleto"),
    "n_usp": ("n_usp", "nusp", "numero_usp"),
    "programa": ("programa",),
    "nivel": ("nivel",),
    "tipo_auxilio": ("tipo_auxilio",),
    "email": ("email",),
    "nome_evento": ("nome_evento",),
    "periodo_evento": ("periodo_evento",),
    "cidade_evento": ("cidade_evento",),
    "estado_evento": ("estado_evento",),
    "pais_evento": ("pais_evento",),
    "link_evento": ("link_evento",),
    "valor_solicitado": ("valor_solicitado",),
    "detalhamento": ("detalhamento",),
    "apresentacao": ("apresentacao",),
    "data_nascimento": ("data_nascimento",),
    "logradouro": ("logradouro",),
    "numero": ("numero",),
    "complemento": ("complemento",),
    "bairro": ("bairro",),
    "cep": ("cep",),
    "cidade": ("cidade",),
    "estado": ("estado",),
    "cpf": ("cpf",),
    "rg": ("rg",),
    "banco": ("banco",),
    "agencia": ("agencia",),
    "conta": ("conta",),
}

OBRIGATORIOS = (
    "nome_completo",
    "n_usp",
    "programa",
    "nivel",
    "tipo_auxilio",
    "email",
    "nome_evento",
    "periodo_evento",
    "cidade_evento",
    "estado_evento",
    "pais_evento",
    "valor_solicitado",
    "detalhamento",
    "apresentacao",
    "data_nascimento",
    "logradouro",
    "numero",
    "bairro",
    "cep",
    "cidade",
    "estado",
    "cpf",
    "rg",
    "banco",
    "agencia",
    "conta",
)

SO_NA_ABA_DE_ALUNOS = ("nivel", "tipo_auxilio")

FORMATO_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
FORMATO_CEP = re.compile(r"\d{5}-\d{3}")
FORMATO_DATA = re.compile(r"\d{2}/\d{2}/\d{4}")
FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _ler(nome):
    with open(os.path.join(BASE, nome), encoding="utf-8") as arquivo:
        return arquivo.read()


def _campo(dados, *nomes):
    for nome in nomes:
        valor = dados.get(nome)
        if valor is not None:
            return str(valor).strip()
    return ""


def _em_reais(texto):
    digitos = re.sub(r"\D", "", texto)
    centavos = int(digitos) if digitos else 0
    inteiros = f"{centavos // 100:,}".replace(",", ".")
    return f"R$ {inteiros},{centavos % 100:02d}"


def _cpf_valido(cpf):
    digitos = re.sub(r"\D", "", cpf)
    for posicao in (9, 10):
        soma = sum(int(digitos[i]) * (posicao + 1 - i) for i in range(posicao))
        if (soma * 10) % 11 % 10 != int(digitos[posicao]):
            return False
    return True


def _data_existente(texto):
    dia, mes, ano = (int(parte) for parte in texto.split("/"))
    try:
        date(ano, mes, dia)
    except ValueError:
        return False
    return True


def _erros(valores, aba):
    obrigatorios = [
        campo
        for campo in OBRIGATORIOS
        if aba == "alunos" or campo not in SO_NA_ABA_DE_ALUNOS
    ]
    erros = []
    if any(not valores[campo] for campo in obrigatorios):
        erros.append("Preencha todos os campos")
    if valores["n_usp"] and not valores["n_usp"].isdigit():
        erros.append("N. USP deve conter apenas números")
    if valores["agencia"] and not valores["agencia"].isdigit():
        erros.append("Número da agência deve conter apenas números")
    digitos_do_valor = re.sub(r"\D", "", valores["valor_solicitado"])
    if valores["valor_solicitado"] and (not digitos_do_valor or int(digitos_do_valor) == 0):
        erros.append("Valor solicitado deve ser maior que 0")
    if valores["email"] and not FORMATO_EMAIL.fullmatch(valores["email"]):
        erros.append("E-mail inválido")
    cpf = valores["cpf"]
    cpf_no_formato = bool(cpf) and bool(FORMATO_CPF.fullmatch(cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")
    if valores["cep"] and not FORMATO_CEP.fullmatch(valores["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    nascimento = valores["data_nascimento"]
    nascimento_no_formato = bool(nascimento) and bool(FORMATO_DATA.fullmatch(nascimento))
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    if cpf_no_formato and not _cpf_valido(cpf):
        erros.append("CPF inválido")
    if nascimento_no_formato and not _data_existente(nascimento):
        erros.append("Data de nascimento inválida")
    return erros


def _oficio(valores, aba):
    linhas = [
        f"Interessada(o): {valores['nome_completo']} - {valores['n_usp']}",
        f"E-mail: {valores['email']}",
    ]
    if aba == "docentes":
        linhas.append("Assunto: Solicitação de Auxílio Financeiro - Verba do programa")
        linhas.append(f"Programa: {valores['programa']}")
    else:
        linhas.append(
            f"Assunto: Solicitação de Auxílio Financeiro - {valores['tipo_auxilio']}"
        )
        linhas.append(f"Programa: {valores['programa']} - {valores['nivel']}")
    linhas.extend(
        [
            "",
            f"A CCP-{valores['programa']} aprovou na data de hoje, a solicitação de auxílio financeiro",
            "para a interessada(o) acima, conforme segue:",
            "",
            "Dados do evento",
            f"Evento: {valores['nome_evento']}",
            f"Período: {valores['periodo_evento']}",
            f"Local: {valores['cidade_evento']} - {valores['estado_evento']} - {valores['pais_evento']}",
        ]
    )
    if valores["link_evento"]:
        linhas.append(f"Link do evento: {valores['link_evento']}")
    linhas.extend(
        [
            f"Apresentação de trabalho: {valores['apresentacao']}",
            f"Valor solicitado: {_em_reais(valores['valor_solicitado'])}",
            f"Detalhamento: {valores['detalhamento']}",
            "",
            "Endereço da(o) interessada(o)",
            f"{valores['logradouro']}, {valores['numero']}",
        ]
    )
    if valores["complemento"]:
        linhas.append(f"Complemento: {valores['complemento']}")
    linhas.extend(
        [
            f"CEP: {valores['cep']}",
            f"{valores['bairro']}, {valores['cidade']} - {valores['estado']}",
            "",
            "Dados para pagamento",
            f"Data de nascimento: {valores['data_nascimento']}",
            f"CPF: {valores['cpf']}",
            f"RG / RNM: {valores['rg']}",
            f"Banco: {valores['banco']}",
            f"Agência: {valores['agencia']}",
            f"Conta: {valores['conta']}",
            "",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ]
    )
    return "\n".join(linhas)


@app.get("/")
def pagina_inicial():
    return HTMLResponse(_ler("index.html"))


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(os.path.join(BASE, "style.css"), media_type="text/css")


@app.get("/app.js")
def script():
    return FileResponse(os.path.join(BASE, "app.js"), media_type="text/javascript")


@app.post("/solicitacao")
def solicitar(payload: dict = Body(...)):
    aba = "docentes" if _campo(payload, "aba").lower() == "docentes" else "alunos"
    valores = {campo: _campo(payload, *nomes) for campo, nomes in NOMES.items()}
    erros = _erros(valores, aba)
    if erros:
        return {"erros": erros}
    return {"oficio": _oficio(valores, aba)}
