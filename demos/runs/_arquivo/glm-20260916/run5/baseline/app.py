import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

RAIZ = Path(__file__).parent

OPCIONAIS = {"LINK DO EVENTO, EXAME OU DEFESA", "COMPLEMENTO"}

ROTULOS_ALUNOS = [
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
    "DATA DE NASCIMENTO",
    "LOGRADOURO",
    "NÚMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CEP",
    "CIDADE",
    "ESTADO",
    "CPF (SEPARADOS POR PONTOS E TRAÇO)",
    "RG / RNM (SEPARADOS POR PONTOS E TRAÇO)",
    "NOME DO BANCO",
    "NÚMERO DA AGÊNCIA",
    "NÚMERO DA CONTA",
]
ROTULOS_DOCENTES = [r for r in ROTULOS_ALUNOS if r not in ("NÍVEL", "TIPO DE AUXÍLIO")]

app = FastAPI(title="Auxílio Financeiro - Pós-Graduação IME-USP")


class Solicitacao(BaseModel):
    papel: str = "alunos"
    campos: dict[str, str] = {}


def dv_cpf(numeros: list[int], peso_inicial: int) -> int:
    soma = sum(n * peso for n, peso in zip(numeros, range(peso_inicial, 1, -1)))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cpf_valido(cpf: str) -> bool:
    digitos = [int(c) for c in cpf if c.isdigit()]
    if len(digitos) != 11:
        return False
    return dv_cpf(digitos[:9], 10) == digitos[9] and dv_cpf(digitos[:10], 11) == digitos[10]


def validar(papel: str, campos: dict[str, str]) -> list[str]:
    rotulos = ROTULOS_DOCENTES if papel == "docentes" else ROTULOS_ALUNOS
    erros: list[str] = []

    if any(not campos.get(rotulo, "").strip() for rotulo in rotulos if rotulo not in OPCIONAIS):
        erros.append("Preencha todos os campos")

    n_usp = campos.get("N. USP", "").strip()
    if n_usp and not n_usp.isdigit():
        erros.append("N. USP deve conter apenas números")

    agencia = campos.get("NÚMERO DA AGÊNCIA", "").strip()
    if agencia and not agencia.isdigit():
        erros.append("Número da agência deve conter apenas números")

    valor = campos.get("VALOR SOLICITADO (R$)", "").strip()
    if valor:
        centavos = re.sub(r"\D", "", valor)
        if not centavos or int(centavos) == 0:
            erros.append("Valor solicitado deve ser maior que 0")

    email = campos.get("E-MAIL", "").strip()
    if email and ("@" not in email or not email.split("@", 1)[1].strip()):
        erros.append("E-mail inválido")

    cpf = campos.get("CPF (SEPARADOS POR PONTOS E TRAÇO)", "").strip()
    cpf_no_formato = bool(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf))
    if cpf and not cpf_no_formato:
        erros.append("CPF deve estar no formato 000.000.000-00")

    cep = campos.get("CEP", "").strip()
    if cep and not re.fullmatch(r"\d{5}-\d{3}", cep):
        erros.append("CEP deve estar no formato 00000-000")

    nascimento = campos.get("DATA DE NASCIMENTO", "").strip()
    data_no_formato = bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", nascimento))
    if nascimento and not data_no_formato:
        erros.append("Data de nascimento deve estar no formato dd/mm/aaaa")

    if cpf and cpf_no_formato and not cpf_valido(cpf):
        erros.append("CPF inválido")

    if nascimento and data_no_formato:
        try:
            datetime.strptime(nascimento, "%d/%m/%Y")
        except ValueError:
            erros.append("Data de nascimento inválida")

    return erros


def formatar_moeda(valor: str) -> str:
    centavos = int(re.sub(r"\D", "", valor) or 0)
    reais, resto = divmod(centavos, 100)
    return f"R$ {reais:,}".replace(",", ".") + f",{resto:02d}"


def gerar_oficio(papel: str, campos: dict[str, str]) -> str:
    c = {chave: valor.strip() for chave, valor in campos.items()}
    if papel == "docentes":
        assunto = "Assunto: Solicitação de Auxílio Financeiro - Verba do programa"
        programa = f"Programa: {c.get('PROGRAMA', '')}"
    else:
        assunto = f"Assunto: Solicitação de Auxílio Financeiro - {c.get('TIPO DE AUXÍLIO', '')}"
        programa = f"Programa: {c.get('PROGRAMA', '')} - {c.get('NÍVEL', '')}"
    linhas = [
        f"Interessada(o): {c.get('NOME COMPLETO - SEM ABREVIAR', '')} - {c.get('N. USP', '')}",
        f"E-mail: {c.get('E-MAIL', '')}",
        assunto,
        programa,
        "",
        f"A CCP-{c.get('PROGRAMA', '')} aprovou na data de hoje, a solicitação de auxílio financeiro para a",
        "interessada(o) acima, conforme segue:",
        "",
        "Dados do evento",
        f"Evento: {c.get('NOME DO EVENTO / BANCA DE EXAME OU DEFESA', '')}",
        f"Período: {c.get('PERÍODO DO EVENTO, EXAME OU DEFESA', '')}",
        f"Local: {c.get('CIDADE DO EVENTO, EXAME OU DEFESA', '')} - {c.get('ESTADO DO EVENTO, EXAME OU DEFESA', '')} - {c.get('PAÍS DO EVENTO, EXAME OU DEFESA', '')}",
    ]
    link = c.get("LINK DO EVENTO, EXAME OU DEFESA", "")
    if link:
        linhas.append(f"Link do evento: {link}")
    linhas += [
        f"Apresentação de trabalho: {c.get('IRÁ APRESENTAR TRABALHO NO EVENTO? QUE TIPO?', '')}",
        f"Valor solicitado: {formatar_moeda(c.get('VALOR SOLICITADO (R$)', ''))}",
        f"Detalhamento: {c.get('DETALHAMENTO DO PEDIDO', '')}",
        "",
        "Endereço da(o) interessada(o)",
        f"{c.get('LOGRADOURO', '')}, {c.get('NÚMERO', '')}",
    ]
    complemento = c.get("COMPLEMENTO", "")
    if complemento:
        linhas.append(f"Complemento: {complemento}")
    linhas += [
        f"CEP: {c.get('CEP', '')}",
        f"{c.get('BAIRRO', '')}, {c.get('CIDADE', '')} - {c.get('ESTADO', '')}",
        "",
        "Dados para pagamento",
        f"Data de nascimento: {c.get('DATA DE NASCIMENTO', '')}",
        f"CPF: {c.get('CPF (SEPARADOS POR PONTOS E TRAÇO)', '')}",
        f"RG / RNM: {c.get('RG / RNM (SEPARADOS POR PONTOS E TRAÇO)', '')}",
        f"Banco: {c.get('NOME DO BANCO', '')}",
        f"Agência: {c.get('NÚMERO DA AGÊNCIA', '')}",
        f"Conta: {c.get('NÚMERO DA CONTA', '')}",
        "",
        "Encaminhe-se ao Serviço Financeiro para providências.",
    ]
    return "\n".join(linhas)


@app.post("/api/solicitacao")
def receber_solicitacao(solicitacao: Solicitacao):
    erros = validar(solicitacao.papel, solicitacao.campos)
    if erros:
        return {"erros": erros}
    return {"oficio": gerar_oficio(solicitacao.papel, solicitacao.campos)}


@app.get("/")
def pagina():
    return FileResponse(RAIZ / "index.html")


@app.get("/style.css")
def folha_de_estilo():
    return FileResponse(RAIZ / "style.css", media_type="text/css")


@app.get("/app.js")
def comportamento():
    return FileResponse(RAIZ / "app.js", media_type="text/javascript")


app.mount("/assets", StaticFiles(directory=RAIZ / "assets"), name="assets")
