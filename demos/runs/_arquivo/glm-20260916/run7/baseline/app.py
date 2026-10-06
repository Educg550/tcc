import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

CAMPOS_SOLICITANTE_E_EVENTO = [
    "NOME COMPLETO - SEM ABREVIAR",
    "N. USP",
    "PROGRAMA",
    "NÍVEL",
    "TIPO DE AUXÍLIO",
    "E-MAIL",
    "NOME DO EVENTO / BANCA DE EXAME OU DEFESA",
    "PERÍODO DO EVENTO, EXAME OU DEFESA",
    "CIDADE DO EVENTO, EXAME OU DEFESA",
    "ESTADO DO EVENTO, EXAME OU DEFESA",
    "PAÍS DO EVENTO, EXAME OU DEFESA",
    "LINK DO EVENTO, EXAME OU DEFESA",
    "VALOR SOLICITADO (R$)",
    "DETALHAMENTO DO PEDIDO",
    "IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?",
]
CAMPOS_ENDERECO = [
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
]
CAMPOS_PAGAMENTO = [
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]
CAMPOS_OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}

app = FastAPI()


class Solicitacao(BaseModel):
    perfil: str
    dados: dict[str, str]


def campos_do_perfil(perfil: str) -> list[str]:
    campos = CAMPOS_SOLICITANTE_E_EVENTO + CAMPOS_ENDERECO + CAMPOS_PAGAMENTO
    if perfil == "docentes":
        return [campo for campo in campos if campo not in ("NÍVEL", "TIPO DE AUXÍLIO")]
    return campos


def cpf_verificador_conferem(cpf: str) -> bool:
    digitos = [int(caractere) for caractere in cpf if caractere.isdigit()]
    if len(digitos) != 11:
        return False
    digito1 = (sum(digitos[i] * (10 - i) for i in range(9)) * 10) % 11 % 10
    digito2 = (sum(digitos[i] * (11 - i) for i in range(10)) * 10) % 11 % 10
    return digito1 == digitos[9] and digito2 == digitos[10]


def validar(perfil: str, valores: dict[str, str]) -> list[str]:
    valores = {chave: (valor or "").strip() for chave, valor in valores.items()}
    erros: list[str] = []

    obrigatorios = [campo for campo in campos_do_perfil(perfil) if campo not in CAMPOS_OPCIONAIS]
    if any(not valores.get(campo) for campo in obrigatorios):
        erros.append("Preencha todos os campos")

    n_usp = valores.get("N. USP", "")
    if n_usp and not re.fullmatch(r"[0-9]+", n_usp):
        erros.append("N. USP deve conter apenas números")

    agencia = valores.get("NÚMERO DA AGÊNCIA", "")
    if agencia and not re.fullmatch(r"[0-9]+", agencia):
        erros.append("Número da agência deve conter apenas números")

    valor = valores.get("VALOR SOLICITADO (R$)", "")
    digitos_do_valor = re.sub(r"[^0-9]", "", valor)
    if valor and (not digitos_do_valor or int(digitos_do_valor) == 0):
        erros.append("Valor solicitado deve ser maior que 0")

    email = valores.get("E-MAIL", "")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        erros.append("E-mail inválido")

    cpf = valores.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "")
    cpf_no_formato = bool(re.fullmatch(r"[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}", cpf)) if cpf else True
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = valores.get("CEP", "")
    if cep and not re.fullmatch(r"[0-9]{5}-[0-9]{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = valores.get("DATA DE NASCIMENTO", "")
    nascimento_no_formato = bool(re.fullmatch(r"[0-9]{2}/[0-9]{2}/[0-9]{4}", nascimento)) if nascimento else True
    if nascimento and not nascimento_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_no_formato and not cpf_verificador_conferem(cpf):
        erros.append("CPF inválido")

    if nascimento and nascimento_no_formato:
        dia, mes, ano = (int(parte) for parte in nascimento.split("/"))
        try:
            date(ano, mes, dia)
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def formatar_valor(digitos: str) -> str:
    inteiro = digitos.zfill(3)
    reais = f"{int(inteiro[:-2]):,}".replace(",", ".")
    return f"R$ {reais},{inteiro[-2:]}"


def gerar_oficio(perfil: str, valores: dict[str, str]) -> str:
    if perfil == "docentes":
        assunto = "Solicitação de Auxílio Financeiro - Verba do programa"
        linha_programa = f"Programa: {valores['PROGRAMA']}"
    else:
        assunto = f"Solicitação de Auxílio Financeiro - {valores['TIPO DE AUXÍLIO']}"
        linha_programa = f"Programa: {valores['PROGRAMA']} - {valores['NÍVEL']}"

    linhas = [
        f"Interessada(o): {valores['NOME COMPLETO - SEM ABREVIAR']} - {valores['N. USP']}",
        f"E-mail: {valores['E-MAIL']}",
        f"Assunto: {assunto}",
        linha_programa,
        "",
        f"A CCP-{valores['PROGRAMA']} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {valores['NOME DO EVENTO / BANCA DE EXAME OU DEFESA']}",
        f"Período: {valores['PERÍODO DO EVENTO, EXAME OU DEFESA']}",
        f"Local: {valores['CIDADE DO EVENTO, EXAME OU DEFESA']} - {valores['ESTADO DO EVENTO, EXAME OU DEFESA']} - {valores['PAÍS DO EVENTO, EXAME OU DEFESA']}",
    ]
    link = valores.get("LINK DO EVENTO, EXAME OU DEFESA", "")
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas.extend(
        [
            f"Apresentação de trabalho: {valores['IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?']}",
            f"Valor solicitado: {formatar_valor(valores['VALOR SOLICITADO (R$)'])}",
            f"Detalhamento: {valores['DETALHAMENTO DO PEDIDO']}",
            "",
            "Endereço da(o) interessada(o)",
            f"{valores['LOGRADOURO']}, {valores['NÚMERO']}",
        ]
    )
    complemento = valores.get("COMPLEMENTO", "")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas.extend(
        [
            f"CEP: {valores['CEP']}",
            f"{valores['BAIRRO']}, {valores['CIDADE']} - {valores['ESTADO']}",
            "",
            "Dados para pagamento",
            f"Data de nascimento: {valores['DATA DE NASCIMENTO']}",
            f"CPF: {valores['CPF (SEPARADOS POR PONTOS E TRAÇO)']}",
            f"RG / RNM: {valores['RG / RNM (SEPARADOS POR PONTOS E TRAÇO)']}",
            f"Banco: {valores['NOME DO BANCO']}",
            f"Agência: {valores['NÚMERO DA AGÊNCIA']}",
            f"Conta: {valores['NÚMERO DA CONTA']}",
            "",
            "Encaminhe-se ao Serviço Financeiro para providências.",
        ]
    )
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def registrar_solicitacao(solicitacao: Solicitacao) -> dict:
    valores = {chave: (valor or "").strip() for chave, valor in solicitacao.dados.items()}
    erros = validar(solicitacao.perfil, valores)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(solicitacao.perfil, valores)}


@app.get("/", include_in_schema=False)
def pagina_inicial() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


@app.get("/style.css", include_in_schema=False)
def folha_de_estilo() -> FileResponse:
    return FileResponse(BASE_DIR / "style.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def roteiro() -> FileResponse:
    return FileResponse(BASE_DIR / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")
