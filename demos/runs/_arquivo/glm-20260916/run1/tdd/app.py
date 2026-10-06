import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).resolve().parent


class Solicitacao(BaseModel):
    tipo: str = ""
    nome_completo: str = ""
    n_usp: str = ""
    programa: str = ""
    nivel: str = ""
    tipo_auxilio: str = ""
    email: str = ""
    nome_evento: str = ""
    periodo_evento: str = ""
    cidade_evento: str = ""
    estado_evento: str = ""
    pais_evento: str = ""
    link_evento: str = ""
    valor_solicitado: str = ""
    detalhamento: str = ""
    apresentacao_trabalho: str = ""
    data_nascimento: str = ""
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cep: str = ""
    cidade: str = ""
    estado: str = ""
    cpf: str = ""
    rg_rnm: str = ""
    nome_banco: str = ""
    agencia: str = ""
    conta: str = ""


_OBRIGATORIOS = (
    "nome_completo", "n_usp", "programa", "email", "nome_evento",
    "periodo_evento", "cidade_evento", "estado_evento", "pais_evento",
    "valor_solicitado", "detalhamento", "apresentacao_trabalho",
    "data_nascimento", "logradouro", "numero", "bairro", "cep",
    "cidade", "estado", "cpf", "rg_rnm", "nome_banco", "agencia", "conta",
)


def _so_digitos(texto: str) -> bool:
    return re.fullmatch(r"[0-9]+", texto) is not None


def _email_valido(email: str) -> bool:
    return re.fullmatch(r"[^@\s]+@[^@\s]+", email) is not None


def _cpf_valido(cpf: str) -> bool:
    numeros = [int(caractere) for caractere in re.sub(r"[^0-9]", "", cpf)]
    if len(numeros) != 11:
        return False
    digito1 = sum(numeros[i] * (10 - i) for i in range(9)) * 10 % 11 % 10
    digito2 = sum(numeros[i] * (11 - i) for i in range(10)) * 10 % 11 % 10
    return numeros[9] == digito1 and numeros[10] == digito2


def _data_existe(data: str) -> bool:
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False
    return True


def _validar(dados: dict) -> list:
    obrigatorios = list(_OBRIGATORIOS)
    if dados["tipo"] == "alunos":
        obrigatorios += ["nivel", "tipo_auxilio"]
    if any(not (dados[campo] or "").strip() for campo in obrigatorios):
        return ["Preencha todos os campos"]

    erros = []
    if not _so_digitos(dados["n_usp"]):
        erros.append("N. USP deve conter apenas números")
    if not _so_digitos(dados["agencia"]):
        erros.append("Número da agência deve conter apenas números")
    if not _so_digitos(dados["valor_solicitado"]) or int(dados["valor_solicitado"]) <= 0:
        erros.append("Valor solicitado deve ser maior que 0")
    if not _email_valido(dados["email"]):
        erros.append("E-mail inválido")
    if not re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", dados["cpf"]):
        erros.append("CPF deve estar no formato 000.000.000-00")
    elif not _cpf_valido(dados["cpf"]):
        erros.append("CPF inválido")
    if not re.fullmatch(r"[0-9]{5}-[0-9]{3}", dados["cep"]):
        erros.append("CEP deve estar no formato 00000-000")
    if not re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", dados["data_nascimento"]):
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")
    elif not _data_existe(dados["data_nascimento"]):
        erros.append("Data de nascimento inválida")
    return erros


def _moeda(digitos: str) -> str:
    centavos = int(digitos)
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def _redigir_oficio(dados: dict) -> str:
    docente = dados["tipo"] == "docentes"
    assunto = "Verba do programa" if docente else dados["tipo_auxilio"]
    programa = f"Programa: {dados['programa']}"
    if not docente:
        programa += f" - {dados['nivel']}"
    linhas = [
        f"Interessada(o): {dados['nome_completo']} - {dados['n_usp']}",
        f"E-mail: {dados['email']}",
        f"Assunto: Solicitação de Auxílio Financeiro - {assunto}",
        programa,
        "",
        "A CCP-" + dados["programa"] + " aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {dados['nome_evento']}",
        f"Período: {dados['periodo_evento']}",
        f"Local: {dados['cidade_evento']} - {dados['estado_evento']} - {dados['pais_evento']}",
    ]
    if dados["link_evento"]:
        linhas.append(f"Link do evento: {dados['link_evento']}")
    linhas += [
        f"Apresentação de trabalho: {dados['apresentacao_trabalho']}",
        f"Valor solicitado: {_moeda(dados['valor_solicitado'])}",
        f"Detalhamento: {dados['detalhamento']}",
        "",
        "Endereço da(o) interessada(o)",
        f"{dados['logradouro']}, {dados['numero']}",
    ]
    if dados["complemento"]:
        linhas.append(f"Complemento: {dados['complemento']}")
    linhas += [
        f"CEP: {dados['cep']}",
        f"{dados['bairro']}, {dados['cidade']} - {dados['estado']}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {dados['data_nascimento']}",
        f"CPF: {dados['cpf']}",
        f"RG / RNM: {dados['rg_rnm']}",
        f"Banco: {dados['nome_banco']}",
        f"Agência: {dados['agencia']}",
        f"Conta: {dados['conta']}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


app = FastAPI(title="Solicitação de Auxílio Financeiro - Pós-Graduação IME-USP")
app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")


@app.get("/")
def _pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def _folha_de_estilo():
    return FileResponse(RAIZ / "style.css")


@app.get("/app.js")
def _script():
    return FileResponse(RAIZ / "app.js")


@app.post("/solicitacao")
def _solicitar(solicitacao: Solicitacao):
    dados = solicitacao.model_dump()
    erros = _validar(dados)
    if erros:
        return JSONResponse(status_code=400, content={"erros": erros})
    return {"oficio": _redigir_oficio(dados)}
